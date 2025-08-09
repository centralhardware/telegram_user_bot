CREATE MATERIALIZED VIEW mv_my_messages_to_chats_log
            TO chats_log
AS
SELECT
    date_time,
    title                                 AS chat_title,
    CAST(id AS Int64)                     AS chat_id,
    CAST([] AS Array(String))             AS username,
    ''                                    AS first_name,
    ''                                    AS second_name,
    client_id                             AS user_id,
    CAST(message_id AS Int64)             AS message_id,
    message,
    CAST(usernames AS Array(LowCardinality(String))) AS chat_usernames,
    reply_to,
    client_id
FROM telegram_messages_new;
