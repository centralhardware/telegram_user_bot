SET allow_suspicious_low_cardinality_types = 1;

CREATE TABLE IF NOT EXISTS client_sessions (
    name LowCardinality(String),
    dc_id UInt32,
    server_address String,
    port UInt32,
    auth_key     Nullable(String) CODEC(ZSTD(3)),   -- сырые байты (BLOB)
    takeout_id Nullable(Int64),
    updated_at DateTime
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY name;

CREATE TABLE IF NOT EXISTS client_session_entities (
    name LowCardinality(String),
    id Int64,
    hash Int64,
    username Nullable(String),
    phone Nullable(Int64),
    display_name String,
    updated_at DateTime
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (name, id);

CREATE TABLE IF NOT EXISTS client_session_sent_files (
    name LowCardinality(String),
    md5_digest BLOB,
    file_size Int64,
    type Int32,
    id Int64,
    hash Int64,
    updated_at DateTime
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (name, md5_digest, file_size, type);

CREATE TABLE IF NOT EXISTS client_session_update_state (
    name LowCardinality(String),
    id Int64,
    pts Int32,
    qts Int32,
    date DateTime,
    seq Int32,
    updated_at DateTime
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (name, id);
