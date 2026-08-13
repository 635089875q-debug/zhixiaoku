
class Retriever:
    def __init__(
            self,
            vector_store,
            chunks,
            threshold=0.55,
            score_gap=0.04
    ):
        self.vector_store = vector_store
        self.chunks = chunks
        self.threshold = threshold
        self.score_gap = score_gap

    def retrieve(
            self,
            query_vector,
            top_k
    ):
        scores, ids = self.vector_store.search(
            query_vector,
            top_k
        )
        candidates = []

        for score, i in zip(scores[0], ids[0]):
            if i == -1:
                continue

            score = float(score)

            if score >= self.threshold:
                document = self.chunks[i].copy()
                document["score"] = score
                candidates.append(document)

        if not candidates:
            return []

        best_score = max(
            document["score"]
            for document in candidates
        )

        relative_threshold = (
            best_score - self.score_gap
        )

        return [
            document
            for document in candidates
            if document["score"] >= relative_threshold
        ]
