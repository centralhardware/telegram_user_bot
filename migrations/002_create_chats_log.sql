SET allow_suspicious_low_cardinality_types = 1;


CREATE TABLE IF NOT EXISTS  chats_log (
    date_time      DateTime,
    chat_title     LowCardinality(String),
    chat_id        Int64,
    username       Array(String),
    first_name     Nullable(String),
    second_name    Nullable(String),
    user_id        UInt64,
    message_id     Int64,
    message        String,
    chat_usernames Array(LowCardinality(String)),
    reply_to       Nullable(UInt64),
    client_id      LowCardinality(UInt64)
) ENGINE = ReplacingMergeTree(date_time)
ORDER BY (chat_id, message_id);
