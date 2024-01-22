import logging
import os
from datetime import datetime

import clickhouse_connect
from aiohttp import web
from telethon import events
from telethon.sync import TelegramClient
from telethon.tl.types import ChatParticipantCreator

config = {
    'api_id': int(os.getenv('API_ID')),
    'api_hash': os.getenv('API_HASH'),
    'telephone': os.getenv('TELEPHONE'),
    'db_user': os.getenv("DB_USER"),
    'db_password': os.getenv("DB_PASSWORD"),
    'db_host': os.getenv("DB_HOST"),
    'db_database': os.getenv("DB_DATABASE"),
}

client = TelegramClient('session/alex', config['api_id'], config['api_hash'])
clickhouse = clickhouse_connect.get_client(host=config['db_host'], database=config['db_database'], port=8123,
                                           username=config['db_user'], password=config['db_password'], settings={'async_insert': '1', 'wait_for_async_insert': '0'})


async def handle_post(request):
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
        logging.info(f"{chat_title}: {event.raw_text} {t[1]} {t[0]}")
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
        logging.info(f"notify admin in {event.chat.title} ({admins})")
        await client.edit_message(event.message, '@' + admins[0])


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.chat_id >= 0 or event.is_private == True or event.raw_text == '': return

    usernames = []
    if (event.message.sender.username is not None):
        usernames.append(event.message.sender.username)
    elif (event.message.sender.usernames is not None):
        for u in event.message.sender.usernames:
            usernames.append(u.username)

    try:
        first_name = event.message.sender.first_name
    except KeyError:
        first_name = None

    data = [[
        datetime.now(),
        event.chat.title,
        event.chat_id,
        usernames,
        first_name,
        event.message.sender.last_name,
        event.message.sender.id,
        event.message.id,
        event.raw_text
    ]]
    clickhouse.insert('chats_log', data, ['date_time', 'chat_title','chat_id' , 'username', 'first_name', 'second_name', 'user_id', 'message_id', 'message'])

    logging.info(f"log message in chat {event.chat.title} {event.message.id}")

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
    client.start(phone=config['telephone'])
    app = web.Application()
    app.add_routes([web.post('/', handle_post)])
    web.run_app(app, port=8080)
    client.disconnect()
