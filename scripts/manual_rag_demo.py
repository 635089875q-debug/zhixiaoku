import time
from openai import OpenAI
from app.config import settings
from app.rag.vector_store import FAISSVectorStore
from app.rag.retriever import Retriever
from app.rag.storage import load_chunks
from app.service.rag_service import RAGService
from app.rag.embedding import get_query_embedding
from app.rag.generator import generate
from app.paths import CHUNKS_PATH, INDEX_PATH

client = OpenAI(
    api_key=settings.SILICONFLOW_API_KEY,
    base_url=settings.BASE_URL
)

query = "深大在哪里"

store = FAISSVectorStore.load(
    str(INDEX_PATH)
)

chunks = load_chunks(
    str(CHUNKS_PATH)
)

retriever = Retriever(
    store,
    chunks,
    threshold=0.5
)

rag = RAGService(
    retriever,
    get_query_embedding,
    generate
)

start = time.time()

answer = rag.chat(
    query
)

print(
    "总耗时:",
    time.time() - start,
    "秒"
)

print(
    "AI回答:",
    answer
)
