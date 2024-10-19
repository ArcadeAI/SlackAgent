import json
from typing import Any, Callable, Dict, List, Optional, Type

from arcadepy import Arcade
from arcadepy.types.shared import ToolDefinition
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, ValidationError, create_model

TYPE_MAPPING = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def get_python_type(val_type: str) -> Any:
    """Map Arcade value types to Python types."""
    return TYPE_MAPPING.get(val_type, Any)


def parse_pydantic_error(e: ValidationError) -> str:
    """Convert Pydantic validation errors into a readable string."""
    return str(e)


class ArcadeToolSet:
    """
    Arcade toolset for LangChain framework.

    This class wraps Arcade tools as LangChain `StructuredTool` objects for integration.
    """

    def __init__(self, client: Arcade):
        self.client = client

    def _wrap_action(
        self,
        tool_def: ToolDefinition,
        args_schema: Type[BaseModel],
    ) -> Callable:
        """Wraps an Arcade tool action into a callable function."""

        toolkit_name = tool_def.toolkit.name
        full_tool_name = ".".join([toolkit_name, tool_def.name])
        requires_authorization = tool_def.requirements.authorization is not None

        def tool_function(
            config: RunnableConfig,
            **kwargs: Any,
        ) -> Any:
            """Function that executes the Arcade tool with the given parameters."""
            user_id = config.get("configurable").get("user_id")
            try:
                if requires_authorization:
                    if not user_id:
                        raise ValueError("user_id is required")
                    # Authorize the user for the tool
                    auth_response = self.client.tools.authorize(
                        tool_name=full_tool_name,
                        user_id=user_id,
                    )
                    if auth_response.status != "completed":
                        return {
                            "output": "Please use the following link to authorize: " + auth_response.authorization_url,
                        }

                # Execute the tool with provided inputs
                inputs_json = json.dumps(kwargs)
                execute_response = self.client.tools.execute(
                    tool_name=full_tool_name,
                    inputs=inputs_json,
                    user_id=user_id,
                )
                if execute_response.success:
                    return execute_response.output.value
                else:
                    return execute_response.output.error
            except Exception as e:
                return {"output": str(e)}

        return tool_function

    def _wrap_tool(self, tool_def: ToolDefinition) -> StructuredTool:
        """Wraps an Arcade `ToolDefinition` as a LangChain `StructuredTool`."""
        tool_name = tool_def.name
        description = tool_def.description or "No description provided."

        # Extract input parameters
        fields: Dict[str, Any] = {}
        for param in tool_def.inputs.parameters:
            param_name = param.name
            param_type = get_python_type(param.value_schema.val_type)
            param_description = param.description or "No description provided."
            default = ... if param.required else None
            fields[param_name] = (
                param_type,
                Field(default=default, description=param_description),
            )

        # Create a Pydantic model for the tool's input arguments
        ArgsSchema = create_model(f"{tool_name}Args", **fields)

        # Create the action function
        action_func = self._wrap_action(
            tool_def=tool_def,
            args_schema=ArgsSchema,
        )

        # Create the StructuredTool instance
        tool = StructuredTool.from_function(
            func=action_func,
            name=tool_name,
            description=description,
            args_schema=ArgsSchema,
            inject_kwargs={"user_id"},
        )
        return tool

    def get_tools(self, toolkit: Optional[str] = None) -> List[StructuredTool]:
        """
        Get Arcade tools wrapped as LangChain StructuredTool objects.

        :param toolkit: Optional toolkit name to filter tools.

        :return: List of StructuredTool instances.
        """
        tool_definitions = self.client.tools.list(toolkit=toolkit)
        lc_tools = []
        for tool_def in tool_definitions:
            try:
                lc_tool = self._wrap_tool(tool_def)
                lc_tools.append(lc_tool)
            except Exception as e:
                # Log the error and continue with the next tool
                print(f"Failed to wrap tool '{tool_def.name}': {e}")
        return lc_tools


""" import os

from arcadepy import Arcade

ARCADE_API_KEY = os.environ.get("ARCADE_API_KEY", "")
# Initialize the Arcade client
client = Arcade(api_key=ARCADE_API_KEY)

# Create the ArcadeToolSet
toolset = ArcadeToolSet(client=client)

# Get the list of tools
tools = toolset.get_tools()

# Assuming we have a user ID
user_id = "sam@arcade-ai.com"

# Use a specific tool
for tool in tools:
    if tool.name == "SendDmToUser":
        # Prepare input arguments (excluding user_id, which is injected)
        inputs = {
            "user_name": "nate",
            "message": "Hello Nate, Hoping this langgraph shit works now"
        }
        # Run the tool by passing user_id and the required inputs
        result = tool.invoke(inputs, config={"configurable": {"user_id": user_id}})
        print(f"Result from tool '{tool.name}': {result}")
        break
 """
