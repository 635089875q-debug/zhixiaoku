from pydantic import BaseModel, Field


class RAGChatRequest(BaseModel):
    question: str = Field(min_length=1)
    conversation_id: int | None = Field(
        default=None,
        gt=0
    )


class RAGConversationCreateRequest(BaseModel):
    title: str = Field(
        default="新对话",
        min_length=1,
        max_length=100
    )
