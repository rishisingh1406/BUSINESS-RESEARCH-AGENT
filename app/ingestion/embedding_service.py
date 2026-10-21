"""Sentence-transformers embedding service.

Loads the model lazily on first use and keeps a single instance per process.
Safe for the single-threaded ingestion worker; not safe to call concurrently
from multiple threads on the same instance.
"""

from __future__ import annotations

import threading

from sentence_transformers import SentenceTransformer


DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 32
DEFAULT_MAX_SEQ_LENGTH = 512
DEFAULT_DEVICE = "cpu"


class LocalEmbeddingService:
    """Local, in-process embedding service backed by sentence-transformers."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        max_seq_length: int = DEFAULT_MAX_SEQ_LENGTH,
        device: str = DEFAULT_DEVICE,
    ) -> None:
        if not model_name.strip():
            raise ValueError("model_name must be non-blank.")
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")
        if max_seq_length <= 0:
            raise ValueError("max_seq_length must be greater than zero.")

        self._model_name = model_name
        self._batch_size = batch_size
        self._max_seq_length = max_seq_length
        self._device = device

        self._model: SentenceTransformer | None = None
        self._model_lock = threading.Lock()

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_model(self) -> SentenceTransformer:
        if self._model is not None:
            return self._model

        with self._model_lock:
            if self._model is None:
                model = SentenceTransformer(
                    self._model_name,
                    device=self._device,
                )
                model.max_seq_length = self._max_seq_length
                self._model = model

        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Return one L2-normalised vector per input text.

        Returns an empty list for empty input without loading the model.
        """
        if not texts:
            return []

        for index, text in enumerate(texts):
            if not isinstance(text, str):
                raise TypeError(
                    f"embed_texts expects strings; item {index} is "
                    f"{type(text).__name__}."
                )

        model = self._get_model()

        vectors = model.encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # sentence-transformers returns numpy arrays or torch tensors
        # depending on version and options; both support .tolist().
        return vectors.tolist()