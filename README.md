# AutoA2A

## 🚀 Overview

**Convert any agent into an A2A-compatible server**

AutoA2A is a CLI tool that scaffolds the boilerplate required to run AI agents as servers compatible with Google's A2A protocol. It supports various agent frameworks — requiring minimal changes to your code.

We currently support the following agent frameworks:

1. CrewAI
2. LangGraph
3. Llama Index
4. OpenAI Agents SDK
5. Pydantic AI

## 🔧 Installation

Python 3.12+ is required.

Install from source:

```bash
git clone https://github.com/NapthaAI/autoa2a
cd autoa2a
git submodule update --init --recursive
pip install -e .
```

Or using UV:

```bash
git clone https://github.com/NapthaAI/autoa2a
cd autoa2a
git submodule update --init --recursive
uv venv
source .venv/bin/activate
uv sync
```

## 🧩 Quick Start

Create a new A2A server for your project:

Navigate to your project directory with your agent implementation:

```bash
cd your-project-directory
```

Generate the A2A server files via CLI with one of the following flags (crewai, langgraph, llamaindex, openai, pydantic):

```bash
autoa2a init --framework langgraph
```

Follow the TODOs and edit the generated `agent.py` file to configure your agent:

```python
# Replace these imports with your actual agent classes
from agent import MyAgent

# Define the input schema
class TaskInput(BaseModel):
    parameter1: str
    parameter2: str

# Replace the agent in the init method
def __init__(self):
    self.agent_graph = MyAgent()
```

Follow the TODOs and edit the generated `taskmanager.py` file to configure your taskmanager:

```python
# Customize TaskInput mapping to match your Input schema
def _get_user_query(self, task_send_params: TaskSendParams) -> TaskInput:
    # existing code .....

    # TODO: Customize this mapping to match your TaskInput schema
        return TaskInput(query=parts[0].text)
```

Follow the TODOs and edit the generated `run_a2a.py` file to configure your A2A server:

```python
# Modify the agent card and agent skill to reflect your agent details
def main(host, port):
    # existing code .....

    skill = AgentSkill(
            id="a2a_agent", # TODO: Change this to the agent's ID
            name="Generic A2A Agent", # TODO: Change this to the agent's name
            description="Plug your A2A logic into this A2A scaffold", # TODO: Change this to the agent's description
            tags=["a2a", "reasoning", "agent"], # TODO: Change this to the agent's tags
            examples=["Example task for A2A agent"], # TODO: Change this to the agent's examples
        )

    agent_card = AgentCard(
        name="A2A Agent", # TODO: Change this to the agent's name
        description="This agent runs A2A logic via A2A", # TODO: Change this to the agent's description
        url= os.getenv("PROXY_URL", f"http://{host}:{port}/"),
        version="0.1.0",
        defaultInputModes=A2AWrapperAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=A2AWrapperAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

```

Install dependencies and run your A2A server:

```bash
uv run serve_a2a
```

## 📁 Generated Files

When you run `autoa2a init --framework <FRAMEWORK>`, the following files are generated:

### __main__.py

This is the main file that sets up and runs your A2A server. It contains:

- **Server Initialization**: Sets up the A2A server using the `A2AServer` class.
- **Agent Configuration**: Defines the agent's capabilities, skills, and metadata using `AgentCard` and `AgentSkill`.
- **Environment Setup**: Loads environment variables and configures logging.
- **Command-Line Interface**: Uses `click` to handle command-line options for host and port.
- **Error Handling**: Manages errors related to missing API keys and server startup issues.

**You'll need to edit the following things in this file**:
- Update the `agent's ID, name, description, and tags` in the `AgentSkill` definition to match your specific agent.

### agent.py

This file contains the implementation of the agent logic. It typically includes:
- **Agent Wrapper**: A class that wraps the core logic of the agent, providing a standardized interface for interaction.
- **Task Input Schema**: A schema class to handle the input parameters accepted the agent

**You'll need to edit the following things in this file**:
- Update the `MyAgent` import with your agent
- Update `TaskInput` class to match your agent's input schema.

### taskmanager.py

This file manages the lifecycle of tasks sent to the agent. It includes:
- **Task Validation**: Ensures that incoming task requests are valid and compatible with the agent's capabilities.
- **Task Execution**: Handles the execution of tasks, including invoking the agent and processing responses.
- **Streaming Support**: Provides support for streaming task responses, allowing for real-time updates.
- **Push Notifications**: Manages push notification configurations and sends updates as tasks progress.
- **Error Handling**: Captures and logs errors during task processing, ensuring robust operation.

**You'll need to edit the following things in this file**:
- Customize the `_get_user_query` method to map incoming task parameters to your agent's input schema.
- Implement any specific logic required for task processing and response handling.

## 🔍 Examples

### Running the examples

The repository includes examples for each supported framework:

```bash
# Clone the repository
git clone https://github.com/NapthaAI/autoa2a.git
cd autoa2a

# Install autoa2a in development mode
pip install -e .

# Navigate to an example directory
cd examples/crewai/simple_researcher

# Run the server
uv run serve_a2a
```

