from app.database import database


class FakeCursor:
    def __init__(
        self,
        fetchone_result=None,
        fetchall_result=None,
        lastrowid=0
    ):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.lastrowid = lastrowid
        self.execute_calls = []
        self.closed = False

    def execute(self, sql, params):
        self.execute_calls.append(
            (" ".join(sql.split()), params)
        )

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.committed = False
        self.closed = False

    def cursor(self):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def use_fake_connection(
    monkeypatch,
    fetchone_result=None,
    fetchall_result=None,
    lastrowid=0
):
    cursor = FakeCursor(
        fetchone_result=fetchone_result,
        fetchall_result=fetchall_result,
        lastrowid=lastrowid
    )
    connection = FakeConnection(cursor)

    monkeypatch.setattr(
        database,
        "get_connection",
        lambda: connection
    )

    return connection, cursor


def test_create_user_inserts_hash_and_returns_id(
        monkeypatch
):
    connection, cursor = use_fake_connection(
        monkeypatch,
        lastrowid=12
    )

    user_id = database.create_user(
        "bill",
        "hashed-password"
    )

    sql, params = cursor.execute_calls[0]

    assert "INSERT INTO users" in sql
    assert "username" in sql
    assert "password_hash" in sql
    assert params == (
        "bill",
        "hashed-password"
    )
    assert user_id == 12
    assert connection.committed is True
    assert cursor.closed is True
    assert connection.closed is True


def test_get_conversations_uses_limit_and_offset(monkeypatch):
    connection, cursor = use_fake_connection(
        monkeypatch,
        fetchall_result=[]
    )

    result = database.get_conversations(
        12,
        chat_type="rag",
        limit=21,
        offset=40
    )
    sql, params = cursor.execute_calls[0]

    assert "LIMIT %s OFFSET %s" in sql
    assert params == (12, "rag", 21, 40)
    assert result == []
    assert connection.closed is True


def test_get_messages_uses_limit_and_offset(monkeypatch):
    connection, cursor = use_fake_connection(
        monkeypatch,
        fetchall_result=[]
    )

    result = database.get_messages(
        12,
        chat_type="rag",
        limit=21,
        conversation_id=88,
        offset=20
    )
    sql, params = cursor.execute_calls[0]

    assert "LIMIT %s OFFSET %s" in sql
    assert params == (12, "rag", 88, 21, 20)
    assert result == []
    assert connection.closed is True


def test_get_user_by_username_returns_password_hash(
        monkeypatch
):
    expected_user = {
        "id": 12,
        "username": "bill",
        "password_hash": "hashed-password"
    }
    connection, cursor = use_fake_connection(
        monkeypatch,
        fetchone_result=expected_user
    )

    user = database.get_user_by_username("bill")
    sql, params = cursor.execute_calls[0]

    assert "FROM users" in sql
    assert "WHERE username=%s" in sql
    assert "password_hash" in sql
    assert "role" in sql
    assert params == ("bill",)
    assert user == expected_user
    assert connection.committed is False
    assert cursor.closed is True
    assert connection.closed is True


def test_get_user_by_id_does_not_return_password_hash(
        monkeypatch
):
    expected_user = {
        "id": 12,
        "username": "bill"
    }
    connection, cursor = use_fake_connection(
        monkeypatch,
        fetchone_result=expected_user
    )

    user = database.get_user_by_id(12)
    sql, params = cursor.execute_calls[0]

    selected_columns = sql.split("FROM users")[0]

    assert "WHERE id=%s" in sql
    assert "password_hash" not in selected_columns
    assert "role" in selected_columns
    assert params == (12,)
    assert user == expected_user
    assert connection.committed is False
    assert cursor.closed is True
    assert connection.closed is True
