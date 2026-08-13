from app.database import (
    add_message,
    get_conversation,
    get_messages,
    touch_conversation,
    update_conversation_title,
)
from app.exceptions import ConversationNotFoundError


class RAGService:
    TOP_K = 3
    HISTORY_LIMIT = 10
    RETRIEVAL_HISTORY_USER_LIMIT = 3

    def __init__(
        self,
        retriever,
        embedding,
        generator
    ):
        self.embedding = embedding
        self.retriever = retriever
        self.generator = generator

    def chat(
        self,
        query,
        user_id=None,
        conversation_id=None
    ):
        history = []
        conversation = None

        if conversation_id is not None:
            if user_id is None:
                raise ConversationNotFoundError()

            conversation = get_conversation(
                conversation_id,
                user_id
            )

            if (
                conversation is None
                or conversation["chat_type"] != "rag"
            ):
                raise ConversationNotFoundError()

            history = get_messages(
                user_id,
                chat_type="rag",
                limit=self.HISTORY_LIMIT,
                conversation_id=conversation_id
            )

        if user_id is not None:
            add_message(
                user_id,
                "user",
                query,
                chat_type="rag",
                conversation_id=conversation_id
            )

        if (
            conversation is not None
            and conversation["title"] == "新对话"
        ):
            title = query.strip()[:30] or "新对话"
            update_conversation_title(
                conversation_id,
                user_id,
                title
            )

        recent_user_questions = [
            message["content"]
            for message in history
            if message["role"] == "user"
        ][-self.RETRIEVAL_HISTORY_USER_LIMIT:]

        retrieval_query = "\n".join(
            recent_user_questions + [query]
        )

        query_vector = self.embedding(
            retrieval_query
        )

        contexts = self.retriever.retrieve(
            query_vector,
            top_k=self.TOP_K
        )

        if not contexts:
            answer = "知识库没有相关知识"
            self._save_assistant_message(
                user_id,
                conversation_id,
                answer
            )
            return {
                "answer": answer,
                "sources": []
            }

        context = "\n".join(
            document["content"]
            for document in contexts
        )

        answer = self.generator(
            query,
            context,
            history=history
        )

        self._save_assistant_message(
            user_id,
            conversation_id,
            answer
        )

        sources = [
            {
                "source": document["source"],
                "chunk_id": document["chunk_id"],
                "page_number": document.get("page_number"),
                "score": round(document["score"], 4),
                "content": document["content"]
            }
            for document in contexts
        ]

        return {
            "answer": answer,
            "sources": sources
        }

    @staticmethod
    def _save_assistant_message(
        user_id,
        conversation_id,
        answer
    ):
        if user_id is None:
            return

        add_message(
            user_id,
            "assistant",
            answer,
            chat_type="rag",
            conversation_id=conversation_id
        )

        if conversation_id is not None:
            touch_conversation(
                conversation_id,
                user_id
            )
