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
        # Set auth_urls values to None to indicate authorization is complete
        user_ids = list(state["auth_urls"].keys())
        state["auth_urls"] = {user_id: None for user_id in user_ids}


    return state
