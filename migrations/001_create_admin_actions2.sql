CREATE TABLE IF NOT EXISTS admin_actions2 (
    event_id       UInt64,
    chat_id        UInt64,
    action_type    LowCardinality(String),
    user_id        UInt64,
    date           DateTime,
    message        String,
    usernames      Array(String),
    chat_usernames Array(LowCardinality(String)),
    chat_title     LowCardinality(String),
    user_title     String
) ENGINE = ReplacingMergeTree
ORDER BY (chat_id, event_id);
