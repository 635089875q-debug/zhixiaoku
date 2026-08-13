import os
from datetime import datetime
from threading import Lock

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile
)
from pydantic import BaseModel

from app.dependencies import (
    get_current_user,
    require_admin,
)
from app.rag.loader import (
    load_docx,
    load_pdf,
    load_txt
)
from app.rag.storage import load_chunks
from app.paths import DOCUMENTS_PATH
from app.service.knowledge_service import (
    KnowledgeBuildError,
    rebuild_knowledge_base
)
from app.service.rag_runtime import rag_runtime


router = APIRouter()


KNOWLEDGE_PATH = str(DOCUMENTS_PATH)

SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".txt",
    ".docx",
    ".pdf"
}

KNOWLEDGE_BUILD_LOCK = Lock()


def acquire_knowledge_build_lock():
    if not KNOWLEDGE_BUILD_LOCK.acquire(
        blocking=False
    ):
        raise HTTPException(
            status_code=409,
            detail="知识库正在更新，请稍后重试"
        )

    try:
        yield
    finally:
        KNOWLEDGE_BUILD_LOCK.release()


def get_document_extension(filename):
    return os.path.splitext(
        filename
    )[1].lower()


def is_supported_document(filename):
    return get_document_extension(
        filename
    ) in SUPPORTED_DOCUMENT_EXTENSIONS


def read_document_content(file_path):
    extension = get_document_extension(
        file_path
    )

    if extension == ".txt":
        return load_txt(
            file_path
        )

    if extension == ".docx":
        return load_docx(
            file_path
        )

    if extension == ".pdf":
        return load_pdf(
            file_path
        )

    raise ValueError(
        "不支持的文档格式"
    )


class KnowledgeUploadRequest(BaseModel):
    filename: str
    content: str
    overwrite: bool = False


@router.post("/knowledge/upload-file")
async def upload_knowledge_file(
        file: UploadFile = File(...),
        overwrite: bool = Form(False),
        _admin=Depends(require_admin),
        _knowledge_lock: None = Depends(
            acquire_knowledge_build_lock
        )
):
    file_path = None
    backup_path = None
    saved_new_file = False

    try:
        original_filename = (
            file.filename or ""
        )

        filename = os.path.basename(
            original_filename
        )

        extension = get_document_extension(
            filename
        )

        if (
            not filename
            or filename != original_filename
        ):
            raise HTTPException(
                status_code=400,
                detail="文件名不合法"
            )

        if extension not in SUPPORTED_DOCUMENT_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="目前只支持txt、docx和pdf文件"
            )

        file_content = await file.read()

        if not file_content:
            raise HTTPException(
                status_code=400,
                detail="文件内容不能为空"
            )

        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="文件大小不能超过10MB"
            )

        file_path = os.path.join(
            KNOWLEDGE_PATH,
            filename
        )

        if (
            os.path.exists(file_path)
            and not overwrite
        ):
            raise HTTPException(
                status_code=409,
                detail="同名文件已经存在，如需覆盖请勾选覆盖选项"
            )

        if os.path.exists(file_path):
            backup_path = (
                file_path + ".upload_backup"
            )

            if os.path.exists(backup_path):
                raise HTTPException(
                    status_code=409,
                    detail="该文档存在未完成的覆盖操作"
                )

            os.replace(
                file_path,
                backup_path
            )

        with open(
            file_path,
            "wb"
        ) as saved_file:
            saved_file.write(
                file_content
            )

        saved_new_file = True

        try:
            extracted_content = read_document_content(
                file_path
            )
        except Exception as parse_error:
            raise HTTPException(
                status_code=400,
                detail=f"文档解析失败：{parse_error}"
            ) from parse_error

        if not extracted_content.strip():
            os.remove(
                file_path
            )

            saved_new_file = False

            raise HTTPException(
                status_code=400,
                detail="文档中没有可读取的文字"
            )

        result = rebuild_knowledge_base(
            KNOWLEDGE_PATH,
            rag_runtime.index_path,
            rag_runtime.chunks_path,
            reload_callback=rag_runtime.reload
        )

        completed_backup = backup_path
        backup_path = None

        if (
            completed_backup is not None
            and os.path.exists(completed_backup)
        ):
            try:
                os.remove(
                    completed_backup
                )
            except OSError as cleanup_error:
                print(cleanup_error)

        return {
            "message": "文件上传并重新建库成功",
            "filename": filename,
            "document_count": result[
                "document_count"
            ],
            "chunk_count": result[
                "chunk_count"
            ],
            "vector_count": result["vector_count"]
        }

    except HTTPException:
        if (
            saved_new_file
            and file_path is not None
            and os.path.exists(file_path)
        ):
            os.remove(
                file_path
            )

        if (
            backup_path is not None
            and os.path.exists(backup_path)
        ):
            os.replace(
                backup_path,
                file_path
            )

        raise

    except Exception as error:
        print(error)

        if (
            saved_new_file
            and file_path is not None
            and os.path.exists(file_path)
        ):
            os.remove(
                file_path
            )

        if (
            backup_path is not None
            and os.path.exists(backup_path)
        ):
            os.replace(
                backup_path,
                file_path
            )

        if isinstance(error, KnowledgeBuildError):
            raise HTTPException(
                status_code=500,
                detail=error.to_detail()
            ) from error

        raise HTTPException(
            status_code=500,
            detail="文件上传或建库失败"
        ) from error

    finally:
        await file.close()


