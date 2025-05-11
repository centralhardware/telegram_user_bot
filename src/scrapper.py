import json
import logging
from datetime import datetime

import clickhouse_connect
from termcolor import colored

from admin_utils import get_admins
from config import config


# Extracted utility function
def build_usernames_from_chat(chat):
    chat_usernames = []
    if hasattr(chat, "username") and chat.username is not None:
        chat_usernames.append(chat.username)
    elif hasattr(chat, "usernames") and chat.usernames is not None:
        for u in chat.usernames:
            chat_usernames.append(u.username)
    return chat_usernames


def remove_empty_and_none(obj):
    if isinstance(obj, dict):
        cleaned = {
            k: remove_empty_and_none(v)
            for k, v in obj.items()
            if v is not None
        }
        return {k: v for k, v in cleaned.items() if v not in (None, {}, [])}
    elif isinstance(obj, list):
        cleaned = [remove_empty_and_none(v) for v in obj if v is not None]
        return [v for v in cleaned if v not in (None, {}, [])]
    else:
        return obj


clickhouse = clickhouse_connect.get_client(host=config.db_host, database=config.db_database, port=8123,
                                           username=config.db_user, password=config.db_password,
                                           settings={'async_insert': '1', 'wait_for_async_insert': '0'})


async def save_outgoing(event):
    chat_title = ''

    if hasattr(event.chat, "title"):
        chat_title = event.chat.title
    else:
        if event.chat is not None and event.chat.bot and hasattr(event.chat, "first_name"):
            chat_title = event.chat.first_name

    chat = await event.get_chat()
    chat_id = build_usernames_from_chat(chat)

    if hasattr(chat, "first_name"):
        last_name = chat.last_name if chat.last_name is not None else ""
        chat_title = chat.first_name + ' ' + last_name

    if chat_title == '':
        chat_title = chat_id[0]

    admins = await get_admins(event.chat, event.client)
    message_dict = remove_empty_and_none(event.message.to_dict())
    message_json = json.dumps(message_dict, default=str, ensure_ascii=False)
    logging.info(f"outcoming {chat_title}: [empty raw_text, serialized to JSON]")
    data = [[datetime.now(), event.raw_text, message_json, chat_title, chat_id, event.chat_id, admins, event.message.id, event.message.reply_to_msg_id]]
    clickhouse.insert('telegram_user_bot.telegram_messages_new', data,
                                  ['date_time', 'message', 'raw',  'title', 'usernames', 'id', 'admins2', 'message_id', 'reply_to'])


def save_inc(data):
    clickhouse.insert('telegram_user_bot.chats_log', data,
                      ['date_time',
                       'chat_title',
                       'chat_id',
                       'username',
                       'chat_usernames',
                       'first_name',
                       'second_name',
                       'user_id',
                       'message_id',
                       'message',
                       'raw',
                       'reply_to'])


def save_del(data):
    clickhouse.insert('telegram_user_bot.deleted_log',
                      data,
                      ['date_time', 'chat_id', 'message_id'])


async def save_incoming(event):
    if event.chat_id >= 0 or event.is_private is True or event.message.sender is None: return

    if event.raw_text != '':
        logging.info(
                f"incoming {event.message.id:12,} {event.chat.title[:20]:<25s} {event.raw_text} reply to {event.message.reply_to_msg_id}")
    else:
        logging.info(
                f"incoming {event.message.id:12,} {event.chat.title[:20]:<25s} [empty raw_text, serialized to JSON] reply to {event.message.reply_to_msg_id}")

    usernames = []
    if event.message.sender.username is not None:
        usernames.append(event.message.sender.username)
    elif event.message.sender.usernames is not None:
        for u in event.message.sender.usernames:
            usernames.append(u.username)
    chat_usernames = build_usernames_from_chat(event.chat)
    try:
        first_name = event.message.sender.first_name
        last_name = event.message.sender.last_name
    except Exception:
        first_name = None
        last_name = None

    # Prepare message content - either raw_text or JSON serialized message
    message_content = event.raw_text
    if event.raw_text == '':
        try:
            # Serialize message object to JSON when raw_text is empty
            message_dict = remove_empty_and_none(event.message.to_dict())
            message_content = json.dumps(message_dict, default=str, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error serializing empty incoming message: {e}")
            message_content = "[Error serializing message]"

    save_inc([[
        datetime.now(),
        event.chat.title,
        event.chat_id,
        usernames,
        chat_usernames,
        first_name,
        last_name,
        event.message.sender.id,
        event.message.id,
        message_content,
        event.message.reply_to_msg_id
    ]])


async def save_deleted(event):
    if event.chat_id is None: return

    for msg_id in event.deleted_ids:
        save_del([[datetime.now(), event.chat_id, msg_id]])

        try:
            chat_title = clickhouse.query("""
            SELECT chat_title
            FROM telegram_user_bot.chats_log
            WHERE chat_id = {chat_id:Int64}
            ORDER BY date_time DESC
            LIMIT 1
            """, {'chat_id': event.chat_id}).result_rows[0][0]
        except Exception:
            chat_title = event.chat_id

        try:
            message = clickhouse.query("""
            SELECT message
            FROM telegram_user_bot.chats_log
            WHERE chat_id = {chat_id:Int64} and message_id = {message_id:Int64}
            LIMIT 1
            """, {'chat_id': event.chat_id, 'message_id': msg_id}).result_rows[0][0]
        except Exception:
            message = msg_id

        logging.info(colored(f" Deleted {chat_title} {msg_id} {message}", 'yellow'))
