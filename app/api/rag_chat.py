from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_current_user
from app.database import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_conversations,
    get_messages,
)
from app.exceptions import ConversationNotFoundError
from app.schemas.rag import (
    RAGChatRequest,
    RAGConversationCreateRequest,
)
from app.service.rag_runtime import rag_runtime


router = APIRouter()


@router.post("/rag/chat")
def rag_chat(
    request: RAGChatRequest,
    current_user=Depends(get_current_user)
):
    try:
        user_id = current_user["id"]

        if request.conversation_id is None:
            result = rag_runtime.chat(
                request.question,
                user_id
            )
        else:
            result = rag_runtime.chat(
                request.question,
                user_id,
                request.conversation_id
            )

        return {
            "question": request.question,
            "answer": result["answer"],
            "sources": result["sources"],
            "conversation_id": request.conversation_id
        }

    except ConversationNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="会话不存在或不属于当前用户"
        )

    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500,
            detail="RAG服务异常"
        ) from error


@router.post(
    "/rag/conversations",
    status_code=201
)
def create_rag_conversation(
    request: RAGConversationCreateRequest,
    current_user=Depends(get_current_user)
):
    try:
        title = request.title.strip()

        if not title:
            raise HTTPException(
                status_code=400,
                detail="会话标题不能为空"
            )

        conversation_id = create_conversation(
            current_user["id"],
            title,
            chat_type="rag"
        )

        return {
            "id": conversation_id,
            "user_id": current_user["id"],
            "title": title,
            "chat_type": "rag"
        }

    except HTTPException:
        raise

    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500,
            detail="RAG会话创建失败"
        ) from error


@router.get("/rag/conversations")
def list_rag_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user)
):
    try:
        user_id = current_user["id"]
        offset = (page - 1) * page_size
        conversations = get_conversations(
            user_id,
            chat_type="rag",
            limit=page_size + 1,
            offset=offset
        )
        has_more = len(conversations) > page_size
        conversations = conversations[:page_size]

        return {
            "user_id": user_id,
            "conversation_count": len(conversations),
            "page": page,
            "page_size": page_size,
            "has_more": has_more,
            "conversations": conversations
        }

    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500,
            detail="RAG会话列表查询失败"
        ) from error


@router.delete("/rag/conversations/{conversation_id}")
def delete_rag_conversation(
    conversation_id: int,
    current_user=Depends(get_current_user)
):
    try:
        user_id = current_user["id"]
        conversation = get_conversation(
            conversation_id,
            user_id
        )

        if (
            conversation is None
            or conversation["chat_type"] != "rag"
        ):
            raise HTTPException(
                status_code=404,
                detail="会话不存在或不属于当前用户"
            )

        deleted_count = delete_conversation(
            conversation_id,
            user_id
        )

        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="会话不存在或已被删除"
            )

        return {
            "message": "会话删除成功",
            "conversation_id": conversation_id
        }

    except HTTPException:
        raise

    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500,
            detail="RAG会话删除失败"
        ) from error


@router.get(
    "/rag/conversations/{conversation_id}/messages"
)
def get_rag_conversation_messages(
    conversation_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user)
):
    try:
        user_id = current_user["id"]
        conversation = get_conversation(
            conversation_id,
            user_id
        )

        if (
            conversation is None
            or conversation["chat_type"] != "rag"
        ):
            raise HTTPException(
                status_code=404,
                detail="会话不存在或不属于当前用户"
            )

        offset = (page - 1) * page_size
        messages = get_messages(
            user_id,
            chat_type="rag",
            limit=page_size + 1,
            conversation_id=conversation_id,
            offset=offset
        )
        has_more = len(messages) > page_size

        if has_more:
            messages = messages[1:]

        return {
            "conversation": conversation,
            "page": page,
            "page_size": page_size,
            "has_more": has_more,
            "messages": messages
        }

    except HTTPException:
        raise

    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500,
            detail="RAG会话消息查询失败"
        ) from error


@router.get("/rag/history")
def get_rag_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user=Depends(get_current_user)
):
    try:
        user_id = current_user["id"]
        messages = get_messages(
            user_id,
            chat_type="rag",
            limit=limit
        )

        return {
            "user_id": user_id,
            "chat_type": "rag",
            "messages": messages
        }

    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500,
            detail="RAG历史记录查询失败"
        ) from error
