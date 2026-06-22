from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.data.env_loader import load_repo_env


class RepoEnvLoaderTest(unittest.TestCase):
    def test_loads_standard_key_value_without_overriding_existing_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("APCA_API_KEY_ID=file_key\nAPCA_API_SECRET_KEY=file_secret\n", encoding="utf-8")
            old_key = os.environ.get("APCA_API_KEY_ID")
            old_secret = os.environ.get("APCA_API_SECRET_KEY")
            try:
                os.environ["APCA_API_KEY_ID"] = "existing"
                os.environ.pop("APCA_API_SECRET_KEY", None)
                loaded = load_repo_env(path)
                self.assertEqual(loaded["APCA_API_KEY_ID"], "file_key")
                self.assertEqual(os.environ["APCA_API_KEY_ID"], "existing")
                self.assertEqual(os.environ["APCA_API_SECRET_KEY"], "file_secret")
            finally:
                _restore("APCA_API_KEY_ID", old_key)
                _restore("APCA_API_SECRET_KEY", old_secret)

    def test_loads_user_alpaca_shorthand(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("secret key file_secret\nkey file_key\n", encoding="utf-8")
            old_key = os.environ.get("APCA_API_KEY_ID")
            old_secret = os.environ.get("APCA_API_SECRET_KEY")
            try:
                os.environ.pop("APCA_API_KEY_ID", None)
                os.environ.pop("APCA_API_SECRET_KEY", None)
                load_repo_env(path)
                self.assertEqual(os.environ["APCA_API_KEY_ID"], "file_key")
                self.assertEqual(os.environ["APCA_API_SECRET_KEY"], "file_secret")
            finally:
                _restore("APCA_API_KEY_ID", old_key)
                _restore("APCA_API_SECRET_KEY", old_secret)

    def test_loads_user_space_separated_key_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("API KEY=file_key\nSECRET API KEY=file_secret\n", encoding="utf-8")
            old_key = os.environ.get("APCA_API_KEY_ID")
            old_secret = os.environ.get("APCA_API_SECRET_KEY")
            try:
                os.environ.pop("APCA_API_KEY_ID", None)
                os.environ.pop("APCA_API_SECRET_KEY", None)
                load_repo_env(path)
                self.assertEqual(os.environ["APCA_API_KEY_ID"], "file_key")
                self.assertEqual(os.environ["APCA_API_SECRET_KEY"], "file_secret")
            finally:
                _restore("APCA_API_KEY_ID", old_key)
                _restore("APCA_API_SECRET_KEY", old_secret)


def _restore(key: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
