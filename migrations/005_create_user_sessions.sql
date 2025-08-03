-- auto-generated definition
CREATE TABLE user_sessions (
    hash           Int64,
    device_model   LowCardinality(String),
    platform       LowCardinality(String),
    system_version LowCardinality(Nullable(String)),
    app_name       LowCardinality(String),
    app_version    LowCardinality(Nullable(String)),
    ip             LowCardinality(Nullable(String)),
    country        LowCardinality(String),
    region         LowCardinality(String),
    date_created   DateTime,
    date_active    DateTime,
    updated_at     DateTime,
    client_id      LowCardinality(UInt64)
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY hash
SETTINGS index_granularity = 8192;
