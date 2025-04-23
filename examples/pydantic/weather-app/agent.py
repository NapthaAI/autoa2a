from typing import Dict, Any, AsyncIterable
from pydantic import BaseModel
from weather_agent import weather_agent

class TaskInput(BaseModel):
    query: str

class A2AWrapperAgent:
    def __init__(self):
        self.agent = weather_agent

    async def invoke(self, input_data: TaskInput, sessionId: str) -> Dict[str, Any]:
        try:
            result = await self.agent.run_sync(input_data.query)

            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": str(result.data)
            }
        except Exception as e:
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Error: {str(e)}"
            }

    async def stream(self, input_data: TaskInput, sessionId: str) -> AsyncIterable[Dict[str, Any]]:
        try:
            async with self.agent.iter(input_data.query) as run:
                async for node in run:
                    content = None

                    # Final result from End node
                    if hasattr(node, "data") and hasattr(node.data, "data"):
                        content = node.data.data

                    # Tool call information
                    elif hasattr(node, "model_response") and hasattr(node.model_response, "parts"):
                        for part in node.model_response.parts:
                            if part.part_kind == "text":
                                content = part.content
                            elif part.part_kind == "tool-call":
                                content = f"Calling tool `{part.tool_name}` with args: {part.args}"

                    # Tool return values (from ModelRequestNode)
                    elif hasattr(node, "request") and hasattr(node.request, "parts"):
                        for part in node.request.parts:
                            if part.part_kind == "tool-return":
                                content = f"Tool `{part.tool_name}` returned: {part.content}"

                    if content:
                        yield {
                            "is_task_complete": False,
                            "require_user_input": False,
                            "content": str(content)
                        }

            # When everything is done, mark as complete
            yield {
                "is_task_complete": True,
                "require_user_input": False,
                "content": str(run.result)
            }

        except Exception as e:
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Streaming error: {str(e)}"
            }


    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]