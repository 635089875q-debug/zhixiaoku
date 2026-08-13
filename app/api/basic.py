from fastapi import APIRouter

from app.config import settings


router = APIRouter()


@router.get("/")
def home():
    return {
        "message": "Hello FastAPI"
    }


@router.get("/search")
def search(keyword: str):
    return {
        "您搜索的是": keyword
    }


@router.get("/system/info")
def get_system_info():
    return {
        "llm_model": settings.LLM_MODEL
    }
