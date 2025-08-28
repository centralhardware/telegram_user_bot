create table if not exists edited_chain_stats
(
    chat_id          Int64,
    message_id       Int64,
    versions_state   AggregateFunction(count),
    first_time_state AggregateFunction(min, DateTime),
    last_time_state  AggregateFunction(max, DateTime)
)
    engine = AggregatingMergeTree ORDER BY (chat_id, message_id);


CREATE MATERIALIZED VIEW IF NOT EXISTS telegram_user_bot.mv_edited_chain_stats TO telegram_user_bot.edited_chain_stats
        (
         `chat_id` Int64,
         `message_id` Int64,
         `versions_state` AggregateFunction(count),
         `first_time_state` AggregateFunction(min, DateTime),
         `last_time_state` AggregateFunction(max, DateTime)
            )
AS SELECT
       chat_id,
       message_id,
       countState() AS versions_state,
       minState(date_time) AS first_time_state,
       maxState(date_time) AS last_time_state
   FROM telegram_user_bot.edited_log
   GROUP BY
       chat_id,
       message_id;

CREATE VIEW IF NOT EXISTS telegram_user_bot.v_edited_chain_stats
            (
             `chat_id` Int64,
             `message_id` Int64,
             `edit_chain_length` Int64,
             `first_seen` DateTime,
             `last_seen` DateTime
                )
AS SELECT
       chat_id,
       message_id,
       countMerge(versions_state) - 1 AS edit_chain_length,
       minMerge(first_time_state) AS first_seen,
       maxMerge(last_time_state) AS last_seen
   FROM telegram_user_bot.edited_chain_stats
   GROUP BY
       chat_id,
       message_id
   ORDER BY last_seen DESC
   LIMIT 100;



