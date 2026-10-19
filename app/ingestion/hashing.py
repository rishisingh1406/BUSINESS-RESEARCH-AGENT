
import hashlib
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    """Return the lowercase SHA-256 hex digest of a file's contents."""
    digest = hashlib.sha256()

    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()
