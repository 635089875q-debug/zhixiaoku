from fastapi import APIRouter

from app.schemas.chat import ChatUpdateRequest
from app.database.legacy_taobao import (
    delete_chat_history,
    get_user_behaviour_count,
    get_user_behaviours,
    update_chat_history,
)


router = APIRouter()


@router.get("/user/{user_id}")
def get_user(user_id: int):
    count = get_user_behaviour_count(user_id)
    return {
        "user_id": user_id,
        "name": "Bill",
        "behavior_count": count
    }


@router.get("/user/{user_id}/behaviours")
def get_behaviours(
    user_id: int,
    page: int = 1,
    size: int = 10
):
    results = get_user_behaviours(user_id, page, size)
    return {
        "user_id": user_id,
        "page": page,
        "size": size,
        "behaviors": results
    }


@router.get("/chat/history")
def history(page: int = 1, size: int = 20):
    return {
        "page": page,
        "size": size,
        "message": [
            "你好",
            "什么是rag？"
        ]
    }


@router.put("/chat/{chat_id}")
def update_chat(request: ChatUpdateRequest, chat_id: int):
    count = update_chat_history(chat_id, request.answer)
    return {
        "update_count": count,
        "message": "更新成功"
    }


@router.delete("/chat/{chat_id}")
def delete_chat(chat_id: int):
    count = delete_chat_history(chat_id)
    return {
        "delete_count": count,
        "message": "删除成功"
    }
