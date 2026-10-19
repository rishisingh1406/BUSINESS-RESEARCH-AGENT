
import hashlib

from app.ingestion.hashing import sha256_file


def test_sha256_file_matches_digest_of_actual_bytes(tmp_path):
    document = tmp_path / "report.md"
    content = b"# Annual Report\nRevenue increased."

    document.write_bytes(content)

    assert sha256_file(document) == hashlib.sha256(content).hexdigest()


def test_identical_file_contents_produce_identical_hashes(tmp_path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    content = b"Identical report content"

    first.write_bytes(content)
    second.write_bytes(content)

    assert sha256_file(first) == sha256_file(second)


def test_different_file_contents_produce_different_hashes(tmp_path):
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"

    first.write_bytes(b"Report A")
    second.write_bytes(b"Report B")

    assert sha256_file(first) != sha256_file(second)
