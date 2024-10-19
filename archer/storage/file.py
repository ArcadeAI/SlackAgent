import json
import logging
import os
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
        # Ensure base_dir exists
        self._mkdir(self.base_dir)

    def set_state(self, user_identity: UserIdentity):
        user_id = user_identity["user_id"]
        filepath = os.path.join(self.base_dir, self._user_id_to_filename(user_id))
        self._mkdir(os.path.dirname(filepath))

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
        filepath = os.path.join(self.base_dir, self._user_id_to_filename(user_id))
        self._mkdir(os.path.dirname(filepath))

        if not os.path.exists(filepath):
            self.logger.warning(f"Data for {user_id} does not exist")
            raise StorageResourceError(f"Data for {user_id} does not exist")

        try:
            with open(filepath, "w") as file:
                data = json.dumps(user_identity)
                file.write(data)
        except Exception as e:
            self.logger.error(f"Failed to update state for {user_id} - {e}")
            raise StorageResourceError(f"Failed to update state for {user_id} - {e}")
        return user_id

    def get_state(self, user_id: str) -> UserIdentity:
        filepath = os.path.join(self.base_dir, self._user_id_to_filename(user_id))
        try:
            print(f"Getting state for {user_id} from {filepath}")
            with open(filepath, "r") as file:
                data = json.load(file)
            return UserIdentity(**data)
        except FileNotFoundError as e:
            self.logger.warning(f"Failed to find data for {user_id} - {e}")
            raise StorageResourceError(f"Failed to find data for {user_id} - {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode data for {user_id} - {e}")
            raise StorageResourceError(f"Failed to decode data for {user_id} - {e}")
        except Exception as e:
            self.logger.error(f"Failed to get state for {user_id} - {e}")
            raise StorageResourceError(f"Failed to get state for {user_id} - {e}")

    def exists(self, user_id: str) -> bool:
        filepath = os.path.join(self.base_dir, self._user_id_to_filename(user_id))
        return os.path.exists(filepath)

    def _user_id_to_filename(self, user_id: str) -> str:
        # Encode user_id to a safe filename using hex encoding
        return user_id.encode('utf-8').hex()

    @staticmethod
    def _mkdir(path) -> None:
        if isinstance(path, str):
            path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
