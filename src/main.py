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
    main_client = TelegramClient("session/alex", config.api_id, config.api_hash)
    second_client = None

    # Use the same application credentials for the optional second account.
    if config.telephone_second:
        second_client = TelegramClient(
            "session/alex2",
            config.api_id,
            config.api_hash,
        )

    # Handlers for the primary client
    main_client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    main_client.add_event_handler(save_deleted, events.MessageDeleted())
    # Incoming messages are handled either by the secondary client or the
    # primary one when no secondary client is configured.
    if second_client:
        second_client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    else:
        main_client.add_event_handler(save_incoming, events.NewMessage(incoming=True))

    main_client.add_event_handler(handle_catbot_trigger, events.NewMessage())

    scheduler = AsyncIOScheduler()

    chat_ids = [int(cid.strip()) for cid in config.chat_ids if cid.strip().isdigit()]
    for chat_id in chat_ids:
        scheduler.add_job(
            fetch_channel_actions, "interval", minutes=1, args=[main_client, chat_id]
        )
    scheduler.add_job(fetch_user_sessions, "interval", minutes=1, args=[main_client])
    scheduler.add_job(flush_incoming_batch, "interval", seconds=10)
    scheduler.start()

    await main_client.start(phone=config.telephone)
    if second_client:
        await second_client.start(phone=config.telephone_second)

    if second_client:
        await asyncio.gather(
            main_client.run_until_disconnected(),
            second_client.run_until_disconnected(),
        )
    else:
        await main_client.run_until_disconnected()


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.info("start application")

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    asyncio.run(run_telegram_clients())


if __name__ == "__main__":
    main()
