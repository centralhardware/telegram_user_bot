SET allow_suspicious_low_cardinality_types = 1;

CREATE TABLE IF NOT EXISTS  user_sessions (
    app_name       LowCardinality(String),
    app_version    LowCardinality(Nullable(String)),
    client_id      LowCardinality(UInt64),
    country        LowCardinality(String),
    date_active    DateTime,
    date_created   DateTime,
    device_model   LowCardinality(String),
    hash           Int64,
    ip             LowCardinality(Nullable(String)),
    platform       LowCardinality(String),
    region         LowCardinality(String),
    system_version LowCardinality(Nullable(String)),
    updated_at     DateTime
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY hash;
