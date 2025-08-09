ALTER TABLE chats_log MODIFY COLUMN message String AFTER date_time;
ALTER TABLE admin_actions2 MODIFY COLUMN date DateTime FIRST;
