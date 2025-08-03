SET allow_suspicious_low_cardinality_types = 1;

ALTER TABLE telegram_user_bot.chats_log
UPDATE first_name = '' WHERE first_name IS NULL;

ALTER TABLE telegram_user_bot.chats_log
UPDATE second_name = '' WHERE second_name IS NULL;

ALTER TABLE telegram_user_bot.chats_log
UPDATE reply_to = 0 WHERE reply_to IS NULL;

ALTER TABLE telegram_user_bot.chats_log
    MODIFY COLUMN first_name String,
    MODIFY COLUMN second_name String,
    MODIFY COLUMN reply_to UInt64;


DROP VIEW IF EXISTS telegram_user_bot.mv_chat_stat;
DROP VIEW IF EXISTS telegram_user_bot.mv_user_stat;

CREATE MATERIALIZED VIEW IF NOT EXISTS telegram_user_bot.mv_chat_stat
(
    `client_id` LowCardinality(UInt64),
    `chat_id` Int64,
    `last_title` String,
    `msg_count` AggregateFunction(count),
    `reply_msg_count` AggregateFunction(sum, UInt8),
    `participants` AggregateFunction(groupUniqArray, UInt64),
    `last_message_id` AggregateFunction(max, Int64)
)
ENGINE = AggregatingMergeTree
ORDER BY (client_id, chat_id)
SETTINGS index_granularity = 8192
AS SELECT
    client_id,
    chat_id,
    anyLast(chat_title) AS last_title,
    countState() AS msg_count,
    sumState(if(reply_to != 0, 1, 0)) AS reply_msg_count,
    groupUniqArrayState(user_id) AS participants,
    maxState(message_id) AS last_message_id
FROM telegram_user_bot.chats_log
GROUP BY
    client_id,
    chat_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS telegram_user_bot.mv_user_stat
(
    `client_id` LowCardinality(UInt64),
    `user_id` UInt64,
    `username` Array(String),
    `first_name` String,
    `second_name` String,
    `chats` AggregateFunction(groupUniqArray, Int64),
    `msg_count` AggregateFunction(count),
    `reply_msg_count` AggregateFunction(sum, UInt8)
)
ENGINE = AggregatingMergeTree
ORDER BY (client_id, user_id)
SETTINGS index_granularity = 8192
AS SELECT
    client_id,
    user_id,
    anyLast(username) AS username,
    anyLast(first_name) AS first_name,
    anyLast(second_name) AS second_name,
    groupUniqArrayState(chat_id) AS chats,
    countState() AS msg_count,
    sumState(if(reply_to != 0, 1, 0)) AS reply_msg_count
FROM telegram_user_bot.chats_log
GROUP BY
    client_id,
    user_id;
