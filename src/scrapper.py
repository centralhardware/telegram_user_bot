import atexit
import json
import logging
import difflib
from datetime import datetime
from typing import List

from telethon import utils
from admin_utils import get_admins
from username_utils import extract_usernames
from clickhouse_utils import get_clickhouse_client
from utils import remove_empty_and_none, colorize

incoming_batch: List[List] = []
edited_batch: List[List] = []
deleted_batch: List[List] = []
reactions_batch: List[List] = []


async def save_outgoing(event):
    clickhouse = get_clickhouse_client()
    chat = await event.get_chat()
    chat_usernames = extract_usernames(chat)
    chat_title = utils.get_display_name(chat)
    if not chat_title:
        if chat_usernames:
            chat_title = chat_usernames[0]
        else:
            chat_title = str(event.chat_id)

    admins = await get_admins(event.chat, event.client)
    message_dict = remove_empty_and_none(event.message.to_dict())
    message_json = json.dumps(message_dict, default=str, ensure_ascii=False)
    logging.info(
        colorize("outgoing", "outgoing %12d %-25s %s reply to %s"),
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
            chat_usernames,
            event.chat_id,
            admins,
            event.message.id,
            event.message.reply_to_msg_id or 0,
            event.client._self_id
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
            "client_id"
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
            "client_id"
        ],
    )


def save_del(data):
    clickhouse = get_clickhouse_client()
    clickhouse.insert(
        "telegram_user_bot.deleted_log",
        data,
        ["date_time", "chat_id", "message_id", "client_id"],
    )


def flush_batches():
    incoming_count = len(incoming_batch)
    edited_count = len(edited_batch)
    deleted_count = len(deleted_batch)
    reactions_count = len(reactions_batch)

    if incoming_batch:
        save_inc(incoming_batch)
        incoming_batch.clear()

    if edited_batch:
        clickhouse = get_clickhouse_client()
        clickhouse.insert(
            "telegram_user_bot.edited_log",
            edited_batch,
            [
                "date_time",
                "chat_id",
                "message_id",
                "original_message",
                "message",
                "diff",
                "user_id",
                "client_id",
            ],
        )
        edited_batch.clear()

    if deleted_batch:
        save_del(deleted_batch)
        deleted_batch.clear()

    if reactions_batch:
        clickhouse = get_clickhouse_client()
        clickhouse.insert(
            "telegram_user_bot.reactions_log",
            reactions_batch,
            [
                "date_time",
                "chat_id",
                "message_id",
                "reactions",
                "client_id",
            ],
        )
        reactions_batch.clear()

    if incoming_count or edited_count or deleted_count or reactions_count:
        logging.info(
            "Saved %s incoming, %s edited, %s deleted messages, %s reaction updates",
            incoming_count,
            edited_count,
            deleted_count,
            reactions_count,
        )


async def save_incoming(event):
    if event.chat_id >= 0 or event.is_private is True or event.message.sender is None:
        return

    usernames = extract_usernames(event.message.sender)
    chat_usernames = extract_usernames(event.chat)
    try:
        first_name = event.message.sender.first_name or ""
        last_name = event.message.sender.last_name or ""
    except Exception:
        first_name = ""
        last_name = ""

    message_content = event.raw_text
    if not message_content:
        try:
            message_dict = remove_empty_and_none(event.message.to_dict())
            message_content = json.dumps(message_dict, default=str, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error serializing empty incoming message: {e}")
            message_content = "[Error serializing message]"

    logging.info(
        colorize("incoming", "incoming %12d %-25s %s reply to %s"),
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
            event.message.reply_to_msg_id or 0,
            event.client._self_id
        ]
    )


