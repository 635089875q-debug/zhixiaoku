import os
from dotenv import load_dotenv


load_dotenv()


class Settings:

    SILICONFLOW_API_KEY = os.getenv(
        "SILICONFLOW_API_KEY"
    )

    LLM_MODEL = os.getenv(
        "LLM_MODEL"
    )

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL"
    )
    
    BASE_URL = os.getenv(
        "BASE_URL"
    )

    MYSQL_HOST = os.getenv(
        "MYSQL_HOST",
        "localhost"
    )

    MYSQL_PORT = int(os.getenv(
        "MYSQL_PORT",
        "3306"
    ))

    MYSQL_USER = os.getenv(
        "MYSQL_USER",
        "root"
    )

    MYSQL_PASSWORD = os.getenv(
        "MYSQL_PASSWORD"
    )

    MYSQL_AI_DATABASE = os.getenv(
        "MYSQL_AI_DATABASE",
        "ai_chat"
    )

    MYSQL_TAOBAO_DATABASE = os.getenv(
        "MYSQL_TAOBAO_DATABASE",
        "taobao"
    )

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY"
    )

    JWT_ALGORITHM = os.getenv(
        "JWT_ALGORITHM",
        "HS256"
    )

    JWT_EXPIRE_MINUTES = int(os.getenv(
        "JWT_EXPIRE_MINUTES",
        "120"
    ))

    SYSTEM_PROMPT = f"""
    你是一名专业的AI助手。
    
    你的名字叫{os.getenv("SYSTEM_NAME")}。
    
    用户会话历史会由系统保存，
    并在后续对话中提供给你。
    
    你可以根据提供的历史消息理解上下文。
    
    用户名字如果出现在历史记录中，
    可以正常使用。
    
    不要声称自己拥有不存在的能力。
    不要说“不会保存信息”，
    因为聊天历史由系统管理。
    """


settings = Settings()
