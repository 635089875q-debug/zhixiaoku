from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import rag_chat as rag_chat_api
from app.dependencies import get_current_user
from app.exceptions import ConversationNotFoundError
from app.main import app
from app.rag import generator as generator_module
from app.service import rag_service as rag_service_module
from app.service.rag_service import RAGService


client = TestClient(app)


@pytest.fixture(autouse=True)
def authenticated_user():
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "username": "test_user",
    }
    yield
    app.dependency_overrides.clear()


def use_user(user_id):
    app.dependency_overrides[get_current_user] = lambda: {
        "id": user_id,
        "username": f"user_{user_id}",
    }


class FakeRetriever:
    def __init__(self, contexts):
        self.contexts = contexts
        self.calls = []

    def retrieve(self, query_vector, top_k):
        self.calls.append(
            {
                "query_vector": query_vector,
                "top_k": top_k,
            }
        )
        return self.contexts


def make_context():
    return {
        "source": "project.txt",
        "chunk_id": 0,
        "score": 0.82,
        "content": "云桥计划的负责人是韩青。",
    }


def test_conversation_rejects_other_user_before_reading_messages(
        monkeypatch
):
    monkeypatch.setattr(
        rag_service_module,
        "get_conversation",
        lambda conversation_id, user_id: None,
    )

    def fail_if_called(*args, **kwargs):
        pytest.fail("无权访问会话时不应继续读取或写入消息")

    monkeypatch.setattr(
        rag_service_module,
        "get_messages",
        fail_if_called,
    )
    monkeypatch.setattr(
        rag_service_module,
        "add_message",
        fail_if_called,
    )

    service = RAGService(
        FakeRetriever([make_context()]),
        lambda query: [0.1],
        lambda query, context, history=None: "不会执行",
    )

    with pytest.raises(ConversationNotFoundError):
        service.chat(
            "负责人是谁",
            user_id=2,
            conversation_id=100,
        )


def test_conversation_history_is_scoped_and_passed_to_rag(
        monkeypatch
):
    history = [
        {"role": "user", "content": "第一问"},
        {"role": "assistant", "content": "第一答"},
        {"role": "user", "content": "第二问"},
        {"role": "assistant", "content": "第二答"},
        {"role": "user", "content": "第三问"},
        {"role": "user", "content": "第四问"},
    ]
    database_calls = []
    embedding_queries = []
    generator_calls = []

    def fake_get_conversation(conversation_id, user_id):
        database_calls.append(
            ("get_conversation", conversation_id, user_id)
        )
        return {
            "id": conversation_id,
            "user_id": user_id,
            "title": "已有会话",
            "chat_type": "rag",
        }

    def fake_get_messages(
            user_id,
            chat_type,
            limit,
            conversation_id=None
    ):
        database_calls.append(
            (
                "get_messages",
                user_id,
                chat_type,
                limit,
                conversation_id,
            )
        )
        return history

    def fake_add_message(
            user_id,
            role,
            content,
            chat_type,
            conversation_id=None
    ):
        database_calls.append(
            (
                "add_message",
                user_id,
                role,
                content,
                chat_type,
                conversation_id,
            )
        )

    def fake_embedding(query):
        embedding_queries.append(query)
        return [0.2, 0.3]

    def fake_generator(query, context, history=None):
        generator_calls.append(
            {
                "query": query,
                "context": context,
                "history": history,
            }
        )
        return "负责人是韩青"

    monkeypatch.setattr(
        rag_service_module,
        "get_conversation",
        fake_get_conversation,
    )
    monkeypatch.setattr(
        rag_service_module,
        "get_messages",
        fake_get_messages,
    )
    monkeypatch.setattr(
        rag_service_module,
        "add_message",
        fake_add_message,
    )
    monkeypatch.setattr(
        rag_service_module,
        "touch_conversation",
        lambda conversation_id, user_id: database_calls.append(
            ("touch_conversation", conversation_id, user_id)
        ),
    )

    retriever = FakeRetriever([make_context()])
    service = RAGService(
        retriever,
        fake_embedding,
        fake_generator,
    )

    result = service.chat(
        "他负责什么？",
        user_id=7,
        conversation_id=42,
    )

    assert (
        "get_conversation",
        42,
        7,
    ) in database_calls
    assert (
        "get_messages",
        7,
        "rag",
        service.HISTORY_LIMIT,
        42,
    ) in database_calls

    assert embedding_queries == [
        "第二问\n第三问\n第四问\n他负责什么？"
    ]
    assert retriever.calls == [
        {
            "query_vector": [0.2, 0.3],
            "top_k": service.TOP_K,
        }
    ]
    assert generator_calls == [
        {
            "query": "他负责什么？",
            "context": "云桥计划的负责人是韩青。",
            "history": history,
        }
    ]

    assert (
        "add_message",
        7,
        "user",
        "他负责什么？",
        "rag",
        42,
    ) in database_calls
    assert (
        "add_message",
        7,
        "assistant",
        "负责人是韩青",
        "rag",
        42,
    ) in database_calls
    assert (
        "touch_conversation",
        42,
        7,
    ) in database_calls
    assert result["answer"] == "负责人是韩青"


