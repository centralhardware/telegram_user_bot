CREATE TABLE IF NOT EXISTS  telegram_messages_new (
    date_time  DateTime,
    message    String,
    title      LowCardinality(String),
    id         Int64,
    admins2    Array(LowCardinality(String)),
    usernames  Array(LowCardinality(String)),
    message_id UInt64,
    reply_to   UInt64,
    raw        String,
    client_id  LowCardinality(UInt64)
) ENGINE = MergeTree
ORDER BY date_time;
