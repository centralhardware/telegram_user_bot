import asyncio
import logging
import threading

from flask import Flask, jsonify
from telethon import events

from config import config
from notify_admins import notify_admins
from scrapper import save_outgoing, save_incoming, save_deleted
from TelegramUtils import create_telegram_client

app = Flask(__name__)
@app.route("/health")
def health():
    resp = jsonify(health="healthy")
    resp.status_code = 200
    return resp

def run_flask():
    app.run(host='0.0.0.0', port=80)

async def run_telegram_clients():
    client = create_telegram_client('session/alex', config.telephone)

    # Добавляем обработчики событий для клиента 1
    client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    client.add_event_handler(save_deleted, events.MessageDeleted())
    client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    client.add_event_handler(notify_admins, events.NewMessage(outgoing=True, pattern='!n', forwards=False))

    # Запускаем клиентов
    await client.start()

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