def test_generator_adds_history_to_prompt(monkeypatch):
    captured = {}

    def fake_create(model, messages):
        captured["model"] = model
        captured["messages"] = messages
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="根据资料回答"
                    )
                )
            ]
        )

    monkeypatch.setattr(
        generator_module.client.chat.completions,
        "create",
        fake_create,
    )

    answer = generator_module.generate(
        "他是谁？",
        "云桥计划的负责人是韩青。",
        history=[
            {"role": "user", "content": "云桥计划是什么？"},
            {"role": "assistant", "content": "这是一个知识库项目。"},
        ],
    )

    prompt = captured["messages"][1]["content"]

    assert "用户：云桥计划是什么？" in prompt
    assert "助手：这是一个知识库项目。" in prompt
    assert "云桥计划的负责人是韩青。" in prompt
    assert "他是谁？" in prompt
    assert answer == "根据资料回答"


def test_chat_without_conversation_id_keeps_legacy_behavior(
        monkeypatch
):
    saved_messages = []
    generator_histories = []

    def fail_if_called(*args, **kwargs):
        pytest.fail("旧调用不应查询 conversations 表")

    monkeypatch.setattr(
        rag_service_module,
        "get_conversation",
        fail_if_called,
    )
    monkeypatch.setattr(
        rag_service_module,
        "get_messages",
        fail_if_called,
    )
    monkeypatch.setattr(
        rag_service_module,
        "add_message",
        lambda user_id, role, content, chat_type, conversation_id=None:
        saved_messages.append(
            (
                user_id,
                role,
                content,
                chat_type,
                conversation_id,
            )
        ),
    )

    service = RAGService(
        FakeRetriever([make_context()]),
        lambda query: [0.1],
        lambda query, context, history=None: (
            generator_histories.append(history)
            or "兼容回答"
        ),
    )

    result = service.chat(
        "负责人是谁",
        user_id=9,
    )

    assert generator_histories == [[]]
    assert saved_messages == [
        (9, "user", "负责人是谁", "rag", None),
        (9, "assistant", "兼容回答", "rag", None),
    ]
    assert result["answer"] == "兼容回答"


def test_rag_chat_api_forwards_conversation_id(monkeypatch):
    use_user(3)
    calls = []

    def fake_chat(question, user_id, conversation_id):
        calls.append(
            (question, user_id, conversation_id)
        )
        return {
            "answer": "会话回答",
            "sources": [],
        }

    monkeypatch.setattr(
        rag_chat_api.rag_runtime,
        "chat",
        fake_chat,
    )

    response = client.post(
        "/rag/chat",
        json={
            "user_id": 999,
            "conversation_id": 88,
            "question": "继续上一问",
        },
    )

    assert response.status_code == 200
    assert calls == [("继续上一问", 3, 88)]
    assert response.json()["conversation_id"] == 88


