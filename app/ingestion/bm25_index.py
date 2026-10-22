"""In-memory BM25 lexical index for a collection's chunks.

Rebuilds the index on each search. For a single collection with a few
hundred to a few thousand chunks, this costs sub-millisecond-to-a-few-ms
per query, which is well within latency budget. Caching can be added
later behind an explicit invalidation hook once the retrieval layer
exists; caching without invalidation is worse than not caching.

BM25 returns only (chunk_id, score) pairs. The retrieval layer is
expected to join these back to document_chunks for provenance.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from rank_bm25 import BM25Okapi


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase, then extract runs of ASCII letters and digits.

    No stemming, no stopword removal — BM25's IDF already down-weights
    frequent terms, and stemming is an optimisation we can defer.
    """
    return _TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True)
class Bm25Hit:
    chunk_id: str
    score: float


class Bm25Index:
    """BM25 lexical search over a collection's chunks."""

    def __init__(
        self,
        loader: Callable[[str], Sequence[tuple[str, str]]],
    ) -> None:
        self._loader = loader

    def search(
        self,
        collection_id: str,
        query: str,
        top_k: int = 20,
    ) -> list[Bm25Hit]:
        """Return top_k chunks by BM25 score.

        Returns [] for an empty collection, an empty query, or a
        collection whose chunks contain no indexable tokens.

        A chunk is a candidate iff it contains at least one query token.
        We deliberately do not filter by score > 0: BM25Okapi yields
        zero (or negative, after rank_bm25's epsilon substitution) IDF
        for query terms that appear in half or more of the corpus, and
        those are still genuine matches that the caller may want to see.
        Score-threshold filtering is the caller's job.
        """
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        chunks = list(self._loader(collection_id))
        if not chunks:
            return []

        chunk_ids = [chunk_id for chunk_id, _ in chunks]
        corpus = [tokenize(text) for _, text in chunks]

        # BM25Okapi divides by average document length; guard against
        # an all-empty corpus to avoid a ZeroDivisionError.
        if not any(corpus):
            return []

        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query_tokens)

        query_token_set = set(query_tokens)
        hits: list[Bm25Hit] = []
        for i, chunk_tokens in enumerate(corpus):
            if not any(token in query_token_set for token in chunk_tokens):
                continue
            hits.append(
                Bm25Hit(chunk_id=chunk_ids[i], score=float(scores[i]))
            )

        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:top_k]