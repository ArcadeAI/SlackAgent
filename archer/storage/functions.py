import logging
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
