import pymysql

from app.config import settings


def get_connection():
    conn = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_AI_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn


def add_message(
    user_id,
    role,
    content,
    chat_type="normal",
    conversation_id=None
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if conversation_id is None:
            sql = """
            INSERT INTO `messages` (
                user_id,
                role,
                content,
                chat_type
            )
            VALUES (%s, %s, %s, %s)
            """
            params = (
                user_id,
                role,
                content,
                chat_type
            )
        else:
            sql = """
            INSERT INTO `messages` (
                user_id,
                conversation_id,
                role,
                content,
                chat_type
            )
            VALUES (%s, %s, %s, %s, %s)
            """
            params = (
                user_id,
                conversation_id,
                role,
                content,
                chat_type
            )

        cursor.execute(
            sql,
            params
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_messages(
    user_id,
    chat_type="normal",
    limit=20,
    conversation_id=None,
    offset=0
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if conversation_id is None:
            sql = """
            SELECT role,content
            FROM(
                SELECT id,role,content
                FROM messages
                WHERE user_id=%s
                AND chat_type=%s
                ORDER BY id DESC
                LIMIT %s
                OFFSET %s
            ) AS t
            ORDER BY id
            """
            params = (
                user_id,
                chat_type,
                limit,
                offset
            )
        else:
            sql = """
            SELECT role,content
            FROM(
                SELECT id,role,content
                FROM messages
                WHERE user_id=%s
                AND chat_type=%s
                AND conversation_id=%s
                ORDER BY id DESC
                LIMIT %s
                OFFSET %s
            ) AS t
            ORDER BY id
            """
            params = (
                user_id,
                chat_type,
                conversation_id,
                limit,
                offset
            )

        cursor.execute(
            sql,
            params
        )
        result = cursor.fetchall()
        return result
    finally:
        cursor.close()
        conn.close()


def create_conversation(
    user_id,
    title="新对话",
    chat_type="rag"
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
        INSERT INTO conversations (
            user_id,
            title,
            chat_type
        )
        VALUES (%s, %s, %s)
        """
        cursor.execute(
            sql,
            (
                user_id,
                title,
                chat_type
            )
        )
        conversation_id = cursor.lastrowid
        conn.commit()
        return conversation_id
    finally:
        cursor.close()
        conn.close()


def get_conversation(
    conversation_id,
    user_id
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT
            id,
            user_id,
            title,
            chat_type,
            created_at,
            updated_at
        FROM conversations
        WHERE id=%s
        AND user_id=%s
        """
        cursor.execute(
            sql,
            (
                conversation_id,
                user_id
            )
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_conversations(
    user_id,
    chat_type="rag",
    limit=50,
    offset=0
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT
            id,
            user_id,
            title,
            chat_type,
            created_at,
            updated_at
        FROM conversations
        WHERE user_id=%s
        AND chat_type=%s
        ORDER BY updated_at DESC, id DESC
        LIMIT %s
        OFFSET %s
        """
        cursor.execute(
            sql,
            (
                user_id,
                chat_type,
                limit,
                offset
            )
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def update_conversation_title(
    conversation_id,
    user_id,
    title
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
        UPDATE conversations
        SET title=%s
        WHERE id=%s
        AND user_id=%s
        """
        cursor.execute(
            sql,
            (
                title,
                conversation_id,
                user_id
            )
        )
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def touch_conversation(
    conversation_id,
    user_id
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
        UPDATE conversations
        SET updated_at=CURRENT_TIMESTAMP
        WHERE id=%s
        AND user_id=%s
        """
        cursor.execute(
            sql,
            (
                conversation_id,
                user_id
            )
        )
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def delete_conversation(
    conversation_id,
    user_id
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
        DELETE FROM conversations
        WHERE id=%s
        AND user_id=%s
        """
        cursor.execute(
            sql,
            (
                conversation_id,
                user_id
            )
        )
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def create_user(
    username,
    password_hash
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
        INSERT INTO users (
            username,
            password_hash
        )
        VALUES (%s, %s)
        """
        cursor.execute(
            sql,
            (
                username,
                password_hash
            )
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    finally:
        cursor.close()
        conn.close()


def get_user_by_username(username):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT
            id,
            username,
            password_hash,
            role,
            created_at,
            updated_at
        FROM users
        WHERE username=%s
        """
        cursor.execute(
            sql,
            (username,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT
            id,
            username,
            role,
            created_at,
            updated_at
        FROM users
        WHERE id=%s
        """
        cursor.execute(
            sql,
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
