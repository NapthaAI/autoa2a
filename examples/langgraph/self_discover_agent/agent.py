from typing import AsyncIterable, Dict, Any, Literal
from pydantic import BaseModel
from langchain_core.messages import AIMessage
from langgraph.types import StateSnapshot

# Import the user agent class
from self_discover_agent import SelfDiscoverAgent  # Replace with actual agent

class TaskInput(BaseModel):
    task_description: str
    reasoning_modules: str = "\n".join(SelfDiscoverAgent().get_reasoning_modules())

class ResponseFormat(BaseModel):
    status: Literal["input_required", "completed", "error"]
    message: str

class A2AWrapperAgent:
    def __init__(self):
        self.agent_graph = SelfDiscoverAgent().get_agent()  # Replace with actual agent

    def invoke(self, input_data: TaskInput, sessionId: str) -> dict:
        config = {"configurable": {"thread_id": sessionId}}
        self.agent_graph.invoke({**input_data.model_dump()}, config)
        return self.get_agent_response(config)

    async def stream(self, input_data: TaskInput, sessionId: str) -> AsyncIterable[Dict[str, Any]]:
        config = {"configurable": {"thread_id": sessionId}}
        seen_ids = set()

        async for step in self.agent_graph.astream({**input_data.model_dump()}, config):
            if not isinstance(step, StateSnapshot):
                continue

            for msg in step.values.get("messages", []):
                if isinstance(msg, AIMessage) and msg.id not in seen_ids:
                    seen_ids.add(msg.id)
                    yield {
                        "is_task_complete": False,
                        "require_user_input": False,
                        "content": msg.content
                    }

        yield self.get_agent_response(config)

    def get_agent_response(self, config: dict) -> Dict[str, Any]:
        state = self.agent_graph.get_state(config)

        # ResponseFormat: user agent provides it
        structured = state.values.get("structured_response")
        if isinstance(structured, ResponseFormat):
            return {
                "is_task_complete": structured.status == "completed",
                "require_user_input": structured.status == "input_required",
                "content": structured.message,
            }

        # ResponseFormat: last AI message
        messages = state.values.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                wrapped = ResponseFormat(status="completed", message=msg.content)
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": wrapped.message,
                }

        answer = state.values.get("answer", "")
        if answer:
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": answer,
            }

        # Fallback: unable to generate a response
        fallback = ResponseFormat(
            status="input_required",
            message="Unable to generate a response."
        )

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": fallback.message,
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]