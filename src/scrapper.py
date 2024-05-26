import logging
from datetime import datetime

import clickhouse_connect

from Accumulator import Accumulator
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
                                           username=config.db_user, password=config.db_password)


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


acc_inc = Accumulator(save_inc, 'incoming')
acc_del = Accumulator(save_del, 'deleted')


async def save_incoming(event):
    if event.chat_id >= 0 or event.is_private is True or event.raw_text == '' or event.message.sender is None: return

    text = event.raw_text.split('\n')[0]
    logging.info(
        f"incoming {acc_inc.len():3} {event.message.id:12,} {event.chat.title[:20]:<25s} {text} reply to {event.message.reply_to_msg_id}")

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

    acc_inc.add([
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
    ])


async def save_deleted(event):
    if event.chat_id is None: return

    for msg_id in event.deleted_ids:
        logging.info(f"{acc_del.len():3} Deleted {event.chat_id} {msg_id}")
        acc_del.add([datetime.now(), event.chat_id, msg_id])
