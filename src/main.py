from src.config import Config
from telethon.sync import TelegramClient

from src.web import MessageSender
import logging
from aiohttp import web
from telethon import events
from src.ban_utils import ban
from src.notify_admins import notify_admins
from src.read_acknowledge_utils import read_acknowledge
from src.scrapper import save_outgoing, save_incoming

config = Config()
def create_telegram_client(session_name, phone):
    client = TelegramClient(session_name, config.api_id, config.api_hash)
    client.connect()
    client.start(phone=phone)
    return client

def add_event_handlers(client):
    client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    client.add_event_handler(notify_admins, events.NewMessage(outgoing=True, pattern='!n', forwards=False))


client2 = create_telegram_client('session/alex2', config.telephone)
client = create_telegram_client('session/alex', config.telephone2)

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
