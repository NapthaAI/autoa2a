from typing import Dict, Any, AsyncIterable
from pydantic import BaseModel
from crew import SimpleResearcherCrew
import uuid
import asyncio

class TaskInput(BaseModel):
    topic: str

class A2AWrapperAgent:
    def __init__(self):
        self.agent = SimpleResearcherCrew()
        self.job_store = {}

    def start_async_task(self, input_data: TaskInput, sessionId: str) -> str:
        job_id = str(uuid.uuid4())
        inputs = {**input_data.model_dump(), "sessionId": sessionId}
        future = asyncio.create_task(self.agent.crew().kickoff_async(inputs))
        self.job_store[job_id] = {
            "future": future,
            "result": None,
            "status": "processing",
            "session_id": sessionId
        }

        return job_id

    async def check_status(self, job_id: str) -> Dict[str, Any]:
        job = self.job_store.get(job_id)
        if not job:
            return {
                "is_task_complete": False,
                "require_user_input": False,
                "content": f"Job ID {job_id} not found",
                "metadata": {}
            }
        future = job["future"]
        if future.done():
            if job["status"] != "complete":
                try:
                    result = await future
                    job["result"] = result
                    job["status"] = "complete"
                except Exception as e:
                    job["result"] = f"Error: {str(e)}"
                    job["status"] = "error"
            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": str(job["result"]),
                "metadata": {
                    "artifact_id": str(job["result"]),
                    "session_id": job["session_id"]
                }
            }
        else:
            return {
                "is_task_complete": False,
                "require_user_input": False,
                "content": "Processing...",
                "metadata": {
                    "session_id": job["session_id"]
                }
            }
    
    async def invoke(self, input_data: TaskInput, sessionId: str) -> Dict[str, Any]:
        try:
            inputs = {**input_data.model_dump(), "sessionId": sessionId}
            result = self.agent.crew().kickoff(inputs)

            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": str(result),
                "metadata": {
                    "artifact_id": str(result),
                    "session_id": sessionId
                }
            }
        except Exception as e:
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Error: {str(e)}"
            }

    async def stream(self, input_data: TaskInput, sessionId: str) -> AsyncIterable[Dict[str, Any]]:
         # Start the async task
        job_id = self.start_async_task(input_data, sessionId)
        
        while True:
            status = await self.check_status(job_id)
            yield {
                "is_task_complete": status["is_task_complete"],
                "require_user_input": status["require_user_input"],
                "content": status["content"],
                "metadata": status.get("metadata", {})
            }
            if status["is_task_complete"]:
                break
            await asyncio.sleep(1)  # Adjust interval as needed

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]