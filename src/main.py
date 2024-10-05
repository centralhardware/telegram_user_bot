import asyncio
import logging
import threading

from flask import Flask, jsonify
from telethon import events

from config import config
from notify_admins import notify_admins
from scrapper import save_outgoing, save_incoming, save_deleted
from Top import top
from Deleted import deleted
from TelegramUtils import create_telegram_client

app = Flask(__name__)
@app.route("/health")
def health():
    resp = jsonify(health="healthy")
    resp.status_code = 200
    return resp

def run_flask():
    app.run(host='0.0.0.0', port=config.port)

async def run_telegram_clients():
    client = create_telegram_client('session/alex', config.telephone)
    client2 = create_telegram_client('session/alex2', config.telephone2)

    # Добавляем обработчики событий для клиента 1
    client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    client.add_event_handler(save_deleted, events.MessageDeleted())
    client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    client.add_event_handler(notify_admins, events.NewMessage(outgoing=True, pattern='!n', forwards=False))

    # Добавляем обработчики событий для клиента 2
    client2.add_event_handler(top, events.NewMessage(outgoing=True, pattern='!top', forwards=False, chats=[-1001633660171]))
    client2.add_event_handler(top, events.NewMessage(incoming=True, pattern='!top', forwards=False, chats=[-1001633660171]))
    client2.add_event_handler(deleted, events.NewMessage(outgoing=True, pattern='!deleted', forwards=False, chats=[-1001633660171]))
    client2.add_event_handler(deleted, events.NewMessage(incoming=True, pattern='!deleted', forwards=False, chats=[-1001633660171]))

    # Запускаем клиентов
    await client.start()
    await client2.start()

    # Блокируем цикл до завершения клиентов
    await client.run_until_disconnected()
    await client2.run_until_disconnected()

def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info('start application')

    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Запускаем Telegram клиентов в asyncio
    asyncio.run(run_telegram_clients())

if __name__ == '__main__':
    main()