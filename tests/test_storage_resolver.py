from pathlib import Path

import pytest

from app.ingestion.storage import StorageResolutionError, resolve_storage_uri


def test_resolves_file_uri_to_existing_file(tmp_path: Path):
    document = tmp_path / "annual_report.pdf"
    document.write_bytes(b"%PDF-test")

    resolved = resolve_storage_uri(document.as_uri())

    assert resolved == document.resolve()
    assert resolved.is_file()


def test_rejects_missing_file_uri(tmp_path: Path):
    missing_file = tmp_path / "missing.pdf"

    with pytest.raises(StorageResolutionError):
        resolve_storage_uri(missing_file.as_uri())


@pytest.mark.parametrize(
    "storage_uri",
    [
        "s3://bucket/annual_report.pdf",
        "https://example.com/annual_report.pdf",
    ],
)
def test_rejects_unsupported_uri_schemes(storage_uri: str):
    with pytest.raises(StorageResolutionError):
        resolve_storage_uri(storage_uri)


def test_rejects_directory_file_uri(tmp_path: Path):
    with pytest.raises(StorageResolutionError):
        resolve_storage_uri(tmp_path.as_uri())