## 🛠️ Creating New Adapter Template

Want to add support for a new agent framework? Here's how:

1. Create a new adapter file in `autoa2a/templates/agent_specific/<framwork_folder>/agent.py` (or add to an existing framework file):
```python
# autoa2a/templates/agent_specific/<framwork_folder>/agent.py
from typing import Dict, Any, AsyncIterable
from pydantic import BaseModel
from agent import MyAgent
# Add any other imports required

class TaskInput(BaseModel):
    # Add the input schema supported by the framework

class A2AWrapperAgent:
    def __init__(self):
        self.agent = MyAgent()
        # Add any other global variable initializations

    # Update the invoke function to run the agent (DONOT change the name of the function)  
    async def invoke(self, input_data: TaskInput, sessionId: str) -> Dict[str, Any]:
        # Use try/catch to handle exceptions
        try:
            # Append sessionId to the Task Inputs
            inputs = {**input_data.model_dump(), "sessionId": sessionId}
            
            # Store the result of your agent after running it
            # Note: You may need to adjust the method calls (kickoff, run)
            # to match your framework's specific API
            result = self.agent.crew().kickoff(inputs)

            return {
                "is_task_complete": True,
                "require_user_input": False,
                "content": str(result),
                # optionally, include metadata for downstream artifact retrieval
                "metadata": {
                    "artifact_id": str(result),
                    "session_id": sessionId
                }
            }
        # Add proper exception handling to better troubleshoot the issues, if there are any
        except Exception as e:
            return {
                "is_task_complete": False,
                "require_user_input": True,
                "content": f"Error: {str(e)}"
            }
    
    # Create a stream function to handle streammable ouput of your framework
    async def stream(self, input_data: TaskInput, sessionId: str) -> AsyncIterable[Dict[str, Any]]:
        # Use the ivoke function if your framework doesnot support streaming
        result = await self.invoke(input_data, sessionId)
        yield result

    # Create a List of supported Content Types
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]


2. Create an example in examples/your_framework/<your_example>/
```

## ☁️ Deploying with Naptha's MCPaaS
Naptha supports deploying your newly-created A2A server to our MCP servers-as-a-service platform! It's easy to get started.

### Setup
Naptha's MCPaaS platform requires your repository be set up with `uv`. 
This means you need a couple configurations in your `pyproject.toml`. 

First, make sure the `run_a2a.py`, `agent.py` and `taskmanager.py` files generated by Naptha's `autoa2a` is the root of your repository.

Second, make sure your `pyproject.toml` has the following configurations:

```toml
[build-system]
requires = [ "hatchling",]
build-backend = "hatchling.build"

[project.scripts]
serve_a2a = "run_a2a:main"

[tool.hatch.metadata]
allow-direct-references = true

[tool.hatch.build.targets.wheel]
include = [ "./run_a2a.py" ]
exclude = [ "__pycache__", "*.pyc" ]
packages = [ "." ]
```

If your agent is in a subdirectory / package of your repository:

```
pyproject.toml
run_a2a.py
agent.py
taskmanager.py
my_agent/
|---| __init__.py
    | agent.py
```

Make sure that it's imported like this in `agent.py`:
```python
from my_agent.agent
```
Not like below, since this will cause the build to fail:
```python 
from .my_agent.agent
``` 

Once you have configured everything, commit and push your code (but not your environment variables!) to github. Then, you can test it to make sure you set up everything correctly:

```shell
uvx --from git+https://github.com/your-username/your-repo serve_a2a
```

If this results in your A2A server being launched on port 10000 successfully, you're good to go!


### Launching your server
1. go to [labs.naptha.ai](https://labs.naptha.ai)
2. Sign in with your github account
3. Choose "A2A" from the "Server Type" dropdown
4. Pick the repository you edited from your repository list -- we autodiscover your github repos.
5. add your environment variables e.g. `OPENAI_API_KEY`, etc.
6. Click Launch.
7. Copy the URL, and paste it into your A2A client:

## 🔌 Using with A2A Clients

### Google's A2A cli client
1. Clone the Google's A2A repo
```shell
git clone https://github.com/google/A2A
```
2. Navigate to `samples/python`
```shell
cd <path to A2A>/samples/python
```
3. Install the dependencies and run the client
```shell
uv venv # Create a virtual environment
source .venv/bin/activate
uv sync

uv run hosts/cli --agent <url of the A2A Server>
```

### Google's A2A UI client

1. Clone the Google's A2A repo
```shell
git clone https://github.com/google/A2A
```
2. Navigate to `demo/ui`
```shell
cd <path to A2A>/demo/ui
```
3. Install the dependencies and run the client
```shell
uv venv # Create a virtual environment
source .venv/bin/activate
uv sync

uv run main.py
```
4. Navigate to agent tab and add the agent by supplying the A2A server url

**Note**: Add the url without the protocol in the client (eg: labs-api.naptha.ai:8080/a2a/<id> )

5. Navigate to conversations tab and start conversation with the agent