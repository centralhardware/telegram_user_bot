import asyncio
import logging
import threading

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from flask import Flask, jsonify
from telethon import events, functions

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


def create_client(session_name: str) -> TelegramClient:
    """Create a Telegram client using the global config."""
    return TelegramClient(session_name, config.api_id, config.api_hash)


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
    main_client = create_client("session/alex")
    second_client = create_client("session/alex2")

    main_client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    main_client.add_event_handler(save_deleted, events.MessageDeleted())
    main_client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    second_client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    second_client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    second_client.add_event_handler(save_deleted, events.MessageDeleted())

    main_client.add_event_handler(handle_catbot_trigger, events.NewMessage())

    started_clients = []

    try:
        await main_client.start(phone=config.telephone)
        started_clients.append(main_client)
    except Exception as exc:
        logging.error("Failed to start main client: %s", exc)

    try:
        await second_client.start(phone=config.telephone_second)
        started_clients.append(second_client)
    except Exception as exc:
        logging.error("Failed to start second client: %s", exc)

    if not started_clients:
        logging.error("No telegram clients could be started.")
        return

    scheduler = AsyncIOScheduler()

    chat_ids = [int(cid.strip()) for cid in config.chat_ids if cid.strip().isdigit()]
    if main_client in started_clients:
        for chat_id in chat_ids:
            scheduler.add_job(
                fetch_channel_actions,
                "interval",
                minutes=1,
                args=[main_client, chat_id],
            )
        scheduler.add_job(
            fetch_user_sessions, "interval", minutes=1, args=[main_client]
        )

    scheduler.add_job(flush_incoming_batch, "interval", seconds=10)
    scheduler.start()

    for client in started_clients:
        await client(
            functions.account.SetContentSettingsRequest(sensitive_enabled=True)
        )

    await asyncio.gather(*(c.run_until_disconnected() for c in started_clients))


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.info("start application")

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    asyncio.run(run_telegram_clients())


if __name__ == "__main__":
    main()
