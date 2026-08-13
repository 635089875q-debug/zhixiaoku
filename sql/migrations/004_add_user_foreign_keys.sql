-- 一次性升级脚本：保留旧数据，将 user_id=0 归属给 bill，随后增加用户外键。
-- 执行前请确认 users 表中存在 username='bill'。

USE ai_chat;

SET @bill_user_id = (
    SELECT id
    FROM users
    WHERE username = 'bill'
    LIMIT 1
);

UPDATE conversations AS conversation
LEFT JOIN users AS user
    ON user.id = conversation.user_id
SET conversation.user_id = @bill_user_id
WHERE user.id IS NULL;

UPDATE messages AS message
LEFT JOIN users AS user
    ON user.id = message.user_id
SET message.user_id = @bill_user_id
WHERE user.id IS NULL;

UPDATE messages AS message
INNER JOIN conversations AS conversation
    ON conversation.id = message.conversation_id
SET message.user_id = conversation.user_id
WHERE message.user_id <> conversation.user_id;

ALTER TABLE messages
    ADD INDEX idx_messages_user_type_conversation_id (
        user_id,
        chat_type,
        conversation_id,
        id
    );

ALTER TABLE conversations
    ADD CONSTRAINT fk_conversations_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE RESTRICT;

ALTER TABLE messages
    ADD CONSTRAINT fk_messages_user
        FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE RESTRICT;
