from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.exceptions import AIServiceError
from app.schemas.chat import ChatRequest
from app.service.chat_service import chat as chat_service

router = APIRouter()


@router.post("/chat")
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user)
):
    try:
        answer = chat_service(
            current_user["id"],
            request.question
        )
    except AIServiceError:
        raise HTTPException(
            status_code=503,
            detail='AI服务器繁忙，请稍后重试'
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="服务器内部错误"
        )
    return {
        "question": request.question,
        "answer": answer,
    }
