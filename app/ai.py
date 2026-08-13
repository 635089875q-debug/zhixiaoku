from openai import OpenAI, RateLimitError
from app.exceptions import AIServiceError
from app.config import settings

client = OpenAI(
    api_key=settings.SILICONFLOW_API_KEY,
    base_url=settings.BASE_URL
)


def ask_llm(history):
    try:
        messages = [
            {
                "role": "system",
                "content": settings.SYSTEM_PROMPT
            }
        ]
        messages.extend(history)
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages
        )
        return response.choices[0].message.content

    except RateLimitError as e:
        print(e)
        raise AIServiceError('AI服务器繁忙')

    except Exception as e:
        print(e)
        raise AIServiceError('AI服务异常') from e
