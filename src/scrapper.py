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
    t = await get_admins(event.chat, event.client)
    if event.raw_text != '':
        logging.info(f"outcoming {chat_title}: {event.raw_text} {t[1]} {t[0]}")
        data = [[datetime.now(), event.raw_text, chat_title, chat_id, event.chat_id, t[1], t[0]]]
        clickhouse.insert('telegram_messages_new', data,
                          ['date_time', 'message', 'title', 'usernames', 'id', 'members_count', 'admins2'])
    else:
        logging.info("ignore empty message")


def save_inc(data):
    clickhouse.insert('chats_log', data,
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
                       'reply_to'])


def save_del(data):
    clickhouse.insert('deleted_log',
                      data,
                      ['date_time', 'chat_id', 'message_id'])


async def save_incoming(event):
    if event.chat_id >= 0 or event.is_private is True or event.raw_text == '' or event.message.sender is None: return

    logging.info(
        f"incoming {event.message.id:12,} {event.chat.title[:20]:<25s} {event.raw_text} reply to {event.message.reply_to_msg_id}")

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
        event.raw_text,
        event.message.reply_to_msg_id
    ]])


async def save_deleted(event):
    if event.chat_id is None: return

    res = clickhouse.query("""
        SELECT chat_title, message
        FROM chats_log
        WHERE chat_id = {id:Int64}
        ORDER BY date_time
        LIMIT 1
        """, {'id': event.chat_id})
    for msg_id in event.deleted_ids:
        logging.info(colored(f" Deleted {res.result_rows[0][0]} {msg_id} {res.result_rows[0][1]}", 'red'))
        save_del([[datetime.now(), event.chat_id, msg_id]])
