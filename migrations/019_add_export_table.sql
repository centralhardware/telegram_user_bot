CREATE TABLE export
(
    date_time   DateTime,
    message     String,
    title       LowCardinality(String),
    message_id  Int64,
    reply_to    Int64 DEFAULT 0,
    chat_id     Int64
)
    ENGINE = ReplacingMergeTree()
        ORDER BY (chat_id, message_id);
