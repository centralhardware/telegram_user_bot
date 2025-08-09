SET allow_suspicious_low_cardinality_types = 1;


CREATE TABLE IF NOT EXISTS  chats_log (
    chat_id        Int64,
    chat_title     LowCardinality(String),
    chat_usernames Array(LowCardinality(String)),
    client_id      LowCardinality(UInt64),
    date_time      DateTime,
    first_name     Nullable(String),
    message        String,
    message_id     Int64,
    reply_to       Nullable(UInt64),
    second_name    Nullable(String),
    user_id        UInt64,
    username       Array(String)
) ENGINE = ReplacingMergeTree(date_time)
ORDER BY (chat_id, message_id);
