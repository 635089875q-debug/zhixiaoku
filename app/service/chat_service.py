from app.database import add_message, get_messages
from app.ai import ask_llm

def chat(user_id, question):
    add_message(
        user_id,
        "user",
        question
    )
    history = get_messages(user_id)


    answer = ask_llm(history)

    add_message(
        user_id,
        "assistant",
        answer
    )
    return answer


