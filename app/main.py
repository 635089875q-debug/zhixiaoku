from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.paths import STATIC_PATH
from app.api.auth import router as auth_router
from app.api.basic import router as basic_router
from app.api.chat import router as chat_router
from app.api.legacy import router as legacy_router
from app.api.rag_chat import router as rag_chat_router
from app.api.knowledge_base import router as knowledge_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(basic_router)
app.include_router(chat_router)
app.include_router(rag_chat_router)
app.include_router(knowledge_router)
app.include_router(legacy_router)

app.mount(
    "/ui",
    StaticFiles(
        directory=str(STATIC_PATH),
        html=True
    ),
    name="ui"
)
