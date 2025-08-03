SET allow_suspicious_low_cardinality_types = 1;

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
    sumState(if((reply_to IS NOT NULL) AND (reply_to != 0), 1, 0)) AS reply_msg_count,
    groupUniqArrayState(user_id) AS participants,
    maxState(message_id) AS last_message_id
FROM telegram_user_bot.chats_log
GROUP BY
    client_id,
    chat_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS telegram_user_bot.mv_message_stats
(
    `id` Int64,
    `client_id` LowCardinality(UInt64),
    `last_title` AggregateFunction(anyLast, String),
    `cnt_state` AggregateFunction(count)
)
ENGINE = AggregatingMergeTree
ORDER BY (id, client_id)
SETTINGS index_granularity = 8192
AS SELECT
    id,
    client_id,
    anyLastState(title) AS last_title,
    countState() AS cnt_state
FROM telegram_user_bot.telegram_messages_new
GROUP BY (id, client_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS telegram_user_bot.mv_user_stat
(
    `client_id` LowCardinality(UInt64),
    `user_id` UInt64,
    `username` Array(String),
    `first_name` Nullable(String),
    `second_name` Nullable(String),
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
    sumState(if((reply_to IS NOT NULL) AND (reply_to != 0), 1, 0)) AS reply_msg_count
FROM telegram_user_bot.chats_log
GROUP BY
    client_id,
    user_id;
