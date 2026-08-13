import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("SILICONFLOW_API_KEY")
client = OpenAI(
    api_key=api_key,
    base_url="https://api.siliconflow.cn/v1"
)


def ask_ai(question):
    response = client.chat.completions.create(
        model='deepseek-ai/DeepSeek-V3',
        messages=[
            {
                "role": "user",
                "content": question
            }
        ]
    )
    return response.choices[0].message.content
