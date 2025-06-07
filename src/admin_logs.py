import json
import logging

from telethon.tl.functions.channels import GetAdminLogRequest

from username_utils import extract_usernames
from clickhouse_utils import get_clickhouse_client
from utils import remove_empty_and_none

clickhouse = get_clickhouse_client()


def get_last_id_from_clickhouse(chat_id):
    result = clickhouse.query(
        """
        SELECT max(event_id) AS last_id
        FROM telegram_user_bot.admin_actions2
        WHERE chat_id = %(chat_id)s
    """,
        parameters={"chat_id": chat_id},
    ).result_rows
    return result[0][0] if result and result[0][0] is not None else 0


async def fetch_channel_actions(client, chat_id):
    last_id = get_last_id_from_clickhouse(chat_id)
    channel = await client.get_entity(chat_id)
    chat_usernames = extract_usernames(channel)
    max_id = last_id
    new_last_id = last_id
    all_data = []

    while True:
        events = await client(
            GetAdminLogRequest(
                channel=channel, q="", min_id=max_id + 1, max_id=0, limit=100
            )
        )

        if not events.events:
            break

        usernames_map = {}
        title_map = {}
        for u in events.users:
            title_map[u.id] = f"{u.first_name or ''} {u.last_name or ''}".strip()
            usernames_map[u.id] = extract_usernames(u)

        chat_map = {}
        for chat in events.chats:
            chat_map[chat.id] = extract_usernames(chat)

        for entry in events.events:
            eid = entry.id
            user_id = getattr(entry.user_id, "user_id", entry.user_id)
            action_type = type(entry.action).__name__.removeprefix(
                "ChannelAdminLogEventAction"
            )
            message = json.dumps(
                remove_empty_and_none(entry.action.to_dict()),
                default=str,
                ensure_ascii=False,
            )
            all_data.append(
                [
                    eid,
                    chat_id,
                    action_type,
                    user_id or 0,
                    entry.date,
                    message,
                    usernames_map.get(user_id) or chat_map.get(user_id, []),
                    chat_usernames,
                    channel.title,
                    title_map.get(user_id, ""),
                ]
            )

            if eid > new_last_id:
                new_last_id = eid

        if len(events.events) < 100:
            break
        else:
            max_id = max(e.id for e in events.events)

    if all_data:
        clickhouse.insert(
            "telegram_user_bot.admin_actions2",
            all_data,
            [
                "event_id",
                "chat_id",
                "action_type",
                "user_id",
                "date",
                "message",
                "usernames",
                "chat_usernames",
                "chat_title",
                "user_title",
            ],
        )
        logging.info(
            "[%s] Inserted %d entries. Last ID: %d",
            channel.title,
            len(all_data),
            new_last_id,
        )
