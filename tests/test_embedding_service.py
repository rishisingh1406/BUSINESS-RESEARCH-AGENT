import numpy as np
import pytest

from app.ingestion.embedding_service import LocalEmbeddingService


class StubModel:
    """Deterministic stub; avoids downloading the real model in unit tests."""

    def __init__(self, dim: int = 4) -> None:
        self.max_seq_length = 512
        self._dim = dim
        self.encode_calls: list[dict] = []

    def encode(self, texts, **kwargs):
        self.encode_calls.append({"texts": list(texts), "kwargs": dict(kwargs)})
        return np.array(
            [[0.1] * self._dim for _ in texts],
            dtype=np.float32,
        )


def test_embed_texts_returns_one_vector_per_text():
    service = LocalEmbeddingService()
    service._model = StubModel()

    result = service.embed_texts(["hello", "world"])

    assert np.allclose(result, [[0.1, 0.1, 0.1, 0.1], [0.1, 0.1, 0.1, 0.1]])
    


def test_embed_texts_empty_returns_empty_without_loading_model(monkeypatch):
    service = LocalEmbeddingService()

    def fail_if_loaded():
        pytest.fail("Model must not be loaded for empty input.")

    monkeypatch.setattr(service, "_get_model", fail_if_loaded)

    assert service.embed_texts([]) == []


def test_embed_texts_rejects_non_string_input():
    service = LocalEmbeddingService()
    service._model = StubModel()

    with pytest.raises(TypeError):
        service.embed_texts(["ok", 123])  # type: ignore[list-item]


def test_embed_texts_passes_batch_and_normalise_options():
    service = LocalEmbeddingService(batch_size=8)
    stub = StubModel()
    service._model = stub

    service.embed_texts(["one"])

    assert stub.encode_calls[0]["kwargs"]["batch_size"] == 8
    assert stub.encode_calls[0]["kwargs"]["normalize_embeddings"] is True


def test_constructor_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        LocalEmbeddingService(batch_size=0)
    with pytest.raises(ValueError):
        LocalEmbeddingService(max_seq_length=0)
    with pytest.raises(ValueError):
        LocalEmbeddingService(model_name="   ")