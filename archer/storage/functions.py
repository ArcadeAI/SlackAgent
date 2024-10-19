import logging
from typing import TYPE_CHECKING

from archer.constants import FILE_STORAGE_BASE_DIR, STORAGE_TYPE
from archer.storage.file import FileStore
from archer.storage.schema import UserIdentity

if TYPE_CHECKING:
    from archer.storage.schema import StateStore

logger = logging.getLogger(__name__)


def get_store() -> "StateStore":
    if STORAGE_TYPE == "file":
        return FileStore.init_or_connect(base_dir=FILE_STORAGE_BASE_DIR, logger=logger)
    else:
        raise ValueError(f"Invalid storage type: {STORAGE_TYPE}")

def set_user_state(
    user_id: str,
    provider_name: str = None,
    model_name: str = None
) -> None:
    user = UserIdentity(user_id=user_id, provider=provider_name, model=model_name)
    store = get_store()
    store.set_state(user)

def get_user_state(user_id: str) -> UserIdentity:
    store = get_store()
    return store.get_state(user_id)

def update_user_state(
    user_id: str,
    provider_name: str = None,
    model_name: str = None
) -> None:
    user_state = get_user_state(user_id)
    if provider_name:
        user_state["provider"] = provider_name
    if model_name:
        user_state["model"] = model_name

    store = get_store()
    store.update_state(user_state)
