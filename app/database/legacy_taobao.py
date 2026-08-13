import pymysql

from app.config import settings


conn = pymysql.connect(
    host=settings.MYSQL_HOST,
    port=settings.MYSQL_PORT,
    user=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    database=settings.MYSQL_TAOBAO_DATABASE,
    charset='utf8mb4'
)
cursor = conn.cursor(pymysql.cursors.DictCursor)


def get_user_behaviour_count(user_id):
    sql = """
    SELECT COUNT(*) AS behavior_count
    FROM user_behaviour 
    WHERE user_id=%s
    """

    cursor.execute(sql, (user_id,))
    result = cursor.fetchone()

    return result["behavior_count"]


def get_user_behaviours(user_id,page,size):
    sql = """
    SELECT item_id,category_id,behavior_type,datetimes
    FROM user_behaviour 
    WHERE user_id=%s
    LIMIT %s,%s
    """
    offset = (page - 1) * size
    cursor.execute(sql, (user_id,offset,size))
    results = cursor.fetchall()

    return results

def add_chat_history(question,answer):
    sql = """
    INSERT INTO chat_history(question,answer)
    VALUES(%s,%s)
    """

    cursor.execute(sql, (question,answer))
    conn.commit()

    return cursor.lastrowid

def update_chat_history(chat_id,answer):
    sql = """
    UPDATE chat_history
    SET answer=%s
    WHERE id=%s
    """
    cursor.execute(sql, (answer,chat_id))
    conn.commit()
    return cursor.rowcount

def delete_chat_history(chat_id):
    sql="""
    DELETE FROM chat_history
    WHERE id=%s
    """
    cursor.execute(sql, (chat_id,))
    conn.commit()
    return cursor.rowcount
