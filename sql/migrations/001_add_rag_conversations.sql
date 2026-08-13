-- 仅用于已有 ai_chat 数据库的一次性升级。
-- 旧消息会保留，conversation_id 默认为 NULL，不会被删除。

USE ai_chat;

CREATE TABLE IF NOT EXISTS conversations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(100) NOT NULL DEFAULT '新对话',
    chat_type VARCHAR(20) NOT NULL DEFAULT 'rag',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_conversations_user_type_updated (
        user_id,
        chat_type,
        updated_at
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE messages
    ADD COLUMN conversation_id BIGINT UNSIGNED NULL
        AFTER user_id,
    ADD INDEX idx_messages_conversation_id (
        conversation_id,
        id
    ),
    ADD CONSTRAINT fk_messages_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations (id)
        ON DELETE CASCADE;
