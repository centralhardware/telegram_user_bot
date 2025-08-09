SET allow_suspicious_low_cardinality_types = 1;

CREATE TABLE IF NOT EXISTS  deleted_log (
    chat_id    Int64,
    client_id  LowCardinality(UInt64),
    date_time  DateTime,
    message_id Int64
) ENGINE = ReplacingMergeTree(date_time)
ORDER BY (chat_id, message_id);
