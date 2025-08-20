import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import events, functions
from clickhouse_session import ClickHouseSession

from config import config
from scrapper import (
    save_outgoing,
    save_incoming,
    save_deleted,
    save_edited,
    flush_batches,
)
from telethon import TelegramClient
from admin_logs import fetch_channel_actions
from fetch_sessions import fetch_user_sessions
from auto_catbot import handle_catbot_trigger


def create_client(session_name: str, api_id: int, api_hash: str) -> TelegramClient:
    """Create a Telegram client using provided API credentials."""
    return TelegramClient(
        ClickHouseSession(session_name),
        api_id,
        api_hash,
        device_model="Telegram Android",
        app_version="10.5.1",
    )



async def run_telegram_clients():
    main_client = create_client("alex", config.api_id, config.api_hash)
    second_client = create_client("alex2", config.api_id_second, config.api_hash_second)

    main_client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    main_client.add_event_handler(save_deleted, events.MessageDeleted())
    main_client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    main_client.add_event_handler(save_edited, events.MessageEdited())
    second_client.add_event_handler(save_outgoing, events.NewMessage(outgoing=True))
    second_client.add_event_handler(save_incoming, events.NewMessage(incoming=True))
    second_client.add_event_handler(save_deleted, events.MessageDeleted())
    second_client.add_event_handler(save_edited, events.MessageEdited())

    main_client.add_event_handler(handle_catbot_trigger, events.NewMessage())

    started_clients = []

    try:
        await second_client.start(phone=config.telephone)
        main_client.session.save()
        started_clients.append(main_client)
    except Exception as exc:
        logging.error("Failed to start main client: %s", exc)

    try:
        await second_client.start(phone=config.telephone_second)
        second_client.session.save()
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

    scheduler.add_job(flush_batches, "interval", seconds=10)
    scheduler.start()

    for client in started_clients:
        await client(
            functions.account.SetContentSettingsRequest(sensitive_enabled=True)
        )

    async def run_client(client, label: str):
        try:
            await client.run_until_disconnected()
        except Exception as exc:
            logging.exception("%s client stopped due to error: %s", label, exc)

    client_labels = {main_client: "main", second_client: "second"}
    tasks = [
        asyncio.create_task(run_client(client, client_labels.get(client, "unknown")))
        for client in started_clients
    ]

    await asyncio.gather(*tasks)


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.info("start application")

    asyncio.run(run_telegram_clients())


if __name__ == "__main__":
    main()
