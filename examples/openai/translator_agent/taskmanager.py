from typing import AsyncIterable, Union, Dict, Any
from common.types import (
    SendTaskRequest,
    TaskSendParams,
    TaskStatus,
    TaskState,
    SendTaskResponse,
    InternalError,
    JSONRPCResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    Artifact,
    Message,
    TextPart,
    PushNotificationConfig,
    InvalidParamsError,
)
from common.server.task_manager import InMemoryTaskManager
from agent import A2AWrapperAgent, TaskInput
from common.utils.push_notification_auth import PushNotificationSenderAuth
import common.server.utils as utils
import asyncio
import logging
import traceback

logger = logging.getLogger(__name__)

class AgentTaskManager(InMemoryTaskManager):
    def __init__(self, agent: A2AWrapperAgent, notification_sender_auth: PushNotificationSenderAuth):
        super().__init__()
        self.agent = agent
        self.notification_sender_auth = notification_sender_auth

    def _validate_request(self, request: Union[SendTaskRequest, SendTaskStreamingRequest]) -> JSONRPCResponse | None:
        task_send_params = request.params
        if not utils.are_modalities_compatible(
            task_send_params.acceptedOutputModes, A2AWrapperAgent.SUPPORTED_CONTENT_TYPES
        ):
            return utils.new_incompatible_types_error(request.id)

        if task_send_params.pushNotification and not task_send_params.pushNotification.url:
            return JSONRPCResponse(id=request.id, error=InvalidParamsError(message="Push notification URL is missing"))

        return None

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        validation_error = self._validate_request(request)
        if validation_error:
            return SendTaskResponse(id=request.id, error=validation_error.error)

        if request.params.pushNotification:
            if not await self.set_push_notification_info(request.params.id, request.params.pushNotification):
                return SendTaskResponse(id=request.id, error=InvalidParamsError(message="Push notification URL is invalid"))

        await self.upsert_task(request.params)
        task = await self.update_store(request.params.id, TaskStatus(state=TaskState.WORKING), None)
        await self.send_task_notification(task)

        task_input = self._get_user_query(request.params)
        try:
            agent_response = self.agent.invoke(task_input, request.params.sessionId)
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            return SendTaskResponse(id=request.id, error=InternalError(message=str(e)))

        return await self._process_agent_response(request, agent_response)

    async def on_send_task_subscribe(self, request: SendTaskStreamingRequest) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        try:
            error = self._validate_request(request)
            if error:
                return error

            await self.upsert_task(request.params)

            if request.params.pushNotification:
                if not await self.set_push_notification_info(request.params.id, request.params.pushNotification):
                    return JSONRPCResponse(id=request.id, error=InvalidParamsError(message="Push notification URL is invalid"))

            sse_event_queue = await self.setup_sse_consumer(request.params.id, False)
            asyncio.create_task(self._run_streaming_agent(request))
            return self.dequeue_events_for_sse(request.id, request.params.id, sse_event_queue)
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            traceback.print_exc()
            return JSONRPCResponse(id=request.id, error=InternalError(message="An error occurred while streaming the response"))

    async def _run_streaming_agent(self, request: SendTaskStreamingRequest):
        try:
            task_input = self._get_user_query(request.params)
            async for item in self.agent.stream(task_input, request.params.sessionId):
                is_task_complete = item["is_task_complete"]
                require_user_input = item["require_user_input"]
                content = item["content"]
                parts = [{"type": "text", "text": content}]

                task_state = TaskState.WORKING
                artifact = None
                message = None
                end_stream = False

                if require_user_input:
                    task_state = TaskState.INPUT_REQUIRED
                    message = Message(role="agent", parts=parts)
                    end_stream = True
                elif is_task_complete:
                    task_state = TaskState.COMPLETED
                    artifact = Artifact(parts=parts)
                    end_stream = True
                else:
                    message = Message(role="agent", parts=parts)

                task_status = TaskStatus(state=task_state, message=message)
                task = await self.update_store(request.params.id, task_status, [artifact] if artifact else None)
                await self.send_task_notification(task)

                if artifact:
                    await self.enqueue_events_for_sse(request.params.id, TaskArtifactUpdateEvent(id=request.params.id, artifact=artifact))

                await self.enqueue_events_for_sse(request.params.id, TaskStatusUpdateEvent(id=request.params.id, status=task_status, final=end_stream))

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            await self.enqueue_events_for_sse(request.params.id, InternalError(message=str(e)))

    async def send_task_notification(self, task):
        if not await self.has_push_notification_info(task.id):
            return
        push_info = await self.get_push_notification_info(task.id)
        await self.notification_sender_auth.send_push_notification(push_info.url, data=task.model_dump(exclude_none=True))

    async def on_resubscribe_to_task(self, request) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        try:
            sse_event_queue = await self.setup_sse_consumer(request.params.id, True)
            return self.dequeue_events_for_sse(request.id, request.params.id, sse_event_queue)
        except Exception as e:
            logger.error(f"Error while reconnecting to SSE: {e}")
            return JSONRPCResponse(id=request.id, error=InternalError(message=str(e)))

    def _get_user_query(self, task_send_params: TaskSendParams) -> TaskInput:
        parts = task_send_params.message.parts

        if not isinstance(parts[0], TextPart):
            raise ValueError("Only text parts are supported.")
        
        return TaskInput(query=parts[0].text)
    
    async def set_push_notification_info(self, task_id: str, push_notification_config: PushNotificationConfig):
        # Verify the ownership of notification URL by issuing a challenge request.
        is_verified = await self.notification_sender_auth.verify_push_notification_url(push_notification_config.url)
        if not is_verified:
            return False
        
        await super().set_push_notification_info(task_id, push_notification_config)
        return True