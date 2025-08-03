CREATE TABLE IF NOT EXISTS  deleted_log (
    date_time  DateTime,
    chat_id    Int64,
    message_id Int64,
    client_id  LowCardinality(UInt64)
) ENGINE = ReplacingMergeTree(date_time)
ORDER BY (chat_id, message_id);
