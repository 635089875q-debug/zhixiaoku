from openai import OpenAI
from app.config import settings
import numpy as np


client = OpenAI(
    api_key=settings.SILICONFLOW_API_KEY,
    base_url=settings.BASE_URL
)


def get_embedding(texts):

    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts
    )

    vectors = [
        item.embedding
        for item in response.data
    ]

    return vectors

def get_query_embedding(query):
    vector = get_embedding([query])[0]
    return np.array(
        vector,
        dtype=np.float32
    ).reshape(1,-1)