@router.post("/knowledge/rebuild")
def rebuild_knowledge(
        _admin=Depends(require_admin),
        _knowledge_lock: None = Depends(
            acquire_knowledge_build_lock
        )
):
    try:
        result = rebuild_knowledge_base(
            KNOWLEDGE_PATH,
            rag_runtime.index_path,
            rag_runtime.chunks_path,
            reload_callback=rag_runtime.reload
        )

        return {
            "message": "知识库重新建库成功",
            "document_count": result["document_count"],
            "chunk_count": result["chunk_count"],
            "vector_count": result["vector_count"]
        }

    except KnowledgeBuildError as error:
        print(error)

        raise HTTPException(
            status_code=500,
            detail=error.to_detail()
        ) from error

    except Exception as e:
        print(e)

        raise HTTPException(
            status_code=500,
            detail="知识库重新建库失败"
        )


@router.get("/knowledge/stats")
def get_knowledge_statistics(
        _current_user=Depends(get_current_user)
):
    try:
        document_count = len(
            [
                filename
                for filename in os.listdir(KNOWLEDGE_PATH)
                if (
                    is_supported_document(filename)
                    and os.path.isfile(
                        os.path.join(KNOWLEDGE_PATH, filename)
                    )
                )
            ]
        )

        runtime_statistics = rag_runtime.get_statistics()
        index_files = [
            rag_runtime.index_path,
            rag_runtime.chunks_path
        ]
        existing_index_files = [
            path
            for path in index_files
            if os.path.isfile(path)
        ]

        last_built_at = None

        if existing_index_files:
            last_built_at = datetime.fromtimestamp(
                max(
                    os.path.getmtime(path)
                    for path in existing_index_files
                )
            ).isoformat(timespec="seconds")

        return {
            "document_count": document_count,
            "chunk_count": runtime_statistics["chunk_count"],
            "vector_count": runtime_statistics["vector_count"],
            "last_built_at": last_built_at,
            "supported_formats": ["TXT", "DOCX", "PDF"],
            "threshold": runtime_statistics["threshold"],
            "score_gap": runtime_statistics["score_gap"],
            "top_k": runtime_statistics["top_k"]
        }

    except Exception as error:
        print(error)

        raise HTTPException(
            status_code=500,
            detail="知识库统计信息查询失败"
        ) from error


@router.get("/knowledge/documents")
def list_knowledge_documents(
        _current_user=Depends(get_current_user)
):
    try:
        documents = []

        for filename in sorted(
            os.listdir(KNOWLEDGE_PATH)
        ):
            file_path = os.path.join(
                KNOWLEDGE_PATH,
                filename
            )

            if (
                not os.path.isfile(file_path)
                or not is_supported_document(filename)
            ):
                continue

            documents.append(
                {
                    "filename": filename,
                    "size_bytes": os.path.getsize(file_path),
                    "updated_at": datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    ).isoformat(timespec="seconds")
                }
            )

        return {
            "document_count": len(documents),
            "documents": documents
        }

    except Exception as e:
        print(e)

        raise HTTPException(
            status_code=500,
            detail="知识库文档列表查询失败"
        )


@router.get("/knowledge/documents/{filename}")
def get_knowledge_document(
        filename: str,
        _current_user=Depends(get_current_user)
):
    try:
        safe_filename = os.path.basename(
            filename
        )

        if (
            safe_filename != filename
            or not is_supported_document(safe_filename)
        ):
            raise HTTPException(
                status_code=400,
                detail="文件名不合法或格式不受支持"
            )

        file_path = os.path.join(
            KNOWLEDGE_PATH,
            safe_filename
        )

        if not os.path.isfile(file_path):
            raise HTTPException(
                status_code=404,
                detail="文档不存在"
            )

        content = read_document_content(
            file_path
        )

        document_chunks = [
            {
                "chunk_id": chunk["chunk_id"],
                "content": chunk["content"],
                "character_count": len(chunk["content"]),
                "page_number": chunk.get("page_number")
            }
            for chunk in load_chunks(rag_runtime.chunks_path)
            if chunk.get("source") == safe_filename
        ]

        document_chunks.sort(
            key=lambda chunk: chunk["chunk_id"]
        )

        return {
            "filename": safe_filename,
            "size_bytes": os.path.getsize(file_path),
            "updated_at": datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).isoformat(timespec="seconds"),
            "content": content,
            "chunk_count": len(document_chunks),
            "chunks": document_chunks
        }

    except HTTPException:
        raise

    except Exception as e:
        print(e)

        raise HTTPException(
            status_code=500,
            detail="知识库文档详情查询失败"
        )


