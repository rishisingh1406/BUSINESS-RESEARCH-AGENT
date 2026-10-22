import pytest

from app.ingestion.bm25_index import Bm25Hit, Bm25Index, tokenize


def make_loader(chunks_by_collection):
    calls = []

    def loader(collection_id):
        calls.append(collection_id)
        return chunks_by_collection.get(collection_id, [])

    loader.calls = calls
    return loader


def test_tokenize_lowercases_and_strips_punctuation():
    assert tokenize("Revenue Grew 12%!") == ["revenue", "grew", "12"]


def test_tokenize_returns_empty_for_non_word_text():
    assert tokenize("!!! ???") == []


def test_search_returns_empty_for_empty_collection():
    index = Bm25Index(make_loader({}))

    assert index.search("unknown-collection", "revenue") == []


def test_search_returns_empty_for_empty_query_without_loading():
    loader = make_loader({"c1": [("chunk-1", "revenue grew")]})
    index = Bm25Index(loader)

    assert index.search("c1", "   ") == []
    # Query validation happens before the loader is called.
    assert loader.calls == []


def test_search_returns_ranked_hits_for_matching_chunks():
    loader = make_loader(
        {
            "c1": [
                ("chunk-a", "revenue increased due to strong sales"),
                ("chunk-b", "revenue increased because expenses fell"),
                ("chunk-c", "unrelated discussion of weather"),
            ]
        }
    )
    index = Bm25Index(loader)

    hits = index.search("c1", "revenue increased", top_k=10)

    # Both a and b contain both query terms; c does not and is excluded.
    # Exact order between a and b depends on BM25's length normalisation
    # (shorter docs rank higher for the same term frequency), which is
    # not our code's concern. We assert the candidate set and that our
    # code returns them in descending score order.
    assert {hit.chunk_id for hit in hits} == {"chunk-a", "chunk-b"}
    assert all(isinstance(hit, Bm25Hit) for hit in hits)

    hit_scores = [hit.score for hit in hits]
    assert hit_scores == sorted(hit_scores, reverse=True)


def test_search_excludes_chunks_without_query_tokens():
    loader = make_loader(
        {
            "c1": [
                ("chunk-a", "revenue increased"),
                ("chunk-b", "nothing about the query here"),
            ]
        }
    )
    index = Bm25Index(loader)

    hits = index.search("c1", "revenue")

    assert [hit.chunk_id for hit in hits] == ["chunk-a"]


def test_search_respects_top_k():
    loader = make_loader(
        {
            "c1": [
                (f"chunk-{i}", "revenue increased") for i in range(10)
            ]
        }
    )
    index = Bm25Index(loader)

    hits = index.search("c1", "revenue", top_k=3)

    assert len(hits) == 3


def test_search_raises_on_invalid_top_k():
    index = Bm25Index(make_loader({}))

    with pytest.raises(ValueError):
        index.search("c1", "revenue", top_k=0)


def test_search_handles_all_empty_corpus():
    loader = make_loader({"c1": [("chunk-a", "!!!"), ("chunk-b", "???")]})
    index = Bm25Index(loader)

    # Guard against BM25Okapi's division by zero on empty corpora.
    assert index.search("c1", "revenue") == []


def test_search_is_isolated_per_collection():
    loader = make_loader(
        {
            "c1": [("chunk-a", "revenue increased")],
            "c2": [("chunk-b", "revenue decreased")],
        }
    )
    index = Bm25Index(loader)

    assert [h.chunk_id for h in index.search("c1", "revenue")] == ["chunk-a"]
    assert [h.chunk_id for h in index.search("c2", "revenue")] == ["chunk-b"]