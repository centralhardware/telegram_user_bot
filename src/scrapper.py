import json
import logging
from datetime import datetime
from typing import List

from admin_utils import get_admins
from username_utils import extract_usernames
from clickhouse_utils import get_clickhouse_client
from utils import remove_empty_and_none

# Batch for incoming messages
INCOMING_BATCH_SIZE = 1000
incoming_batch: List[List] = []


async def save_outgoing(event):
    clickhouse = get_clickhouse_client()
    chat_title = ""

    if hasattr(event.chat, "title"):
        chat_title = event.chat.title
    else:
        if (
            event.chat is not None
            and event.chat.bot
            and hasattr(event.chat, "first_name")
        ):
            chat_title = event.chat.first_name

    chat = await event.get_chat()
    chat_id = extract_usernames(chat)

    if hasattr(chat, "first_name"):
        last_name = chat.last_name if chat.last_name is not None else ""
        chat_title = chat.first_name + " " + last_name

    if chat_title == "":
        chat_title = chat_id[0]

    admins = await get_admins(event.chat, event.client)
    message_dict = remove_empty_and_none(event.message.to_dict())
    message_json = json.dumps(message_dict, default=str, ensure_ascii=False)
    logging.info(
        "outgoing %12d %-25s %s reply to %s",
        event.message.id,
        chat_title[:20],
        event.raw_text,
        event.message.reply_to_msg_id,
    )
    data = [
        [
            datetime.now(),
            event.raw_text,
            message_json,
            chat_title,
            chat_id,
            event.chat_id,
            admins,
            event.message.id,
            event.message.reply_to_msg_id or 0,
            event.sender_id or 0,
        ]
    ]
    clickhouse.insert(
        "telegram_user_bot.telegram_messages_new",
        data,
        [
            "date_time",
            "message",
            "raw",
            "title",
            "usernames",
            "id",
            "admins2",
            "message_id",
            "reply_to",
            "user_id",
        ],
    )


def save_inc(data):
    clickhouse = get_clickhouse_client()
    clickhouse.insert(
        "telegram_user_bot.chats_log",
        data,
        [
            "date_time",
            "chat_title",
            "chat_id",
            "username",
            "chat_usernames",
            "first_name",
            "second_name",
            "user_id",
            "message_id",
            "message",
            "reply_to",
        ],
    )


def save_del(data):
    clickhouse = get_clickhouse_client()
    clickhouse.insert(
        "telegram_user_bot.deleted_log", data, ["date_time", "chat_id", "message_id"]
    )


def flush_incoming_batch():
    if incoming_batch:
        save_inc(incoming_batch)
        incoming_batch.clear()


async def save_incoming(event):
    if event.chat_id >= 0 or event.is_private is True or event.message.sender is None:
        return

    usernames = extract_usernames(event.message.sender)
    chat_usernames = extract_usernames(event.chat)
    try:
        first_name = event.message.sender.first_name
        last_name = event.message.sender.last_name
    except Exception:
        first_name = None
        last_name = None

    message_content = event.raw_text
    if event.raw_text == "":
        try:
            message_dict = remove_empty_and_none(event.message.to_dict())
            message_content = json.dumps(message_dict, default=str, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error serializing empty incoming message: {e}")
            message_content = "[Error serializing message]"

    logging.info(
        "incoming %12d %-25s %s reply to %s",
        event.message.id,
        event.chat.title[:20],
        message_content,
        event.message.reply_to_msg_id,
    )

    incoming_batch.append(
        [
            datetime.now(),
            event.chat.title,
            event.chat_id,
            usernames,
            chat_usernames,
            first_name,
            last_name,
            event.message.sender.id,
            event.message.id,
            message_content,
            event.message.reply_to_msg_id,
        ]
    )
    if len(incoming_batch) >= INCOMING_BATCH_SIZE:
        flush_incoming_batch()


async def save_deleted(event):
    if event.chat_id is None:
        return

    clickhouse = get_clickhouse_client()
    for msg_id in event.deleted_ids:
        save_del([[datetime.now(), event.chat_id, msg_id]])

        try:
            chat_title = clickhouse.query(
                """
            SELECT chat_title
            FROM telegram_user_bot.chats_log
            WHERE chat_id = {chat_id:Int64}
            ORDER BY date_time DESC
            LIMIT 1
            """,
                {"chat_id": event.chat_id},
            ).result_rows[0][0]
        except Exception:
            chat_title = event.chat_id

        try:
            message = clickhouse.query(
                """
            SELECT message
            FROM telegram_user_bot.chats_log
            WHERE chat_id = {chat_id:Int64} and message_id = {message_id:Int64}
            LIMIT 1
            """,
                {"chat_id": event.chat_id, "message_id": msg_id},
            ).result_rows[0][0]
        except Exception:
            message = msg_id

        logging.info(
            "deleted  %12d %-25s %s",
            msg_id,
            str(chat_title)[:20],
            message,
        )
