from app.rag.retriever import Retriever


class FakeVectorStore:
    def __init__(self, scores, ids):
        self.scores = scores
        self.ids = ids

    def search(self, query_vector, top_k):
        return [self.scores[:top_k]], [self.ids[:top_k]]


def create_chunks(count):
    return [
        {
            "content": f"片段{i}",
            "source": "test.txt",
            "chunk_id": i
        }
        for i in range(count)
    ]


def test_retrieve_filters_scores_below_threshold():
    chunks = create_chunks(2)
    retriever = Retriever(
        FakeVectorStore(
            scores=[0.80, 0.54],
            ids=[0, 1]
        ),
        chunks,
        threshold=0.55,
        score_gap=0.10
    )

    results = retriever.retrieve(
        query_vector=[0.1, 0.2],
        top_k=2
    )

    assert len(results) == 1
    assert results[0]["chunk_id"] == 0
    assert results[0]["score"] == 0.80


def test_retrieve_applies_relative_score_gap():
    chunks = create_chunks(3)
    retriever = Retriever(
        FakeVectorStore(
            scores=[0.80, 0.77, 0.70],
            ids=[0, 1, 2]
        ),
        chunks,
        threshold=0.55,
        score_gap=0.04
    )

    results = retriever.retrieve(
        query_vector=[0.1, 0.2],
        top_k=3
    )

    assert [
        result["chunk_id"]
        for result in results
    ] == [0, 1]


def test_retrieve_ignores_invalid_faiss_id():
    retriever = Retriever(
        FakeVectorStore(
            scores=[0.90],
            ids=[-1]
        ),
        create_chunks(1)
    )

    results = retriever.retrieve(
        query_vector=[0.1, 0.2],
        top_k=1
    )

    assert results == []


def test_retrieve_does_not_modify_original_chunks():
    chunks = create_chunks(1)
    retriever = Retriever(
        FakeVectorStore(
            scores=[0.80],
            ids=[0]
        ),
        chunks
    )

    retriever.retrieve(
        query_vector=[0.1, 0.2],
        top_k=1
    )

    assert "score" not in chunks[0]
