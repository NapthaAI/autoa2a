# AutoA2A

**Convert any agent into an A2A-compatible server**

AutoA2A is a CLI tool that scaffolds the boilerplate required to run AI agents as servers compatible with Google's A2A protocol. It supports agent frameworks like LangGraph, LangChain, and more — requiring minimal changes to your code.

Note: This tool is in development process and we currently support only langgraph agents

## 🔧 Requirements

Python 3.12+

## 🚀 Installation

```bash
git pull https://github.com/Satti-Gowtham/autoa2a
cd autoa2a
pip install -e .
```

## Quickstart
Create a new A2A server for your project:

Navigate to your project directory with your agent implementation:

```bash
autoa2a init --framework langgraph
```

## ✨ Running examples

Navigate to examples/langgraph/<agent> folder and run the tool

```bash
autoa2a init --framework langgraph
uv run .
```