def test_create_conversation_ignores_spoofed_user_id(
        monkeypatch
):
    use_user(21)
    calls = []

    monkeypatch.setattr(
        rag_chat_api,
        "create_conversation",
        lambda user_id, title, chat_type: (
            calls.append((user_id, title, chat_type))
            or 45
        ),
    )

    response = client.post(
        "/rag/conversations",
        json={
            "user_id": 999,
            "title": "认证会话",
        },
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == 21
    assert calls == [(21, "认证会话", "rag")]


def test_rag_chat_api_returns_404_for_foreign_conversation(
        monkeypatch
):
    use_user(4)
    def raise_not_found(*args, **kwargs):
        raise ConversationNotFoundError()

    monkeypatch.setattr(
        rag_chat_api.rag_runtime,
        "chat",
        raise_not_found,
    )

    response = client.post(
        "/rag/chat",
        json={
            "conversation_id": 88,
            "question": "尝试读取其他用户会话",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "会话不存在或不属于当前用户"
    )


def test_conversation_messages_endpoint_does_not_leak_foreign_data(
        monkeypatch
):
    use_user(4)
    monkeypatch.setattr(
        rag_chat_api,
        "get_conversation",
        lambda conversation_id, user_id: None,
    )

    def fail_if_called(*args, **kwargs):
        pytest.fail("会话校验失败后不应读取消息")

    monkeypatch.setattr(
        rag_chat_api,
        "get_messages",
        fail_if_called,
    )

    response = client.get(
        "/rag/conversations/88/messages",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "会话不存在或不属于当前用户"
    )


def test_delete_conversation_checks_owner_and_returns_deleted_id(
        monkeypatch
):
    use_user(7)
    delete_calls = []

    monkeypatch.setattr(
        rag_chat_api,
        "get_conversation",
        lambda conversation_id, user_id: {
            "id": conversation_id,
            "user_id": user_id,
            "title": "待删除会话",
            "chat_type": "rag",
        },
    )
    monkeypatch.setattr(
        rag_chat_api,
        "delete_conversation",
        lambda conversation_id, user_id: (
            delete_calls.append(
                (conversation_id, user_id)
            )
            or 1
        ),
    )

    response = client.delete(
        "/rag/conversations/23",
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "会话删除成功",
        "conversation_id": 23,
    }
    assert delete_calls == [(23, 7)]


def test_delete_conversation_does_not_delete_foreign_conversation(
        monkeypatch
):
    use_user(8)
    monkeypatch.setattr(
        rag_chat_api,
        "get_conversation",
        lambda conversation_id, user_id: None,
    )

    def fail_if_called(*args, **kwargs):
        pytest.fail("无权访问会话时不应执行删除")

    monkeypatch.setattr(
        rag_chat_api,
        "delete_conversation",
        fail_if_called,
    )

    response = client.delete(
        "/rag/conversations/23",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "会话不存在或不属于当前用户"
    )


def test_rag_chat_requires_authentication():
    app.dependency_overrides.clear()

    response = client.post(
        "/rag/chat",
        json={"question": "未登录提问"},
    )

    assert response.status_code == 401


def test_conversation_list_uses_authenticated_user(
        monkeypatch
):
    use_user(15)
    calls = []

    monkeypatch.setattr(
        rag_chat_api,
        "get_conversations",
        lambda user_id, chat_type, limit, offset: (
            calls.append((user_id, chat_type, limit, offset))
            or []
        ),
    )

    response = client.get(
        "/rag/conversations",
        params={"page": 2, "page_size": 10},
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == 15
    assert response.json()["page"] == 2
    assert response.json()["has_more"] is False
    assert calls == [(15, "rag", 11, 10)]


def test_conversation_list_reports_has_more(monkeypatch):
    use_user(15)
    conversations = [
        {
            "id": index,
            "user_id": 15,
            "title": f"会话 {index}",
            "chat_type": "rag",
        }
        for index in range(1, 4)
    ]

    monkeypatch.setattr(
        rag_chat_api,
        "get_conversations",
        lambda user_id, chat_type, limit, offset: conversations,
    )

    response = client.get(
        "/rag/conversations",
        params={"page": 1, "page_size": 2},
    )

    assert response.status_code == 200
    assert response.json()["has_more"] is True
    assert len(response.json()["conversations"]) == 2


def test_conversation_messages_are_paginated(monkeypatch):
    use_user(15)
    calls = []

    monkeypatch.setattr(
        rag_chat_api,
        "get_conversation",
        lambda conversation_id, user_id: {
            "id": conversation_id,
            "user_id": user_id,
            "title": "分页会话",
            "chat_type": "rag",
        },
    )
    monkeypatch.setattr(
        rag_chat_api,
        "get_messages",
        lambda user_id, chat_type, limit, conversation_id, offset: (
            calls.append(
                (user_id, chat_type, limit, conversation_id, offset)
            )
            or [
                {"role": "user", "content": "额外旧消息"},
                {"role": "assistant", "content": "消息一"},
                {"role": "user", "content": "消息二"},
            ]
        ),
    )

    response = client.get(
        "/rag/conversations/88/messages",
        params={"page": 2, "page_size": 2},
    )

    assert response.status_code == 200
    assert response.json()["has_more"] is True
    assert response.json()["messages"] == [
        {"role": "assistant", "content": "消息一"},
        {"role": "user", "content": "消息二"},
    ]
    assert calls == [(15, "rag", 3, 88, 2)]
