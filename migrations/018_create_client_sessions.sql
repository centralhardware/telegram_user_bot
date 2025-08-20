SET allow_suspicious_low_cardinality_types = 1;

CREATE TABLE IF NOT EXISTS client_sessions (
    name LowCardinality(String),
    session String,
    updated_at DateTime
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY name;
