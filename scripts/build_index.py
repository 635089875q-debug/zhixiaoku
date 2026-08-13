from app.service.knowledge_service import rebuild_knowledge_base
from app.paths import CHUNKS_PATH, DOCUMENTS_PATH, INDEX_PATH


KNOWLEDGE_PATH = str(DOCUMENTS_PATH)
INDEX_FILE_PATH = str(INDEX_PATH)
CHUNKS_FILE_PATH = str(CHUNKS_PATH)


def build_index():
    result = rebuild_knowledge_base(
        KNOWLEDGE_PATH,
        INDEX_FILE_PATH,
        CHUNKS_FILE_PATH
    )

    print(
        f"建库完成，共处理"
        f"{result['document_count']}个文档，"
        f"生成{result['chunk_count']}个文本片段，"
        f"写入{result['vector_count']}个向量"
    )


if __name__ == "__main__":
    build_index()
