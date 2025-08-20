SET allow_suspicious_low_cardinality_types = 1;

-- 1) Сессии клиента: auth_key храним как RAW bytes в Nullable(String)
CREATE TABLE IF NOT EXISTS client_sessions
(
    name           LowCardinality(String),
    dc_id          UInt32,
    server_address String,
    port           UInt16,
    auth_key       Nullable(String) CODEC(ZSTD(3)),   -- сырые байты (не hex)
    takeout_id     Nullable(Int64),
    updated_at     DateTime64(3, 'UTC')
)
    ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY name;

-- 2) Кеш сущностей: телефон как строка, не число
CREATE TABLE IF NOT EXISTS client_session_entities
(
    name         LowCardinality(String),
    id           Int64,
    hash         Int64,
    username     Nullable(String),
    phone        Nullable(String),                    -- телефон как текст
    display_name String,
    updated_at   DateTime64(3, 'UTC')
)
    ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (name, id);

-- 3) Отправленные файлы: md5_digest как RAW 16 байт
CREATE TABLE IF NOT EXISTS client_session_sent_files
(
    name        LowCardinality(String),
    md5_digest  FixedString(16),                      -- 16 «сырых» байт (не hex)
    file_size   UInt64,
    type        UInt8,
    id          UInt64,
    hash        UInt64,
    updated_at  DateTime64(3, 'UTC')
)
    ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (name, md5_digest, file_size, type);

-- 4) Состояния апдейтов
CREATE TABLE IF NOT EXISTS client_session_update_state
(
    name       LowCardinality(String),
    id         Int64,
    pts        Int32,
    qts        Int32,
    date       DateTime64(3, 'UTC'),
    seq        Int32,
    updated_at DateTime64(3, 'UTC')
)
    ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (name, id);
