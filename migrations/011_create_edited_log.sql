SET allow_suspicious_low_cardinality_types = 1;

CREATE TABLE IF NOT EXISTS  edited_log (
    date_time  DateTime,
    chat_id    Int64,
    message_id Int64,
    message    String,
    diff       String,
    client_id  LowCardinality(UInt64)
) ENGINE = ReplacingMergeTree(date_time)
ORDER BY (chat_id, message_id);
