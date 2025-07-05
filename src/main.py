import asyncio
import logging
import threading

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask, jsonify
from telethon import events

from config import config
from scrapper import (
    save_outgoing,
    save_incoming,
    save_deleted,
    flush_incoming_batch,
)
from telethon import TelegramClient
from admin_logs import fetch_channel_actions
from fetch_sessions import fetch_user_sessions
from auto_catbot import handle_catbot_trigger

app = Flask(__name__)


@app.route("/health")
def health():
    resp = jsonify(health="healthy")
    resp.status_code = 200
    return resp


def run_flask():
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    app.run(host="0.0.0.0", port=80, use_reloader=False)


async def run_telegram_clients():
    client = TelegramClient("session/alex", config.api_id, config.api_hash)

    client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    client.add_event_handler(save_deleted, events.MessageDeleted())
    client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    client.add_event_handler(handle_catbot_trigger, events.NewMessage())

    scheduler = AsyncIOScheduler()

    chat_ids = [
        int(cid.strip()) for cid in config.chat_ids if cid.strip().isdigit()
    ]
    for chat_id in chat_ids:
        scheduler.add_job(
            fetch_channel_actions, "interval", minutes=1, args=[client, chat_id]
        )

    scheduler.add_job(fetch_user_sessions, "interval", minutes=1, args=[client])
    scheduler.add_job(flush_incoming_batch, "interval", seconds=1)
    scheduler.start()

    await client.start(phone=config.telephone)

    await client.run_until_disconnected()


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.info("start application")

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    asyncio.run(run_telegram_clients())


if __name__ == "__main__":
    main()
