from app.rag.embedding import get_query_embedding
from app.rag.generator import generate
from app.paths import CHUNKS_PATH, INDEX_PATH
from app.rag.retriever import Retriever
from app.rag.storage import load_chunks
from app.rag.vector_store import FAISSVectorStore
from app.service.rag_service import RAGService


class RAGRuntime:
    def __init__(
            self,
            index_path,
            chunks_path,
            threshold=0.55,
            score_gap=0.04
    ):
        self.index_path = index_path
        self.chunks_path = chunks_path
        self.threshold = threshold
        self.score_gap = score_gap
        self.rag_service = None

        self.reload()

    def reload(self):
        new_store = FAISSVectorStore.load(
            self.index_path
        )

        new_chunks = load_chunks(
            self.chunks_path
        )

        vector_count = (
            new_store.index.ntotal
        )

        if vector_count != len(new_chunks):
            raise ValueError(
                "索引向量数量和文本片段数量不一致"
            )

        new_retriever = Retriever(
            new_store,
            new_chunks,
            threshold=self.threshold,
            score_gap=self.score_gap
        )

        new_rag_service = RAGService(
            new_retriever,
            get_query_embedding,
            generate
        )

        self.rag_service = new_rag_service

        return {
            "vector_count": vector_count,
            "chunk_count": len(new_chunks)
        }

    def chat(
            self,
            query,
            user_id=None,
            conversation_id=None
    ):
        return self.rag_service.chat(
            query,
            user_id,
            conversation_id
        )

    def get_statistics(self):
        retriever = self.rag_service.retriever

        return {
            "chunk_count": len(retriever.chunks),
            "vector_count": retriever.vector_store.index.ntotal,
            "threshold": retriever.threshold,
            "score_gap": retriever.score_gap,
            "top_k": self.rag_service.TOP_K
        }


rag_runtime = RAGRuntime(
    index_path=str(INDEX_PATH),
    chunks_path=str(CHUNKS_PATH),
    threshold=0.55,
    score_gap=0.04
)
