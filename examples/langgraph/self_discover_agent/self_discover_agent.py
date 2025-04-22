from typing import Optional, Dict, Any
from typing_extensions import TypedDict
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Define the prompts
select_prompt = hub.pull("hwchase17/self-discovery-select")
adapt_prompt = hub.pull("hwchase17/self-discovery-adapt")
structured_prompt = hub.pull("hwchase17/self-discovery-structure")
reasoning_prompt = hub.pull("hwchase17/self-discovery-reasoning")

# Define the state
class SelfDiscoverState(TypedDict):
    reasoning_modules: str
    task_description: str
    selected_modules: Optional[str]
    adapted_modules: Optional[str]
    reasoning_structure: Optional[str]
    answer: Optional[str]

class SelfDiscoverAgent:
    def __init__(self, openai_model: str = "gpt-4o"):
        self.llm = ChatOpenAI(temperature=0, model=openai_model)
        
        # Define the prompts
        self.select_prompt = hub.pull("hwchase17/self-discovery-select")
        self.adapt_prompt = hub.pull("hwchase17/self-discovery-adapt")
        self.structured_prompt = hub.pull("hwchase17/self-discovery-structure")
        self.reasoning_prompt = hub.pull("hwchase17/self-discovery-reasoning")
        
        # Initialize graph
        self._init_graph()

    def select(self, inputs):
        select_chain = self.select_prompt | self.llm | StrOutputParser()
        return {"selected_modules": select_chain.invoke(inputs)}

    def adapt(self, inputs):
        adapt_chain = self.adapt_prompt | self.llm | StrOutputParser()
        return {"adapted_modules": adapt_chain.invoke(inputs)}

    def structure(self, inputs):
        structure_chain = self.structured_prompt | self.llm | StrOutputParser()
        return {"reasoning_structure": structure_chain.invoke(inputs)}

    def reason(self, inputs):
        reasoning_chain = self.reasoning_prompt | self.llm | StrOutputParser()
        return {"answer": reasoning_chain.invoke(inputs)}

    def _init_graph(self):
        graph = StateGraph(SelfDiscoverState)
        graph.add_node("select", self.select)
        graph.add_node("adapt", self.adapt)
        graph.add_node("structure", self.structure)
        graph.add_node("reason", self.reason)
        graph.add_edge(START, "select")
        graph.add_edge("select", "adapt")
        graph.add_edge("adapt", "structure")
        graph.add_edge("structure", "reason")
        graph.add_edge("reason", END)
        self.graph = graph.compile(checkpointer=MemorySaver())

    def get_agent(self):
        return self.graph
    
    def get_reasoning_modules(self):
        # Example reasoning modules
        reasoning_modules = [
            "1. How could I devise an experiment to help solve that problem?",
            "2. Make a list of ideas for solving this problem, and apply them one by one to the problem to see if any progress can be made.",
            "4. How can I simplify the problem so that it is easier to solve?",
            "5. What are the key assumptions underlying this problem?",
            "6. What are the potential risks and drawbacks of each solution?",
            "7. What are the alternative perspectives or viewpoints on this problem?",
            "8. What are the long-term implications of this problem and its solutions?",
            "9. How can I break down this problem into smaller, more manageable parts?",
            "10. Critical Thinking: This style involves analyzing the problem from different perspectives, questioning assumptions, and evaluating the evidence or information available. It focuses on logical reasoning, evidence-based decision-making, and identifying potential biases or flaws in thinking.",
            "11. Try creative thinking, generate innovative and out-of-the-box ideas to solve the problem. Explore unconventional solutions, thinking beyond traditional boundaries, and encouraging imagination and originality.",
            "13. Use systems thinking: Consider the problem as part of a larger system and understanding the interconnectedness of various elements. Focuses on identifying the underlying causes, feedback loops, and interdependencies that influence the problem, and developing holistic solutions that address the system as a whole.",
            "14. Use Risk Analysis: Evaluate potential risks, uncertainties, and tradeoffs associated with different solutions or approaches to a problem. Emphasize assessing the potential consequences and likelihood of success or failure, and making informed decisions based on a balanced analysis of risks and benefits.",
            "16. What is the core issue or problem that needs to be addressed?",
            "17. What are the underlying causes or factors contributing to the problem?",
            "18. Are there any potential solutions or strategies that have been tried before? If yes, what were the outcomes and lessons learned?",
            "19. What are the potential obstacles or challenges that might arise in solving this problem?",
            "20. Are there any relevant data or information that can provide insights into the problem? If yes, what data sources are available, and how can they be analyzed?",
            "21. Are there any stakeholders or individuals who are directly affected by the problem? What are their perspectives and needs?",
            "22. What resources (financial, human, technological, etc.) are needed to tackle the problem effectively?",
            "23. How can progress or success in solving the problem be measured or evaluated?",
            "24. What indicators or metrics can be used?",
            "25. Is the problem a technical or practical one that requires a specific expertise or skill set? Or is it more of a conceptual or theoretical problem?",
            "26. Does the problem involve a physical constraint, such as limited resources, infrastructure, or space?",
            "27. Is the problem related to human behavior, such as a social, cultural, or psychological issue?",
            "28. Does the problem involve decision-making or planning, where choices need to be made under uncertainty or with competing objectives?",
            "29. Is the problem an analytical one that requires data analysis, modeling, or optimization techniques?",
            "30. Is the problem a design challenge that requires creative solutions and innovation?",
            "31. Does the problem require addressing systemic or structural issues rather than just individual instances?",
            "32. Is the problem time-sensitive or urgent, requiring immediate attention and action?",
            "33. What kinds of solution typically are produced for this kind of problem specification?",
            "34. Given the problem specification and the current best solution, have a guess about other possible solutions.",
            "35. Let's imagine the current best solution is totally wrong, what other ways are there to think about the problem specification?",
            "36. What is the best way to modify this current best solution, given what you know about these kinds of problem specification?",
            "37. Ignoring the current best solution, create an entirely new solution to the problem.",
            "39. Let's make a step by step plan and implement it with good notation and explanation.",
        ]
        
        return reasoning_modules

