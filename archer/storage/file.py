import json
import logging
import os
from logging import Logger
from pathlib import Path

from archer.storage.schema import StateStore, StorageResourceError, UserIdentity


class FileStore(StateStore):
    def __init__(
        self,
        *,
        base_dir: str = "./data",
        logger: Logger | None = None,
    ):
        self.base_dir = base_dir
        self.logger = logger or logging.getLogger(__name__)
        # Ensure base_dir exists
        self._mkdir(self.base_dir)

    def set_state(self, user_identity: UserIdentity) -> str:
        user_id = user_identity["user_id"]
        filepath = self._get_filepath(user_id)
        self._mkdir(Path(filepath).parent)

        try:
            self._write_json_to_file(filepath, user_identity)
        except Exception as e:
            self.logger.exception("Failed to set state")
            raise StorageResourceError("Failed to set state") from e
        return user_id

    def update_state(self, user_identity: UserIdentity) -> str:
        user_id = user_identity["user_id"]
        filepath = self._get_filepath(user_id)
        self._mkdir(Path(filepath).parent)

        if not os.path.exists(filepath):
            self.logger.warning(f"Data for {user_id} does not exist")
            raise StorageResourceError("Data does not exist")

        try:
            self._write_json_to_file(filepath, user_identity)
        except Exception as e:
            self.logger.exception("Failed to update state")
            raise StorageResourceError("Failed to update state") from e
        return user_id

    def get_state(self, user_id: str) -> UserIdentity:
        filepath = self._get_filepath(user_id)
        try:
            print(f"Getting state for {user_id} from {filepath}")
            with open(filepath) as file:
                data = json.load(file)
            return UserIdentity(**data)
        except FileNotFoundError as e:
            self.logger.warning(f"Failed to find data for {user_id}")
            raise StorageResourceError("Failed to find data") from e
        except json.JSONDecodeError as e:
            self.logger.exception(f"Failed to decode data for {user_id}")
            raise StorageResourceError("Failed to decode data") from e
        except Exception as e:
            self.logger.exception(f"Failed to get state for {user_id}")
            raise StorageResourceError("Failed to get state") from e

    def exists(self, user_id: str | UserIdentity) -> bool:
        if not isinstance(user_id, str):
            user_id = user_id["user_id"]
        filepath = self._get_filepath(user_id)
        return os.path.exists(filepath)

    def _get_filepath(self, user_id: str) -> str:
        """Get the filepath for a user ID."""
        return os.path.join(self.base_dir, self._user_id_to_filename(user_id))

    def _write_json_to_file(self, filepath: str, data: dict) -> None:
        """Write JSON data to a file."""
        with open(filepath, "w") as file:
            file.write(json.dumps(data))

    def _user_id_to_filename(self, user_id: str) -> str:
        """Encode user_id to a safe filename using hex encoding."""
        return user_id.encode("utf-8").hex()

    @staticmethod
    def _mkdir(path) -> None:
        if isinstance(path, str):
            path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
