import asyncio
import logging
import os
import threading

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask, jsonify
from telethon import events

from config import config
from notify_admins import notify_admins
from scrapper import save_outgoing, save_incoming, save_deleted
from TelegramUtils import create_telegram_client
from admin_logs import fetch_channel_actions
from fetch_sessions import fetch_user_sessions

app = Flask(__name__)


@app.route("/health")
def health():
    resp = jsonify(health="healthy")
    resp.status_code = 200
    return resp


def run_flask():
    # Disable default werkzeug request logging
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    app.run(host='0.0.0.0', port=80, use_reloader=False)


async def run_telegram_clients():
    client = create_telegram_client('session/alex', config.telephone)

    client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    client.add_event_handler(save_deleted, events.MessageDeleted())
    client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    client.add_event_handler(notify_admins, events.NewMessage(outgoing=True, pattern='!n', forwards=False))

    scheduler = AsyncIOScheduler()

    chat_ids_str = os.getenv("TELEGRAM_CHAT_IDS", "")
    chat_ids = [int(cid.strip()) for cid in chat_ids_str.split(",") if cid.strip().isdigit()]
    for chat_id in chat_ids:
        scheduler.add_job(fetch_channel_actions, 'interval', minutes=1, args=[client, chat_id])

    scheduler.add_job(fetch_user_sessions, "interval", minutes=1, args=[client])
    scheduler.start()

    await client.start()

    await client.run_until_disconnected()


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.info('start application')

    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Запускаем Telegram клиентов в asyncio
    asyncio.run(run_telegram_clients())

if __name__ == '__main__':
    main()
