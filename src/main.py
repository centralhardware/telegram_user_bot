import logging

from aiohttp import web
from telethon import events
from telethon.sync import TelegramClient

from config import config
from notify_admins import notify_admins
from scrapper import save_outgoing, save_incoming, save_deleted
from Top import top
from Deleted import deleted
from Ai import answer
from web import MessageSender


def create_telegram_client(session_name, phone):
    c = TelegramClient(session_name, config.api_id, config.api_hash)
    c.connect()
    c.start(phone=phone)
    return c


client = create_telegram_client('session/alex', config.telephone)
client2 = create_telegram_client('session/alex2', config.telephone2)

client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
client.add_event_handler(save_deleted, events.MessageDeleted())
client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
client.add_event_handler(notify_admins, events.NewMessage(outgoing=True, pattern='!n', forwards=False))
client.add_event_handler(top, events.NewMessage(outgoing=True, pattern='!top', forwards=False, chats=[-1001633660171]))
client.add_event_handler(top, events.NewMessage(incoming=True, pattern='!top', forwards=False, chats=[-1001633660171]))
client.add_event_handler(deleted, events.NewMessage(outgoing=True, pattern='!deleted', forwards=False, chats=[-1001633660171]))
client.add_event_handler(deleted, events.NewMessage(incoming=True, pattern='!deleted', forwards=False, chats=[-1001633660171]))
client.add_event_handler(answer, events.NewMessage(outgoing=True, pattern='!ai', forwards=False))
client.add_event_handler(answer, events.NewMessage(incoming=True, pattern='!ai', forwards=False, chats=[-1001633660171]))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('start application')

    sender = MessageSender(client)
    app = web.Application()
    app.add_routes([web.post('/', sender.handle_post)])
    web.run_app(app, port=8080, loop=client.loop)

    client.disconnect()
