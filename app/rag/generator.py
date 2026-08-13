from openai import OpenAI

from app.config import settings


client = OpenAI(
    api_key=settings.SILICONFLOW_API_KEY,
    base_url=settings.BASE_URL
)


def format_history(history):
    role_names = {
        "user": "用户",
        "assistant": "助手"
    }

    return "\n".join(
        f"{role_names.get(message['role'], message['role'])}："
        f"{message['content']}"
        for message in history
    )


def generate(query, context, history=None):
    history = history or []
    history_text = format_history(
        history
    ) or "无"

    messages = [
        {
            "role": "system",
            "content": """
            你是一名知识库问答助手。
            请根据当前提供的参考资料回答用户问题。

            要求：
            1. 事实信息只能来自当前参考资料。
            2. 历史对话只用于理解代词、追问和上下文，不可作为事实来源。
            3. 如果参考资料中没有答案，明确回答“知识库中没有相关信息”。
            4. 不要自行编造信息。
            """
        },
        {
            "role": "user",
            "content": f"""
            最近历史对话：
            {history_text}

            当前参考资料：
            {context}

            当前用户问题：
            {query}
            """
        }
    ]

    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=messages
    )

    return response.choices[0].message.content
