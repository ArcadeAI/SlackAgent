import json
from logging import Logger
from pathlib import Path

from archer.storage.schema import StateStore, StorageResourceError, UserIdentity


class FileStore(StateStore):
    def __init__(self, base_dir: str, logger: Logger):
        self.base_dir = Path(base_dir)
        self.logger = logger
        self.user_dir = self.base_dir / "users"
        self.state_dir = self.base_dir / "states"

        # Create directories if they don't exist
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_path(self, user_id: str) -> Path:
        return self.user_dir / f"{user_id}.json"

    def _get_state_path(self, state_id: str) -> Path:
        return self.state_dir / f"{state_id}.json"

    def set_state(self, user_identity: UserIdentity) -> None:
        user_path = self._get_user_path(user_identity["user_id"])
        with open(user_path, "w") as f:
            json.dump(user_identity, f, indent=2)

    def get_state(self, user_id: str) -> UserIdentity:
        user_path = self._get_user_path(user_id)
        if not user_path.exists():
            raise StorageResourceError(f"User {user_id} not found")

        with open(user_path) as f:
            return json.load(f)

    def update_state(self, user_identity: UserIdentity) -> None:
        self.set_state(user_identity)

    def save_agent_state(self, state_id: str, state_data: dict) -> None:
        state_path = self._get_state_path(state_id)
        with open(state_path, "w") as f:
            json.dump(state_data, f, indent=2)

    def get_agent_state(self, state_id: str) -> dict:
        state_path = self._get_state_path(state_id)
        if not state_path.exists():
            raise StorageResourceError(f"State {state_id} not found")

        with open(state_path) as f:
            return json.load(f)

    def exists(self, user_id: str) -> bool:
        user_path = self._get_user_path(user_id)
        return user_path.exists()
