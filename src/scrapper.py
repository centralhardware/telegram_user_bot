import functools
import shutil
import textwrap
from datetime import datetime
import clickhouse_connect
import redis
from detoxify import Detoxify
from lingua import LanguageDetectorBuilder, Language
import logging
from admin_utils import get_admins
from config import Config
from termcolor import colored


# Extracted utility function
def build_usernames_from_chat(chat):
    chat_usernames = []
    if hasattr(chat, "username") and chat.username is not None:
        chat_usernames.append(chat.username)
    elif hasattr(chat, "usernames") and chat.usernames is not None:
        for u in chat.usernames:
            chat_usernames.append(u.username)
    return chat_usernames


config = Config()
clickhouse = clickhouse_connect.get_client(host=config.db_host, database=config.db_database, port=8123,
                                           username=config.db_user, password=config.db_password,
                                           settings={'async_insert': '1', 'wait_for_async_insert': '0'})


async def save_outgoing(event):
    chat_title = ''
    chat_id = build_usernames_from_chat(event.chat)

    if hasattr(event.chat, "title"):
        chat_title = event.chat.title
    else:
        if event.chat is not None and event.chat.bot and hasattr(event.chat, "first_name"):
            chat_title = event.chat.first_name

    chat = await event.get_chat()
    chat_id_copy = build_usernames_from_chat(chat)
    chat_id.extend(chat_id_copy)

    if hasattr(chat, "first_name"):
        last_name = chat.last_name if chat.last_name is not None else ""
        chat_title = chat.first_name + ' ' + last_name

    if chat_title == '':
        chat_title = chat_id[0]
    t = await get_admins(event.chat)
    if event.raw_text != '':
        logging.info(f"{chat_title}: {event.raw_text} {t[1]} {t[0]}")
        data = [[datetime.now(), event.raw_text, chat_title, chat_id, event.chat_id, t[1], t[0]]]
        clickhouse.insert('telegram_messages_new', data,
                          ['date_time', 'message', 'title', 'usernames', 'id', 'members_count', 'admins2'])
    else:
        logging.info("ignore empty message")


@functools.cache
def is_baned(chat_id):
    return r.sismember('banned', chat_id)


languages = [Language.ENGLISH, Language.RUSSIAN]
lng = LanguageDetectorBuilder.from_languages(*languages).with_preloaded_language_models().build()
detoxify = Detoxify('multilingual')
config = Config()
r = redis.Redis(host=config.redis_host, port=config.redis_port, decode_responses=True)


async def save_incoming(event):
    if is_baned(event.chat_id):
        return
    if event.chat_id >= 0 or event.is_private is True or event.raw_text == '' or event.message.sender is None: return
    tox = detoxify.predict(event.raw_text)
    try:
        lang = lng.detect_language_of(event.raw_text).name
    except Exception:
        lang = '      '

    toxicity = "toxic    " if tox['toxicity'] > 0.5 else "non toxic"
    color = "red" if tox['toxicity'] > 0.5 else "green"

    raw_text_lines = event.raw_text.splitlines()
    wrapped_lines = []
    reserved_symbols = 48
    for i, line in enumerate(raw_text_lines):
        indent = ' ' * reserved_symbols if i else ''
        wrapped = textwrap.fill(line, width=130, initial_indent=indent,
                                subsequent_indent=indent)
        wrapped_lines.append(wrapped)

    adjusted_raw_text = '\n'.join(wrapped_lines)

    logging.info(
        f"{event.message.id:12,} {colored(toxicity, color)} {event.chat.title[:20]:<25s} {adjusted_raw_text} reply to {event.message.reply_to_msg_id}")

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
    data = [[
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
        event.message.reply_to_msg_id,
        *tox.values(),
        lang
    ]]
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
                       'reply_to',
                       'toxicity',
                       'severe_toxicity',
                       'obscene',
                       'identity_attack',
                       'insult',
                       'threat',
                       'sexual_explicit',
                       'lang'])

