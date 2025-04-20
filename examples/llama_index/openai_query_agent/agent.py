from typing import Dict, Any, AsyncIterable
from pydantic import BaseModel
from llama_index.core.workflow import Context
from llama_index.core.agent.workflow import AgentStream, ToolCall
from query_agent import QueryAgent

class TaskInput(BaseModel):
    query: str

class A2AWrapperAgent:
    def __init__(self):
        self.agent = QueryAgent().get_agent()
        self._ctx_states: Dict[str, Dict[str, Any]] = {}

    async def invoke(self, input_data: TaskInput, sessionId: str) -> Dict[str, Any]:
        try:
            ctx = self._get_context(sessionId)
            handler = self.agent.run(input_data.query, ctx=ctx)
            result = await handler

            # Save context
            self._ctx_states[sessionId] = ctx.to_dict()

            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": str(result)
            }
        except Exception as e:
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Error: {str(e)}"
            }

    async def stream(self, input_data: TaskInput, sessionId: str) -> AsyncIterable[Dict[str, Any]]:
        try:
            ctx = self._get_context(sessionId)
            print(ctx.to_dict())
            handler = self.agent.run(input_data.query, ctx=ctx)

            async for event in handler.stream_events():
                if isinstance(event, AgentStream) and event.response != "":
                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": str(event.response)
                    }
                elif isinstance(event, ToolCall):
                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": f"Calling tool {event.tool_name}"
                    }

            final_response = await handler
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": str(final_response)
            }

            self._ctx_states[sessionId] = handler.ctx.to_dict()

        except Exception as e:
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Streaming error: {str(e)}"
            }

            if sessionId in self._ctx_states:
                del self._ctx_states[sessionId]

    def _get_context(self, sessionId: str) -> Context:
        if sessionId in self._ctx_states:
            return Context.from_dict(self.agent, self._ctx_states[sessionId])
        return Context(self.agent)

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]