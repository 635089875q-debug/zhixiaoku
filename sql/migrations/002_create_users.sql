-- 用于已有 ai_chat 数据库增加用户账号表。
-- 该脚本可以重复执行，不会删除或覆盖现有数据。
-- 暂不为 messages 和 conversations 增加 users 外键，
-- 以保留当前 user_id=0 的历史聊天记录。

USE ai_chat;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE INDEX uk_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
