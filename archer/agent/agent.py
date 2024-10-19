import os
from typing import Annotated

from arcadepy import Arcade
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from archer.agent.utils import ArcadeToolSet
from archer.constants import ARCADE_API_KEY


# Define the State TypedDict
class State(TypedDict):
	messages: Annotated[list, add_messages]


# Define the ChatbotGraph class
class ChatbotGraph:
	def __init__(
 	   self,
		model: str = "gpt-4o",
	):
		# Initialize the LLM with the specified model
		print(f"Using model: {model}")
		self.llm = ChatOpenAI(
			model=model,
		)

		client = Arcade(api_key=ARCADE_API_KEY)

		# Initialize Arcade tools
		self.tools = ArcadeToolSet(client).get_tools()
		self.llm_with_tools = self.llm.bind_tools(self.tools)

		# Setup the graph with tools
		self.setup_graph()

	def chatbot_node(self, state: State):
		# Use the LLM with tools to generate a response
		ai_message = self.llm_with_tools.invoke(state["messages"])
		# Update the state with the assistant's message
		return {"messages": state["messages"] + [ai_message]}

	def setup_graph(self):
		# Initialize the state graph
		self.graph_builder = StateGraph(state_schema=State)

		# Add the chatbot node
		self.graph_builder.add_node("chatbot", self.chatbot_node)

		# Add the tools node
		tool_node = ToolNode(tools=self.tools)
		self.graph_builder.add_node("tools", tool_node)

		# Define entry and exit points
		self.graph_builder.add_edge(START, "chatbot")
		self.graph_builder.add_edge("chatbot", END)

		# Define the routing function
		def route_tools(state: State):
			"""
			Use in the conditional_edge to route to the ToolNode if the last message
			has tool calls. Otherwise, route to the end.
			"""
			if isinstance(state, list):
				ai_message = state[-1]
			elif messages := state.get("messages", []):
				ai_message = messages[-1]
			else:
				raise ValueError(f"No messages found in input state to tool_edge: {state}")
			if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
				return "tools"
			return END

		# Add conditional edges based on tool calls
		self.graph_builder.add_conditional_edges(
			"chatbot",
			route_tools,
			{"tools": "tools", END: END},
		)

		# Any time a tool is called, return to the chatbot
		self.graph_builder.add_edge("tools", "chatbot")

		# Compile the graph
		self.graph = self.graph_builder.compile()

	def get_graph(self):
		return self.graph


if __name__ == "__main__":
	config = {
		"configurable": {
			"user_id": os.environ.get("ARCADE_USER_ID", "sam@arcade-ai.com"),
		}
	}
	ChatbotGraph().get_graph().invoke(
		{"messages": [{"role": "user", "content": "Hello, how are you?"}]},
		config=config
	)
