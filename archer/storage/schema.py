from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from archer.storage.schema import UserIdentity


class StorageError(Exception):
    pass


class StorageResourceError(StorageError):
    pass


class StorageConnectionError(StorageError):
    pass


class StateStore:
    def set_state(self, user_identity: "UserIdentity") -> None:
        pass

    def get_state(self, user_id: str) -> "UserIdentity":
        pass

    def update_state(self, user_identity: "UserIdentity") -> None:
        pass

    def save_agent_state(self, state_id: str, state_data: dict) -> None:
        pass

    def get_agent_state(self, state_id: str) -> dict:
        pass

    def exists(self, user_id: str) -> bool:
        pass


class UserIdentity(TypedDict):
    user_id: str
    provider: str
    model: str
