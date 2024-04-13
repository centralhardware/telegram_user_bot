import logging
import os
from datetime import datetime

from detoxify import Detoxify
import clickhouse_connect
from aiohttp import web
import redis
from lingua import LanguageDetectorBuilder, Language
from telethon import events
from telethon.sync import TelegramClient
from telethon.tl.types import ChatParticipantCreator

config = {
    'api_id': int(os.getenv('API_ID')),
    'api_hash': os.getenv('API_HASH'),
    'telephone': os.getenv('TELEPHONE'),
    'telephone2': os.getenv('TELEPHONE2'),
    'db_user': os.getenv("DB_USER"),
    'db_password': os.getenv("DB_PASSWORD"),
    'db_host': os.getenv("DB_HOST"),
    'db_database': os.getenv("DB_DATABASE"),
    'redis_host': os.getenv("REDIS_HOST"),
    'redis_port': os.getenv('REDIS_PORT')
}

client = TelegramClient('session/alex', config['api_id'], config['api_hash'])
client2 = TelegramClient('session/alex2', config['api_id'], config['api_hash'])
clickhouse = clickhouse_connect.get_client(host=config['db_host'], database=config['db_database'], port=8123,
                                           username=config['db_user'], password=config['db_password'],
                                           settings={'async_insert': '1', 'wait_for_async_insert': '0'})
detoxify = Detoxify('multilingual')
languages = [Language.ENGLISH, Language.RUSSIAN]
lng = LanguageDetectorBuilder.from_languages(*languages).with_preloaded_language_models().build()
r = redis.Redis(host=config.get('redis_host'), port=config.get('redis_port'), decode_responses=True)


async def handle_post(request):
    try:
        username = request.query['username']
        text = request.query['text']
    except Exception:
        return web.Response(status=400)
    result = await handle(username, text)
    if result:
        return web.Response(status=200, body='ok')


async def handle(username, text):
    chat = await client.get_input_entity(username)
    async with client.conversation(chat) as conv:
        await conv.send_message(text)
        return True


@client.on(events.NewMessage(outgoing=True))
async def handler(event):
    chat_title = ''
    chat_id = []
    if hasattr(event.chat, "title"):
        chat_title = event.chat.title
    else:
        if event.chat is not None and event.chat.bot and hasattr(event.chat, "first_name"):
            chat_title = event.chat.first_name
    if hasattr(event.chat, "username") and event.chat.username is not None:
        chat_id.append(event.chat.username)
    elif hasattr(event.chat, "usernames") and event.chat.usernames is not None:
        for u in event.chat.usernames:
            chat_id.append(u.username)
    else:
        chat = await event.get_chat()
        if hasattr(chat, "username") and chat.username is not None:
            chat_id.append(chat.username)
        elif hasattr(chat, "usernames") and chat.usernames is not None:
            for u in chat.usernames:
                chat_id.append(u.username)
        if hasattr(chat, "first_name"):
            last_name = chat.last_name
            if last_name is None:
                last_name = ""
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


@client.on(events.NewMessage(outgoing=True, pattern='!n', forwards=False))
async def admin(event):
    if event.raw_text == "!n":
        n = 1
    else:
        n = int(event.raw_text.replace("!n", ""))
    t = await get_admins(event.chat)
    admins = t[0]
    if admins:
        logging.info(f"notify {n} admins in {event.chat.title} ({admins})")
        await client.delete_messages(event.chat, message_ids=[event.message.id])

        admins = admins[:n]

        msg = ", ".join(admins)
        if event.message.reply_to_msg_id:
            await client.send_message(event.chat, msg, reply_to=event.message.reply_to_msg_id)
        else:
            await client.send_message(event.chat, msg)


@client.on(events.NewMessage(incoming=True))
@client2.on(events.NewMessage(incoming=True))
async def handler(event):
    if r.sismember('banned', event.chat_id): return

    if event.chat_id >= 0 or event.is_private is True or event.raw_text == '' or event.message.sender is None: return

    tox = detoxify.predict(event.raw_text)
    try:
        lang = lng.detect_language_of(event.raw_text).name
    except Exception:
        lang = '      '
    logging.info(
        f"{event.message.id:12,} {event.chat.title[:20]:<20s} {tox['toxicity']:.4f} {event.raw_text} reply to {event.message.reply_to_msg_id}")

    usernames = []
    if event.message.sender.username is not None:
        usernames.append(event.message.sender.username)
    elif event.message.sender.usernames is not None:
        for u in event.message.sender.usernames:
            usernames.append(u.username)

    chat_usernames = []
    if hasattr(event.chat, "username") and event.chat.username is not None:
        chat_usernames.append(event.chat.username)
    elif hasattr(event.chat, "usernames") and event.chat.usernames is not None:
        for u in event.chat.usernames:
            chat_usernames.append(u.username)

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
        tox['toxicity'],
        tox['severe_toxicity'],
        tox['obscene'],
        tox['identity_attack'],
        tox['insult'],
        tox['threat'],
        tox['sexual_explicit'],
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


async def get_admins(chat):
    admins = []
    count = 0
    async for user in client.iter_participants(chat):
        try:
            count = count + 1
            if user.bot:
                continue
            if isinstance(user.participant, ChatParticipantCreator) or user.participant.admin_rights.delete_messages:
                if user.username is not None:
                    admins.append("@" + user.username)
                else:
                    admins.append("@" + user.usernames[0].username)
        except AttributeError:
            pass
        except TypeError:
            pass
    return [admins, count]


@client2.on(events.NewMessage(outgoing=True, pattern='!r', forwards=False))
async def handler(event):
    async for dialog in client2.iter_dialogs():
        logging.info(f"mark {dialog.name} as read")
        await client2.send_read_acknowledge(dialog, clear_mentions=True, clear_reactions=True)


@client2.on(events.NewMessage(outgoing=True, pattern='!ban', forwards=False))
async def handler(event):
    await r.sadd('banned', event.raw_text.replace('!ban ', ''))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('start application')

    client.connect()
    client.start(phone=config['telephone'])
    client2.connect()
    client2.start(phone=config['telephone2'])
    app = web.Application()
    app.add_routes([web.post('/', handle_post)])
    web.run_app(app, port=8080, loop=client.loop)
    client.disconnect()
