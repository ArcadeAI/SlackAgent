import copy
import logging
import pickle
import uuid
from typing import TYPE_CHECKING

from archer.env import FILE_STORAGE_BASE_DIR, STORAGE_TYPE
from archer.storage.file import FileStore
from archer.storage.schema import UserIdentity

if TYPE_CHECKING:
    from archer.storage.schema import StateStore

logger = logging.getLogger(__name__)


def get_store() -> "StateStore":
    if STORAGE_TYPE == "file":
        return FileStore(base_dir=FILE_STORAGE_BASE_DIR, logger=logger)
    else:
        msg = f"Invalid storage type: {STORAGE_TYPE}"
        logger.error(msg)
        raise ValueError(msg)


def set_user_state(user_id: str, provider: str, model: str) -> UserIdentity:
    user = UserIdentity(user_id=user_id, provider=provider, model=model)
    store = get_store()
    store.set_state(user)
    return user


def get_user_state(user_id: str) -> UserIdentity:
    store = get_store()
    if store.exists(user_id):
        return store.get_state(user_id)
    else:
        return set_user_state(user_id, "openai", "gpt-4o")


def update_user_state(user_id: str, provider: str | None = None, model: str | None = None) -> None:
    user_state = get_user_state(user_id)
    if provider:
        user_state["provider"] = provider
    if model:
        user_state["model"] = model

    store = get_store()
    store.update_state(user_state)


def save_agent_state(state_data: dict) -> str:
    """
    Save an agent state to storage and return a unique ID for retrieving it

    Args:
        state_data: The agent state to save

    Returns:
        str: A unique identifier for the saved state
    """
    # Create a deep copy to avoid modifying the original

    state_to_save = copy.deepcopy(state_data)

    # Generate a unique ID and save the state using pickle
    state_id = str(uuid.uuid4())
    store = get_store()

    try:
        # Use pickle to serialize the entire state object
        store.save_agent_state(state_id, state_to_save)
        logger.info(f"Saved agent state with ID: {state_id}")
        return state_id
    except Exception:
        logger.exception("Failed to pickle agent state")
        raise


def get_agent_state(state_id: str) -> dict:
    """
    Retrieve an agent state by its ID and prepare it for reuse

    Args:
        state_id: The ID of the agent state to retrieve

    Returns:
        dict: The retrieved agent state, ready for use
    """
    store = get_store()
    state = store.get_agent_state(state_id)

    # Ensure the state has the expected structure for LangGraph
    if "messages" not in state:
        logger.warning(f"Retrieved state with ID {state_id} is missing 'messages' key")
        state["messages"] = []

    # Clear auth_urls to prevent re-triggering authorization
    if "auth_urls" in state:
        # Set auth_urls to empty dict or with None values to indicate authorization is complete
        user_ids = list(state["auth_urls"].keys())
        state["auth_urls"] = {user_id: None for user_id in user_ids}

    # Fix tool calls without responses
    if "messages" in state and len(state["messages"]) > 0:
        messages = state["messages"]

        # Find the last assistant message with tool calls
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]

            # Check if this is an assistant message with tool calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                # Get all tool call IDs from this message
                tool_call_ids = [tc["id"] for tc in msg.tool_calls]

                # Check if we have tool response messages for each tool call
                missing_tool_responses = set(tool_call_ids)

                # Look for tool response messages after this message
                for j in range(i + 1, len(messages)):
                    if (
                        hasattr(messages[j], "tool_call_id")
                        and messages[j].tool_call_id in missing_tool_responses
                    ):
                        missing_tool_responses.remove(messages[j].tool_call_id)

                # If we have missing tool responses, add dummy tool response messages
                if missing_tool_responses:
                    logger.warning(
                        f"Adding dummy tool responses for {len(missing_tool_responses)} missing tool calls"
                    )

                    # Find the index where we should insert the tool responses
                    insert_idx = i + 1

                    # Create dummy tool response messages for each missing tool call
                    for tool_call_id in missing_tool_responses:
                        # Find the corresponding tool call to get the tool name
                        tool_call = next(
                            (tc for tc in msg.tool_calls if tc["id"] == tool_call_id), None
                        )
                        if tool_call:
                            tool_name = tool_call.get("name", "unknown_tool")

                            # Create a dummy tool response message
                            from langchain_core.messages import ToolMessage

                            tool_response = ToolMessage(
                                content="Authorization completed. Tool ready to use.",
                                tool_call_id=tool_call_id,
                                name=tool_name,
                            )

                            # Insert the tool response message
                            messages.insert(insert_idx, tool_response)
                            insert_idx += 1

                # We only need to fix the most recent assistant message with tool calls
                break

    return state
