import json
import logging
from pathlib import Path

from archer.storage.schema import StateStore, StorageResourceError, UserIdentity


class FileStore(StateStore):
    def __init__(
        self,
        *,
        base_dir: str = "./data",
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self.base_dir = base_dir
        self.logger = logger

    def set_state(self, user_identity: UserIdentity):
        user_id = user_identity["user_id"]
        self._mkdir(self.base_dir)
        filepath = f"{self.base_dir}/{user_id}"

        try:
            with open(filepath, "w") as file:
                data = json.dumps(user_identity)
                file.write(data)
        except Exception as e:
            self.logger.error(f"Failed to set state for {user_id} - {e}")
            raise StorageResourceError(f"Failed to set state for {user_id} - {e}")
        return user_id

    def update_state(self, user_identity: UserIdentity):
        user_id = user_identity["user_id"]
        filepath = f"{self.base_dir}/{user_id}"
        try:
            with open(filepath, "w") as file:
                data = json.dumps(user_identity)
                file.write(data)
        except FileNotFoundError as e:
            self.logger.warning(f"Failed to find data for {user_id} - {e}")
            raise StorageResourceError(f"Failed to find data for {user_id} - {e}")
        except Exception as e:
            self.logger.error(f"Failed to update state for {user_id} - {e}")
            raise StorageResourceError(f"Failed to update state for {user_id} - {e}")
        return user_id

    def get_state(self, user_id: str) -> UserIdentity:
        filepath = f"{self.base_dir}/{user_id}"
        try:
            with open(filepath, "r") as file:
                data = json.load(file)
                return UserIdentity(**data)
        except FileNotFoundError as e:
            self.logger.warning(f"Failed to find data for {user_id} - {e}")
            raise StorageResourceError(f"Failed to find data for {user_id} - {e}")

    @staticmethod
    def _mkdir(path) -> None:
        if isinstance(path, str):
            path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
