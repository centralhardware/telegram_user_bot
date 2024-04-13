from config import Config
from telethon.sync import TelegramClient

from web import MessageSender
import logging
from aiohttp import web
from telethon import events
from ban_utils import ban
from notify_admins import notify_admins
from read_acknowledge_utils import read_acknowledge
from scrapper import save_outgoing, save_incoming

config = Config()


def create_telegram_client(session_name, phone):
    c = TelegramClient(session_name, config.api_id, config.api_hash)
    c.connect()
    c.start(phone=phone)
    return c


def add_event_handlers(client):
    client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    client.add_event_handler(notify_admins, events.NewMessage(outgoing=True, pattern='!n', forwards=False))


client2 = create_telegram_client('session/alex2', config.telephone2)
client = create_telegram_client('session/alex', config.telephone)

add_event_handlers(client)

client2.add_event_handler(read_acknowledge, events.NewMessage(outgoing=True, pattern='!r', forwards=False))
client2.add_event_handler(ban, events.NewMessage(outgoing=True, pattern='!ban', forwards=False))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('start application')

    sender = MessageSender(client)
    app = web.Application()
    app.add_routes([web.post('/', sender.handle_post)])
    web.run_app(app, port=8080, loop=client.loop)

    client.disconnect()
    client2.disconnect()
