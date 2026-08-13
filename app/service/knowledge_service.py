import os
from uuid import uuid4

from app.rag.embedding import get_embedding
from app.rag.loader import load_documents
from app.rag.splitter import split_text
from app.rag.storage import load_chunks, save_chunks
from app.rag.vector_store import FAISSVectorStore


class KnowledgeBuildError(Exception):
    def __init__(self, stage, message):
        super().__init__(message)
        self.stage = stage
        self.message = message

    def to_detail(self):
        return {
            "stage": self.stage,
            "message": self.message
        }


def remove_file_if_exists(path):
    if os.path.exists(path):
        os.remove(path)


def restore_file(
        final_path,
        backup_path,
        had_original
):
    if os.path.exists(backup_path):
        remove_file_if_exists(
            final_path
        )
        os.replace(
            backup_path,
            final_path
        )
    elif (
        not had_original
        and os.path.exists(final_path)
    ):
        os.remove(
            final_path
        )


def rebuild_knowledge_base(
        knowledge_path,
        index_path,
        chunks_path,
        reload_callback=None
):
    try:
        documents = load_documents(
            knowledge_path
        )
    except Exception as error:
        raise KnowledgeBuildError(
            "reading",
            "文档读取或解析失败，请检查文件是否完整"
        ) from error

    if not documents:
        raise KnowledgeBuildError(
            "reading",
            "知识库目录中没有可用文档"
        )

    chunks = []
    source_chunk_counts = {}

    try:
        for document in documents:
            source = document["source"]
            chunk_id_start = source_chunk_counts.get(
                source,
                0
            )

            document_chunks = split_text(
                document["content"],
                source,
                page_number=document.get("page_number"),
                chunk_id_start=chunk_id_start
            )

            chunks.extend(
                document_chunks
            )

            source_chunk_counts[source] = (
                chunk_id_start + len(document_chunks)
            )
    except Exception as error:
        raise KnowledgeBuildError(
            "splitting",
            "文本切块失败，请检查文档内容"
        ) from error

    if not chunks:
        raise KnowledgeBuildError(
            "splitting",
            "文档中没有生成有效的文本片段"
        )

    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    try:
        vectors = get_embedding(
            texts
        )
    except Exception as error:
        raise KnowledgeBuildError(
            "embedding",
            "Embedding向量生成失败，请检查模型服务和网络连接"
        ) from error

    if len(vectors) != len(chunks):
        raise KnowledgeBuildError(
            "embedding",
            "向量数量和文本片段数量不一致"
        )

    dimension = len(
        vectors[0]
    )

    build_id = uuid4().hex
    temporary_index_path = (
        f"{index_path}.building-{build_id}"
    )
    temporary_chunks_path = (
        f"{chunks_path}.building-{build_id}"
    )
    backup_index_path = (
        f"{index_path}.backup-{build_id}"
    )
    backup_chunks_path = (
        f"{chunks_path}.backup-{build_id}"
    )
    index_had_original = os.path.exists(
        index_path
    )
    chunks_had_original = os.path.exists(
        chunks_path
    )
    replacement_started = False
    replacement_completed = False

    try:
        store = FAISSVectorStore(
            dimension
        )

        store.add(
            vectors
        )

        store.save(
            temporary_index_path
        )

        save_chunks(
            chunks,
            temporary_chunks_path
        )

        validation_store = FAISSVectorStore.load(
            temporary_index_path
        )
        validation_chunks = load_chunks(
            temporary_chunks_path
        )

        if (
            validation_store.index.ntotal
            != len(validation_chunks)
        ):
            raise KnowledgeBuildError(
                "saving",
                "临时索引向量数量和文本片段数量不一致"
            )

        replacement_started = True

        if index_had_original:
            os.replace(
                index_path,
                backup_index_path
            )

        if chunks_had_original:
            os.replace(
                chunks_path,
                backup_chunks_path
            )

        os.replace(
            temporary_index_path,
            index_path
        )
        os.replace(
            temporary_chunks_path,
            chunks_path
        )

        if reload_callback is not None:
            try:
                reload_callback()
            except Exception as error:
                raise KnowledgeBuildError(
                    "reloading",
                    "新索引加载失败，系统已恢复旧索引"
                ) from error

        replacement_completed = True

    except Exception as error:
        if replacement_started:
            try:
                restore_file(
                    index_path,
                    backup_index_path,
                    index_had_original
                )
                restore_file(
                    chunks_path,
                    backup_chunks_path,
                    chunks_had_original
                )
            except Exception as rollback_error:
                raise KnowledgeBuildError(
                    "saving",
                    "索引替换失败且自动回滚未完全成功"
                ) from rollback_error

        if isinstance(error, KnowledgeBuildError):
            raise

        raise KnowledgeBuildError(
            "saving",
            "FAISS索引或分块数据保存失败"
        ) from error

    finally:
        remove_file_if_exists(
            temporary_index_path
        )
        remove_file_if_exists(
            temporary_chunks_path
        )

        if replacement_completed:
            remove_file_if_exists(
                backup_index_path
            )
            remove_file_if_exists(
                backup_chunks_path
            )

    return {
        "document_count": len(
            {
                document["source"]
                for document in documents
            }
        ),
        "chunk_count": len(chunks),
        "vector_count": len(vectors)
    }
