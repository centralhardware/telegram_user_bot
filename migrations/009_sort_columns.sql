SET allow_suspicious_low_cardinality_types = 1;

ALTER TABLE telegram_user_bot.admin_actions2
    MODIFY COLUMN action_type LowCardinality(String) FIRST,
    MODIFY COLUMN chat_id UInt64 AFTER action_type,
    MODIFY COLUMN chat_title LowCardinality(String) AFTER chat_id,
    MODIFY COLUMN chat_usernames Array(LowCardinality(String)) AFTER chat_title,
    MODIFY COLUMN date DateTime AFTER chat_usernames,
    MODIFY COLUMN event_id UInt64 AFTER date,
    MODIFY COLUMN message String AFTER event_id,
    MODIFY COLUMN user_id UInt64 AFTER message,
    MODIFY COLUMN user_title String AFTER user_id,
    MODIFY COLUMN usernames Array(String) AFTER user_title;

ALTER TABLE telegram_user_bot.chats_log
    MODIFY COLUMN chat_id Int64 FIRST,
    MODIFY COLUMN chat_title LowCardinality(String) AFTER chat_id,
    MODIFY COLUMN chat_usernames Array(LowCardinality(String)) AFTER chat_title,
    MODIFY COLUMN client_id LowCardinality(UInt64) AFTER chat_usernames,
    MODIFY COLUMN date_time DateTime AFTER client_id,
    MODIFY COLUMN first_name String AFTER date_time,
    MODIFY COLUMN message String AFTER first_name,
    MODIFY COLUMN message_id Int64 AFTER message,
    MODIFY COLUMN reply_to UInt64 AFTER message_id,
    MODIFY COLUMN second_name String AFTER reply_to,
    MODIFY COLUMN user_id UInt64 AFTER second_name,
    MODIFY COLUMN username Array(String) AFTER user_id;

ALTER TABLE telegram_user_bot.deleted_log
    MODIFY COLUMN chat_id Int64 FIRST,
    MODIFY COLUMN client_id LowCardinality(UInt64) AFTER chat_id,
    MODIFY COLUMN date_time DateTime AFTER client_id,
    MODIFY COLUMN message_id Int64 AFTER date_time;

ALTER TABLE telegram_user_bot.telegram_messages_new
    MODIFY COLUMN admins2 Array(LowCardinality(String)) FIRST,
    MODIFY COLUMN client_id LowCardinality(UInt64) AFTER admins2,
    MODIFY COLUMN date_time DateTime AFTER client_id,
    MODIFY COLUMN id Int64 AFTER date_time,
    MODIFY COLUMN message String AFTER id,
    MODIFY COLUMN message_id UInt64 AFTER message,
    MODIFY COLUMN raw String AFTER message_id,
    MODIFY COLUMN reply_to UInt64 AFTER raw,
    MODIFY COLUMN title LowCardinality(String) AFTER reply_to,
    MODIFY COLUMN usernames Array(LowCardinality(String)) AFTER title;

ALTER TABLE telegram_user_bot.user_sessions
    MODIFY COLUMN app_name LowCardinality(String) FIRST,
    MODIFY COLUMN app_version LowCardinality(Nullable(String)) AFTER app_name,
    MODIFY COLUMN client_id LowCardinality(UInt64) AFTER app_version,
    MODIFY COLUMN country LowCardinality(String) AFTER client_id,
    MODIFY COLUMN date_active DateTime AFTER country,
    MODIFY COLUMN date_created DateTime AFTER date_active,
    MODIFY COLUMN device_model LowCardinality(String) AFTER date_created,
    MODIFY COLUMN hash Int64 AFTER device_model,
    MODIFY COLUMN ip LowCardinality(Nullable(String)) AFTER hash,
    MODIFY COLUMN platform LowCardinality(String) AFTER ip,
    MODIFY COLUMN region LowCardinality(String) AFTER platform,
    MODIFY COLUMN system_version LowCardinality(Nullable(String)) AFTER region,
    MODIFY COLUMN updated_at DateTime AFTER system_version;
