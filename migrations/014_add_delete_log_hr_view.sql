SET allow_suspicious_low_cardinality_types = 1;

CREATE OR REPLACE VIEW telegram_user_bot.delete_log_hr AS
SELECT
    dl.date_time,
    dl.client_id,
    dl.chat_id,
    cs.chat_title,
    dl.message_id,
    cl.message AS original_message
FROM telegram_user_bot.deleted_log AS dl
         LEFT JOIN
     (
         SELECT
             client_id,
             chat_id,
             anyLast(last_title) AS chat_title
         FROM telegram_user_bot.mv_chat_stat
         WHERE (client_id, chat_id) IN (
             SELECT DISTINCT client_id, chat_id FROM telegram_user_bot.deleted_log
         )
         GROUP BY client_id, chat_id
         ) AS cs USING (client_id, chat_id)

         LEFT JOIN
     (
         SELECT
             client_id,
             chat_id,
             message_id,
             anyLast(message) AS message
         FROM telegram_user_bot.chats_log
         WHERE (client_id, chat_id, message_id) IN (
             SELECT DISTINCT client_id, chat_id, message_id
             FROM telegram_user_bot.deleted_log
         )
         GROUP BY client_id, chat_id, message_id
         ) AS cl
     USING (client_id, chat_id, message_id);
