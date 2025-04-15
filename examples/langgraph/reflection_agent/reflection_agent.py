from dotenv import load_dotenv
from typing import Annotated, Dict, Any
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import asyncio
from langgraph.checkpoint.memory import MemorySaver
load_dotenv()

class State(TypedDict):
    query: str
    messages: Annotated[list, add_messages] = []

class ReflectionAgent:
    def __init__(self, openai_model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=openai_model)

        # Set up generation prompt and chain
        self.generate_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an essay assistant tasked with writing excellent 5-paragraph essays."
                " Generate the best essay possible for the user's request."
                " If the user provides critique, respond with a revised version of your previous attempts.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
        self.generate = self.generate_prompt | self.llm

        # Set up reflection prompt and chain
        self.reflection_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a teacher grading an essay submission. Generate critique and recommendations for the user's submission."
                " Provide detailed recommendations, including requests for length, depth, style, etc.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
        self.reflect = self.reflection_prompt | self.llm

        # Store max_iterations as instance attribute, can be updated by run
        self.max_iterations = 3
        # Initialize graph structure - graph definition remains the same
        self._init_graph()

    def generation_node(self, state: State) -> State:
        messages = state.get("messages", [])
        
        # If messages is empty, create a new message from query
        if not messages:
            query = state["query"]
            # The prompt template will add the system message, we just need the human query
            input_messages = [HumanMessage(content=query)]
        else:
            # The content is already built up in messages
            input_messages = messages
            
        # This invokes the generate_prompt with the system prompt + input_messages
        response = self.generate.invoke({"messages": input_messages})
        
        # Add the new AI message to the existing messages
        updated_messages = messages + [response]
        return {"messages": updated_messages}

    def reflection_node(self, state: State) -> State:
        messages = state["messages"]
        
        # Get the last AI message for reflection (the essay to critique)
        ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
        if not ai_messages:
            # Should never happen but just in case
            return {"messages": messages}
            
        last_essay = ai_messages[-1]
        
        # For the reflection, we need a message with the essay to critique
        reflection_input = [HumanMessage(content=last_essay.content)]
        
        # This invokes the reflection_prompt with the system prompt + reflection_input
        reflection = self.reflect.invoke({"messages": reflection_input})
        
        # Add the reflection as a human message to the existing messages
        updated_messages = messages + [HumanMessage(content=reflection.content)]
        return {"messages": updated_messages}

    def _init_graph(self):
        builder = StateGraph(State)
        builder.add_node("generate", self.generation_node)
        builder.add_node("reflect", self.reflection_node)
        builder.add_edge(START, "generate")

        # Conditional edge function remains synchronous as it only checks state length
        builder.add_conditional_edges("generate", self.should_continue)
        builder.add_edge("reflect", "generate")
        # Compile the graph - graph object can be used sync or async
        self.graph = builder.compile(checkpointer=MemorySaver())

    def should_continue(self, state: State):
        if len(state.get("messages", [])) >= self.max_iterations:
            return END
        return "reflect"


if __name__ == "__main__":
    import time

    start = time.time()
    reflection_agent = ReflectionAgent()

    initial_state = {
        "query": "Write an essay on the topicality of The Little Prince and its message in modern life",
    }

    final_state = asyncio.run(reflection_agent.graph.ainvoke(initial_state))
    print(final_state)
    end = time.time()
    print(f"\nTime taken: {end - start:.2f} seconds")