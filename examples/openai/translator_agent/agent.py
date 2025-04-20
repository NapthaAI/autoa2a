from openai.types.responses import ResponseTextDeltaEvent
from agents import Runner
from pydantic import BaseModel
from typing import Literal, Dict, Any, AsyncIterable
from translator_agent import TranslatorAgent

class TaskInput(BaseModel):
    query: str

class ResponseFormat(BaseModel):
    status: Literal["input_required", "completed", "error"]
    message: str

class A2AWrapperAgent:
    def __init__(self):
        self.agent = TranslatorAgent().get_orchestrator_agent()

    async def invoke(self, input_data: TaskInput, sessionId: str) -> Dict[str, Any]:
        try:
            result = await Runner.run(self.agent, input_data.query)
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": result.final_output
            }
        except Exception as e:
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"An error occurred: {str(e)}"
            }

    async def stream(self, input_data: TaskInput, sessionId: str) -> AsyncIterable[Dict[str, Any]]:
        try:
            result = Runner.run_streamed(self.agent, input=input_data.query)
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    delta = event.data.delta
                    if delta:  # skip empty chunks
                        yield {
                            "is_task_complete": False,
                            "require_user_input": False,
                            "content": delta
                        }

            # Final wrap-up
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": result.final_output
            }

        except Exception as e:
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Streaming error: {str(e)}"
            }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
