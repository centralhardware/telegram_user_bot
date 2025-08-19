SET allow_suspicious_low_cardinality_types = 1;

ALTER TABLE edited_log ADD COLUMN original_message String AFTER message_id;

CREATE OR REPLACE VIEW telegram_user_bot.edit_log_hr AS
SELECT
    el.date_time,
    el.client_id,
    el.chat_id,
    cs.chat_title,                -- из mv_chat_stat, схлопнуто
    el.message_id,
    el.original_message,
    el.message,
    el.diff,
    el.user_id,
    us.username,                  -- из mv_user_stat, схлопнуто
    us.first_name,
    us.second_name
FROM telegram_user_bot.edited_log AS el
         LEFT JOIN
     (
         SELECT
             client_id,
             chat_id,
             anyLast(last_title) AS chat_title
         FROM telegram_user_bot.mv_chat_stat
         GROUP BY client_id, chat_id
     ) AS cs USING (client_id, chat_id)
         LEFT JOIN
     (
         SELECT
             client_id,
             user_id,
             anyLast(username)   AS username,
             anyLast(first_name) AS first_name,
             anyLast(second_name) AS second_name
         FROM telegram_user_bot.mv_user_stat
         GROUP BY client_id, user_id
     ) AS us
     ON  us.client_id = el.client_id
         AND us.user_id   = toUInt64(el.user_id);
