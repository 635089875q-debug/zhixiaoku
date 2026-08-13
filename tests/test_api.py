from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import chat as chat_api
from app.api import knowledge_base
from app.api import rag_chat as rag_chat_api
from app.dependencies import get_current_user
from app.exceptions import AIServiceError
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticated_user():
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "username": "test_user",
        "role": "admin",
    }
    yield
    app.dependency_overrides.clear()


def use_role(role):
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 2,
        "username": f"{role}_user",
        "role": role,
    }


@pytest.fixture
def isolated_knowledge_base(
        tmp_path,
        monkeypatch
):
    monkeypatch.setattr(
        knowledge_base,
        "KNOWLEDGE_PATH",
        str(tmp_path)
    )

    def fake_rebuild(
            folder,
            index_path,
            chunks_path,
            reload_callback=None
    ):
        documents = [
            path
            for path in Path(folder).iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                in knowledge_base.SUPPORTED_DOCUMENT_EXTENSIONS
            )
        ]

        return {
            "document_count": len(documents),
            "chunk_count": len(documents),
            "vector_count": len(documents)
        }

    monkeypatch.setattr(
        knowledge_base,
        "rebuild_knowledge_base",
        fake_rebuild
    )

    return tmp_path

def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Hello FastAPI"
    }

def test_list_documents():
    response = client.get(
        "/knowledge/documents"
    )

    assert response.status_code == 200

    data = response.json()

    assert "document_count" in data
    assert "documents" in data
    assert isinstance(
        data["documents"],
        list
    )
    assert data["document_count"] == len(
        data["documents"]
    )


def test_knowledge_documents_require_authentication():
    app.dependency_overrides.clear()

    response = client.get("/knowledge/documents")

    assert response.status_code == 401


def test_regular_user_cannot_rebuild_knowledge_base():
    use_role("user")

    response = client.post("/knowledge/rebuild")

    assert response.status_code == 403
    assert response.json()["detail"] == "需要管理员权限"


def test_search_accepts_keyword():
    response = client.get(
        "/search",
        params={"keyword": "RAG"}
    )

    assert response.status_code == 200


def test_search_requires_keyword():
    response = client.get("/search")

    assert response.status_code == 422


def test_system_info_returns_model_name():
    response = client.get("/system/info")

    assert response.status_code == 200
    assert "llm_model" in response.json()
    assert isinstance(
        response.json()["llm_model"],
        str
    )


def test_get_document_rejects_unsupported_format():
    response = client.get(
        "/knowledge/documents/readme.md"
    )

    assert response.status_code == 400


def test_get_missing_document_returns_404():
    response = client.get(
        "/knowledge/documents/"
        "definitely_missing_document_20260811.txt"
    )

    assert response.status_code == 404


def test_upload_file_rejects_unsupported_format():
    response = client.post(
        "/knowledge/upload-file",
        files={
            "file": (
                "readme.md",
                b"unsupported content",
                "text/markdown"
            )
        },
        data={"overwrite": "false"}
    )

    assert response.status_code == 400


def test_upload_file_rejects_empty_file():
    response = client.post(
        "/knowledge/upload-file",
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain"
            )
        },
        data={"overwrite": "false"}
    )

    assert response.status_code == 400


def test_chat_requires_question():
    response = client.post(
        "/chat",
        json={}
    )

    assert response.status_code == 422


def test_rag_chat_requires_question():
    response = client.post(
        "/rag/chat",
        json={}
    )

    assert response.status_code == 422


def test_list_documents_uses_isolated_directory(
        isolated_knowledge_base
):
    (isolated_knowledge_base / "a.txt").write_text(
        "文档A",
        encoding="utf-8"
    )
    (isolated_knowledge_base / "b.docx").write_bytes(
        b"test"
    )
    (isolated_knowledge_base / "ignored.md").write_text(
        "忽略",
        encoding="utf-8"
    )

    response = client.get(
        "/knowledge/documents"
    )

    assert response.status_code == 200
    assert response.json()["document_count"] == 2
    assert [
        document["filename"]
        for document in response.json()["documents"]
    ] == ["a.txt", "b.docx"]