# Example usage
if __name__ == "__main__":
    async def main():
        # Example reasoning modules
        reasoning_modules = [
            "1. How could I devise an experiment to help solve that problem?",
            "2. Make a list of ideas for solving this problem, and apply them one by one to the problem to see if any progress can be made.",
            "4. How can I simplify the problem so that it is easier to solve?",
            "5. What are the key assumptions underlying this problem?",
            "6. What are the potential risks and drawbacks of each solution?",
            "7. What are the alternative perspectives or viewpoints on this problem?",
            "8. What are the long-term implications of this problem and its solutions?",
            "9. How can I break down this problem into smaller, more manageable parts?",
            "10. Critical Thinking: This style involves analyzing the problem from different perspectives, questioning assumptions, and evaluating the evidence or information available. It focuses on logical reasoning, evidence-based decision-making, and identifying potential biases or flaws in thinking.",
            "11. Try creative thinking, generate innovative and out-of-the-box ideas to solve the problem. Explore unconventional solutions, thinking beyond traditional boundaries, and encouraging imagination and originality.",
            "13. Use systems thinking: Consider the problem as part of a larger system and understanding the interconnectedness of various elements. Focuses on identifying the underlying causes, feedback loops, and interdependencies that influence the problem, and developing holistic solutions that address the system as a whole.",
            "14. Use Risk Analysis: Evaluate potential risks, uncertainties, and tradeoffs associated with different solutions or approaches to a problem. Emphasize assessing the potential consequences and likelihood of success or failure, and making informed decisions based on a balanced analysis of risks and benefits.",
            "16. What is the core issue or problem that needs to be addressed?",
            "17. What are the underlying causes or factors contributing to the problem?",
            "18. Are there any potential solutions or strategies that have been tried before? If yes, what were the outcomes and lessons learned?",
            "19. What are the potential obstacles or challenges that might arise in solving this problem?",
            "20. Are there any relevant data or information that can provide insights into the problem? If yes, what data sources are available, and how can they be analyzed?",
            "21. Are there any stakeholders or individuals who are directly affected by the problem? What are their perspectives and needs?",
            "22. What resources (financial, human, technological, etc.) are needed to tackle the problem effectively?",
            "23. How can progress or success in solving the problem be measured or evaluated?",
            "24. What indicators or metrics can be used?",
            "25. Is the problem a technical or practical one that requires a specific expertise or skill set? Or is it more of a conceptual or theoretical problem?",
            "26. Does the problem involve a physical constraint, such as limited resources, infrastructure, or space?",
            "27. Is the problem related to human behavior, such as a social, cultural, or psychological issue?",
            "28. Does the problem involve decision-making or planning, where choices need to be made under uncertainty or with competing objectives?",
            "29. Is the problem an analytical one that requires data analysis, modeling, or optimization techniques?",
            "30. Is the problem a design challenge that requires creative solutions and innovation?",
            "31. Does the problem require addressing systemic or structural issues rather than just individual instances?",
            "32. Is the problem time-sensitive or urgent, requiring immediate attention and action?",
            "33. What kinds of solution typically are produced for this kind of problem specification?",
            "34. Given the problem specification and the current best solution, have a guess about other possible solutions.",
            "35. Let's imagine the current best solution is totally wrong, what other ways are there to think about the problem specification?",
            "36. What is the best way to modify this current best solution, given what you know about these kinds of problem specification?",
            "37. Ignoring the current best solution, create an entirely new solution to the problem.",
            "39. Let's make a step by step plan and implement it with good notation and explanation.",
        ]

        # Example task
        task_example = """This SVG path element <path d="M 55.57,80.69 L 57.38,65.80 M 57.38,65.80 L 48.90,57.46 M 48.90,57.46 L
        45.58,47.78 M 45.58,47.78 L 53.25,36.07 L 66.29,48.90 L 78.69,61.09 L 55.57,80.69"/> draws a:
        (A) circle (B) heptagon (C) hexagon (D) kite (E) line (F) octagon (G) pentagon(H) rectangle (I) sector (J) triangle"""

        # Convert reasoning modules to string
        reasoning_modules_str = "\n".join(reasoning_modules)

        # Run the agent
        agent = SelfDiscoverAgent().get_agent()
        config = {"configurable": {"thread_id": "test-session"}}
        result = await agent.ainvoke({"task_description": task_example, "reasoning_modules": reasoning_modules_str}, config)
        print("Results:", result)

    # Run the async main function
    asyncio.run(main())