@router.delete("/knowledge/documents/{filename}")
def delete_knowledge_document(
        filename: str,
        _admin=Depends(require_admin),
        _knowledge_lock: None = Depends(
            acquire_knowledge_build_lock
        )
):
    backup_path = None

    try:
        safe_filename = os.path.basename(
            filename
        )

        if (
            safe_filename != filename
            or not is_supported_document(safe_filename)
        ):
            raise HTTPException(
                status_code=400,
                detail="文件名不合法或格式不受支持"
            )

        file_path = os.path.join(
            KNOWLEDGE_PATH,
            safe_filename
        )

        if not os.path.isfile(file_path):
            raise HTTPException(
                status_code=404,
                detail="文档不存在"
            )

        document_count = len(
            [
                name
                for name in os.listdir(KNOWLEDGE_PATH)
                if (
                    is_supported_document(name)
                    and os.path.isfile(
                        os.path.join(KNOWLEDGE_PATH, name)
                    )
                )
            ]
        )

        if document_count <= 1:
            raise HTTPException(
                status_code=409,
                detail="不能删除知识库中的最后一个文档"
            )

        backup_path = file_path + ".delete_backup"

        if os.path.exists(backup_path):
            raise HTTPException(
                status_code=409,
                detail="该文档存在未完成的删除操作"
            )

        os.replace(
            file_path,
            backup_path
        )

        result = rebuild_knowledge_base(
            KNOWLEDGE_PATH,
            rag_runtime.index_path,
            rag_runtime.chunks_path,
            reload_callback=rag_runtime.reload
        )

        deleted_backup = backup_path
        backup_path = None

        try:
            os.remove(deleted_backup)
        except OSError as cleanup_error:
            print(cleanup_error)

        return {
            "message": "文档删除并重新建库成功",
            "filename": safe_filename,
            "document_count": result["document_count"],
            "chunk_count": result["chunk_count"],
            "vector_count": result["vector_count"]
        }

    except HTTPException:
        raise

    except Exception as e:
        if (
            backup_path is not None
            and os.path.exists(backup_path)
        ):
            original_path = backup_path.removesuffix(
                ".delete_backup"
            )

            os.replace(
                backup_path,
                original_path
            )

        print(e)

        if isinstance(e, KnowledgeBuildError):
            raise HTTPException(
                status_code=500,
                detail=e.to_detail()
            ) from e

        raise HTTPException(
            status_code=500,
            detail="文档删除或重新建库失败"
        )


@router.post("/knowledge/upload")
def upload_knowledge(
        request: KnowledgeUploadRequest,
        _admin=Depends(require_admin),
        _knowledge_lock: None = Depends(
            acquire_knowledge_build_lock
        )
):
    try:
        filename = os.path.basename(
            request.filename
        )

        if not filename.lower().endswith(
            ".txt"
        ):
            raise HTTPException(
                status_code=400,
                detail="目前只支持txt文件"
            )

        if not request.content.strip():
            raise HTTPException(
                status_code=400,
                detail="文档内容不能为空"
            )

        file_path = os.path.join(
            KNOWLEDGE_PATH,
            filename
        )

        if (
            os.path.exists(file_path)
            and not request.overwrite
        ):
            raise HTTPException(
                status_code=409,
                detail="文件已存在，如需覆盖请设置overwrite为true"
            )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(
                request.content
            )

        result = rebuild_knowledge_base(
            KNOWLEDGE_PATH,
            rag_runtime.index_path,
            rag_runtime.chunks_path,
            reload_callback=rag_runtime.reload
        )

        return {
            "message": "文档上传并重新建库成功",
            "filename": filename,
            "document_count": result["document_count"],
            "chunk_count": result["chunk_count"],
            "vector_count": result["vector_count"]
        }

    except HTTPException:
        raise

    except KnowledgeBuildError as error:
        print(error)

        raise HTTPException(
            status_code=500,
            detail=error.to_detail()
        ) from error

    except Exception as e:
        print(e)

        raise HTTPException(
            status_code=500,
            detail="文档上传或建库失败"
        )