async def save_edited(event):
    if event.chat_id is None:
        return

    message_content = event.raw_text

    clickhouse = get_clickhouse_client()

    try:
        original = clickhouse.query(
            """
        SELECT message
        FROM telegram_user_bot.edited_log
        WHERE chat_id = {chat_id:Int64} AND message_id = {message_id:Int64}
        ORDER BY date_time DESC
        LIMIT 1
        """,
            {"chat_id": event.chat_id, "message_id": event.message.id},
        ).result_rows[0][0]
    except Exception:
        original = ""

    if not original:
        try:
            original = clickhouse.query(
                """
            SELECT message
            FROM telegram_user_bot.chats_log
            WHERE chat_id = {chat_id:Int64} AND message_id = {message_id:Int64}
            ORDER BY date_time DESC
            LIMIT 1
            """,
                {"chat_id": event.chat_id, "message_id": event.message.id},
            ).result_rows[0][0]
        except Exception:
            original = ""

    if not original or not message_content or original == message_content:
        return

    diff = "\n".join(
        difflib.unified_diff(
            original.splitlines(),
            message_content.splitlines(),
            lineterm="",
        )
    )

    user_id = event.message.sender_id or 0

    edited_batch.append(
        [
            datetime.now(),
            event.chat_id,
            event.message.id,
            original,
            message_content,
            diff,
            user_id,
            event.client._self_id,
        ]
    )

    logging.info(
        colorize("edited", "edited   %12d %-25s \n%s"),
        event.message.id,
        getattr(event.chat, "title", "")[:20],
        diff,
    )


async def save_deleted(event):
    if event.chat_id is None:
        return

    clickhouse = get_clickhouse_client()
    for msg_id in event.deleted_ids:
        deleted_batch.append(
            [datetime.now(), event.chat_id, msg_id, event.client._self_id]
        )

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
            FROM telegram_user_bot.edited_log
            WHERE chat_id = {chat_id:Int64} AND message_id = {message_id:Int64}
            ORDER BY date_time DESC
            LIMIT 1
            """,
                {"chat_id": event.chat_id, "message_id": msg_id},
            ).result_rows[0][0]
        except Exception:
            try:
                message = clickhouse.query(
                    """
                SELECT message
                FROM telegram_user_bot.chats_log
                WHERE chat_id = {chat_id:Int64} AND message_id = {message_id:Int64}
                ORDER BY date_time DESC
                LIMIT 1
                """,
                    {"chat_id": event.chat_id, "message_id": msg_id},
                ).result_rows[0][0]
            except Exception:
                message = msg_id

        logging.info(
            colorize("deleted", "deleted  %12d %-25s %s"),
            msg_id,
            str(chat_title)[:20],
            message,
        )


async def save_reactions(event):
    """Save message reactions to database.

    This handler processes UpdateMessageReactions events from Telegram.
    It saves a snapshot of all current reactions for a message (without user info).
    """
    from telethon.tl.types import (
        UpdateMessageReactions,
        ReactionEmoji,
        ReactionCustomEmoji,
        MessagePeerReaction,
    )

    if not isinstance(event, UpdateMessageReactions):
        return

    chat_id = None

    if hasattr(event, 'peer'):
        from telethon.tl.types import PeerChannel, PeerChat, PeerUser
        peer = event.peer

        if isinstance(peer, PeerChannel):
            chat_id = -1000000000000 - peer.channel_id
        elif isinstance(peer, PeerChat):
            chat_id = -peer.chat_id
        elif isinstance(peer, PeerUser):
            chat_id = peer.user_id

    if chat_id is None:
        return

    message_id = event.msg_id
    client_id = event._client._self_id

    # Collect all current reactions (only the reaction itself, not who reacted)
    reactions_array = []

    if hasattr(event, 'reactions') and event.reactions:
        if hasattr(event.reactions, 'recent_reactions') and event.reactions.recent_reactions:
            for reaction_obj in event.reactions.recent_reactions:
                if isinstance(reaction_obj, MessagePeerReaction):
                    reaction_str = ""
                    if isinstance(reaction_obj.reaction, ReactionEmoji):
                        reaction_str = reaction_obj.reaction.emoticon
                    elif isinstance(reaction_obj.reaction, ReactionCustomEmoji):
                        reaction_str = f"custom_{reaction_obj.reaction.document_id}"

                    if reaction_str:
                        reactions_array.append(reaction_str)

    # Save the current snapshot of reactions
    reactions_batch.append([
        datetime.now(),
        chat_id,
        message_id,
        reactions_array,
        client_id,
    ])

    logging.info(
        colorize("reactions", "reactions  %12d chat %d: %d reactions"),
        message_id,
        chat_id,
        len(reactions_array),
    )


atexit.register(flush_batches)
