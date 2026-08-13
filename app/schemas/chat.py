from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatUpdateRequest(BaseModel):
    answer: str
