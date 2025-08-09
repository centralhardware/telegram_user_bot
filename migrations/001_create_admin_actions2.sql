CREATE TABLE IF NOT EXISTS admin_actions2 (
    action_type    LowCardinality(String),
    chat_id        UInt64,
    chat_title     LowCardinality(String),
    chat_usernames Array(LowCardinality(String)),
    date           DateTime,
    event_id       UInt64,
    message        String,
    user_id        UInt64,
    user_title     String,
    usernames      Array(String)
) ENGINE = ReplacingMergeTree
ORDER BY (chat_id, event_id);