def test_upload_text_document_without_real_rebuild(
        isolated_knowledge_base
):
    response = client.post(
        "/knowledge/upload",
        json={
            "filename": "new.txt",
            "content": "临时知识库内容",
            "overwrite": False
        }
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "new.txt"
    assert (
        isolated_knowledge_base / "new.txt"
    ).read_text(encoding="utf-8") == "临时知识库内容"


def test_upload_file_without_real_rebuild(
        isolated_knowledge_base
):
    response = client.post(
        "/knowledge/upload-file",
        files={
            "file": (
                "upload.txt",
                "上传文件内容".encode("utf-8"),
                "text/plain"
            )
        },
        data={"overwrite": "false"}
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "upload.txt"
    assert (
        isolated_knowledge_base / "upload.txt"
    ).read_text(encoding="utf-8") == "上传文件内容"


def test_get_document_returns_content_and_chunks(
        isolated_knowledge_base,
        monkeypatch
):
    file_path = (
        isolated_knowledge_base / "detail.txt"
    )
    file_path.write_text(
        "文档详情",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        knowledge_base,
        "load_chunks",
        lambda path: [
            {
                "source": "detail.txt",
                "chunk_id": 0,
                "content": "文档详情"
            }
        ]
    )

    response = client.get(
        "/knowledge/documents/detail.txt"
    )

    assert response.status_code == 200
    assert response.json()["content"] == "文档详情"
    assert response.json()["chunk_count"] == 1
    assert response.json()["chunks"][0]["chunk_id"] == 0


def test_delete_document_without_real_rebuild(
        isolated_knowledge_base
):
    target = isolated_knowledge_base / "delete.txt"
    target.write_text(
        "待删除",
        encoding="utf-8"
    )
    (isolated_knowledge_base / "keep.txt").write_text(
        "保留",
        encoding="utf-8"
    )

    response = client.delete(
        "/knowledge/documents/delete.txt"
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "delete.txt"
    assert not target.exists()
    assert (
        isolated_knowledge_base / "keep.txt"
    ).exists()


def test_delete_last_document_is_rejected(
        isolated_knowledge_base
):
    target = isolated_knowledge_base / "last.txt"
    target.write_text(
        "最后一个文档",
        encoding="utf-8"
    )

    response = client.delete(
        "/knowledge/documents/last.txt"
    )

    assert response.status_code == 409
    assert target.exists()


def test_chat_returns_mocked_answer(monkeypatch):
    calls = []
    monkeypatch.setattr(
        chat_api,
        "chat_service",
        lambda user_id, question: (
            calls.append((user_id, question))
            or "模拟回答"
        )
    )

    response = client.post(
        "/chat",
        json={
            "user_id": 999,
            "question": "你好"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": "你好",
        "answer": "模拟回答"
    }
    assert calls == [(1, "你好")]


def test_chat_requires_authentication():
    app.dependency_overrides.clear()

    response = client.post(
        "/chat",
        json={"question": "你好"}
    )

    assert response.status_code == 401


def test_chat_converts_ai_error_to_503(monkeypatch):
    def raise_ai_error(user_id, question):
        raise AIServiceError()

    monkeypatch.setattr(
        chat_api,
        "chat_service",
        raise_ai_error
    )

    response = client.post(
        "/chat",
        json={
            "question": "你好"
        }
    )

    assert response.status_code == 503


def test_rag_chat_returns_mocked_sources(monkeypatch):
    monkeypatch.setattr(
        rag_chat_api.rag_runtime,
        "chat",
        lambda question, user_id: {
            "answer": "深圳大学位于南山区",
            "sources": [
                {
                    "source": "szu.txt",
                    "chunk_id": 0,
                    "score": 0.8,
                    "content": "深圳大学位于南山区"
                }
            ]
        }
    )

    response = client.post(
        "/rag/chat",
        json={
            "question": "深圳大学在哪里"
        }
    )

    assert response.status_code == 200
    assert response.json()["answer"] == (
        "深圳大学位于南山区"
    )
    assert response.json()["sources"][0][
        "source"
    ] == "szu.txt"


def test_rag_history_returns_mocked_messages(
        monkeypatch
):
    monkeypatch.setattr(
        rag_chat_api,
        "get_messages",
        lambda user_id, chat_type, limit: [
            {
                "role": "user",
                "content": "深圳大学在哪里"
            },
            {
                "role": "assistant",
                "content": "深圳大学位于南山区"
            }
        ]
    )

    response = client.get(
        "/rag/history",
        params={"limit": 10}
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == 1
    assert response.json()["chat_type"] == "rag"
    assert len(response.json()["messages"]) == 2


def test_rebuild_knowledge_base_without_embedding(
        isolated_knowledge_base
):
    (isolated_knowledge_base / "test.txt").write_text(
        "临时内容",
        encoding="utf-8"
    )

    response = client.post(
        "/knowledge/rebuild"
    )

    assert response.status_code == 200
    assert response.json()["document_count"] == 1
    assert response.json()["chunk_count"] == 1
    assert response.json()["vector_count"] == 1

