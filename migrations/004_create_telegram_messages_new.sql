SET allow_suspicious_low_cardinality_types = 1;

CREATE TABLE IF NOT EXISTS  telegram_messages_new (
    admins2    Array(LowCardinality(String)),
    client_id  LowCardinality(UInt64),
    date_time  DateTime,
    id         Int64,
    message    String,
    message_id UInt64,
    raw        String,
    reply_to   UInt64,
    title      LowCardinality(String),
    usernames  Array(LowCardinality(String))
) ENGINE = MergeTree
ORDER BY date_time;
