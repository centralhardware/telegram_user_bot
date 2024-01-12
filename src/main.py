import json
import logging
import os
from datetime import datetime
from json.decoder import JSONDecodeError

import clickhouse_connect
from aiohttp import web
from telethon import events
from telethon.sync import TelegramClient
from telethon.tl.types import ChatParticipantCreator


def str2bool(boolean_string):
    return boolean_string.lower() in ("yes", "true", "t", "1")


api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
telephone = os.getenv('TELEPHONE')
client = TelegramClient('session/alex', api_id, api_hash)

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST")
database = os.getenv("DB_DATABASE")
clickhouse = clickhouse_connect.get_client(host=host, database=database, port=8123, username=user, password=password)


async def handle_post(request):
    body = await request.text()
    if not body:
        return web.Response(status=422, body='emtpy body')
    try:
        data = json.loads(body)
        result = await handle(data['username'], data['text'])
    except JSONDecodeError:
        return web.Response(status=422, body='invalid json')
    except KeyError:
        return web.Response(status=422, body='mission required param username')

    if result:
        return web.Response(status=200, body='ok')
    else:
        return web.Response(status=400, body='bot offline')


async def handle_get(request):
    try:
        username = request.query['username']
        text = request.query['text']
    except KeyError:
        return web.Response(status=422, body='mission required param username')
    if not username:
        return web.Response(status=422, body='username param can not be empty')
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
    chat_id = ''
    if hasattr(event.chat, "title"):
        chat_title = event.chat.title
    else:
        if event.chat is not None and event.chat.bot and hasattr(event.chat, "first_name"):
            chat_title = event.chat.first_name
    if hasattr(event.chat, "username"):
        chat_id = event.chat.username
    else:
        chat = await event.get_chat()
        if hasattr(chat, "username") and chat.username is not None:
            chat_id = chat.username
        if hasattr(chat, "first_name"):
            last_name = chat.last_name
            if last_name is None:
                last_name = ""
            chat_title = chat.first_name + ' ' + last_name

    if chat_title == '':
        chat_title = chat_id
    if chat_id is None:
        chat_id = ''

    t = await get_admins(event.chat)
    if event.raw_text != '':
        logging.info("%s: %s %s (%s)", chat_title, event.raw_text, t[1], t[0])
        data = [[datetime.now(), event.raw_text, chat_title, chat_id, event.chat_id, t[1], t[0]]]
        clickhouse.insert('telegram_messages_new', data,
                          ['date_time', 'message', 'title', 'username', 'id', 'members_count', 'admins2'])
    else:
        logging.info("ignore empty message")


@client.on(events.NewMessage(outgoing=True, pattern='!admin', forwards=False))
async def handler(event):
    t = await get_admins(event.chat)
    admins = t[0]
    if admins:
        logging.info("notify admin in %s (%s) ", event.chat.title, admins)
        await client.edit_message(event.message, '@' + admins[0])


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
                    admins.append(user.username)
                else:
                    admins.append(user.usernames[0].username)
        except AttributeError:
            pass
        except TypeError:
            pass
    return [admins, count]


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('start application')

    client.connect()
    client.start(phone=telephone)
    app = web.Application()
    app.add_routes([web.post('/', handle_post),
                    web.get('/', handle_get)])
    web.run_app(app, port=8080)
    client.disconnect()
