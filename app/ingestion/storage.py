from pathlib import Path
from urllib.parse import unquote, urlsplit


class StorageResolutionError(ValueError):
    """Raised when a storage URI cannot resolve to a local file."""


def resolve_storage_uri(storage_uri: str) -> Path:
    """Resolve a file:// URI to an existing local regular file."""
    if not storage_uri or not storage_uri.strip():
        raise StorageResolutionError("Storage URI must not be empty.")

    try:
        parsed = urlsplit(storage_uri)
    except ValueError as exc:
        raise StorageResolutionError("Invalid storage URI.") from exc

    if parsed.scheme.lower() != "file":
        raise StorageResolutionError(
            "Only file:// storage URIs are supported."
        )

    if parsed.query or parsed.fragment:
        raise StorageResolutionError(
            "File URI must not contain a query or fragment."
        )

    if parsed.netloc not in ("", "localhost"):
        raise StorageResolutionError(
            "Remote file URI authorities are not supported."
        )

    if not parsed.path:
        raise StorageResolutionError("File URI must include a path.")

    path = Path(unquote(parsed.path))

    # file:///C:/... is the usual Windows file URI form.
    if path.as_posix().startswith("/") and len(path.parts) > 1:
        drive = path.parts[1]
        if len(drive) == 2 and drive[1] == ":":
            path = Path(drive + "/" + "/".join(path.parts[2:]))

    path = path.resolve()

    if not path.is_file():
        raise StorageResolutionError(
            "Storage URI must point to an existing regular file."
        )

    return path
