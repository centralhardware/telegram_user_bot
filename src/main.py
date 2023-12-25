import json
import logging
import os
from datetime import datetime
from json.decoder import JSONDecodeError

import clickhouse_connect
from aiohttp import web
from telethon import events
from telethon.sync import TelegramClient

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
clickhouse.command("""
    CREATE TABLE IF NOT EXISTS telegram_messages (
                                                 date_time DateTime,
                                                 message String,
                                                 chat String)
    ENGINE MergeTree ORDER BY date_time
""")
clickhouse.command("""
    ALTER TABLE telegram_messages
    ADD COLUMN IF NOT EXISTS chat_id String
""")


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
    logging.info(username)
    logging.info(text)
    chat = await client.get_input_entity(username)
    async with client.conversation(chat) as conv:
        await conv.send_message(text)
        return True

@client.on(events.NewMessage(outgoing=True))
async def handler(event):
    chat_title = ''
    chat_id= ''
    if hasattr(event.chat, "title"):
        chat_title = event.chat.title
    if event.chat.username is not None:
        chat_id = event.chat.username

    if chat_title == '':
        chat_title = chat_id

    admins = []
    async for user in client.iter_participants(event.chat):
        try:
            if user.username.lower().endswith('bot'):
                continue
            if user.participant.admin_rights.delete_messages:
                admins.append(user.username)
        except AttributeError:
            pass
        except TypeError:
            pass

    if event.raw_text != '':
        logging.info("triggered in chat %s on message: %s", chat_title, event.raw_text)
        logging.info("found admins: %s ", admins)
        data = [[datetime.now(), event.raw_text, chat_title, chat_id, ','.join(admins)]]
        clickhouse.insert('telegram_messages', data, ['date_time', 'message', 'chat', 'chat_id', 'admins'])
        logging.info("insert new message\n")
    else:
        logging.info("ignore empty message\n")

@client.on(events.NewMessage(outgoing=True, pattern='!admin', forwards=False))
async def handler(event):
    try:
        logging.info("notify admin in %s", event.chat.title)
    except AttributeError:
        pass
    admins = []
    async for user in client.iter_participants(event.chat):
        try:
            if user.username.lower().endswith('bot'):
                continue
            if user.participant.admin_rights.delete_messages:
                admins.append(user.username)
        except AttributeError:
            pass
        except TypeError:
            pass
    if admins:
        logging.info("found admins: %s\n ", admins)
        await client.edit_message(event.message, '@' + admins[0])




if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.info('start application')

    client.connect()
    client.start(phone=telephone)
    app = web.Application()
    app.add_routes([web.post('/', handle_post),
                    web.get('/', handle_get)])
    web.run_app(app, port=8080)
    client.disconnect()
