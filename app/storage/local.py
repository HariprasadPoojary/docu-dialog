"""Generated-key file storage for local development."""

from pathlib import Path
from typing import BinaryIO
from uuid import uuid4


class UploadTooLargeError(Exception):
    """Raised when an upload exceeds its configured byte limit."""


class LocalFileStorage:
    """Store uploaded bytes below a configured root without using user paths."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def save(self, source: BinaryIO, suffix: str, max_bytes: int) -> tuple[str, int]:
        """Stream a file to a generated key and enforce the byte limit while copying."""

        self.root.mkdir(parents=True, exist_ok=True)
        storage_key = f"{uuid4().hex}{suffix}"
        destination = self._path_for(storage_key)
        byte_count = 0
        source.seek(0)

        try:
            with destination.open("xb") as target:
                while chunk := source.read(64 * 1024):
                    byte_count += len(chunk)
                    if byte_count > max_bytes:
                        raise UploadTooLargeError
                    target.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        return storage_key, byte_count

    def delete(self, storage_key: str) -> None:
        """Delete a file only when its key resolves inside this storage root."""

        self._path_for(storage_key).unlink(missing_ok=True)

    def read(self, storage_key: str) -> bytes:
        """Read one stored file after validating that its key remains within the root."""

        return self._path_for(storage_key).read_bytes()

    def _path_for(self, storage_key: str) -> Path:
        if not storage_key or Path(storage_key).name != storage_key:
            raise ValueError("Invalid storage key")
        path = (self.root / storage_key).resolve()
        path.relative_to(self.root)
        return path
