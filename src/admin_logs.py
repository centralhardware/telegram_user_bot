import json
import logging

import clickhouse_connect
from telethon.tl.functions.channels import GetAdminLogRequest

from config import config

clickhouse = clickhouse_connect.get_client(host=config.db_host, database=config.db_database, port=8123,
                                           username=config.db_user, password=config.db_password,
                                           settings={'async_insert': '1', 'wait_for_async_insert': '0'})


def get_last_id_from_clickhouse(chat_id):
    result = clickhouse.query(f"""
        SELECT max(event_id) AS last_id
        FROM telegram_user_bot.admin_actions2
        WHERE chat_id = %(chat_id)s
    """, parameters={"chat_id": chat_id}).result_rows
    return result[0][0] if result and result[0][0] is not None else 0


async def fetch_channel_actions(client, chat_id):
    last_id = get_last_id_from_clickhouse(chat_id)
    channel = await client.get_entity(chat_id)
    max_id = last_id
    new_last_id = last_id
    all_data = []

    while True:
        events = await client(GetAdminLogRequest(
            channel=channel,
            q='',
            min_id=max_id + 1,
            max_id=0,
            limit=100
        ))

        if not events.events:
            break

        user_map = {}
        for u in events.users:
            usernames = []
            if hasattr(u, "username") and u.username is not None:
                usernames.append(u.username)
            elif hasattr(u, "usernames") and u.usernames is not None:
                for username in u.usernames:
                    usernames.append(username)
                    user_map[u.id] = usernames


        chat = events.chats[0]
        usernames = []
        if hasattr(chat, "username") and chat.username is not None:
            usernames.append(chat.username)
        elif hasattr(chat, "usernames") and chat.usernames is not None:
            for username in chat.usernames:
                usernames.append(username)

        for entry in events.events:
            eid = entry.id
            user_id = getattr(entry.user_id, 'user_id', entry.user_id)
            action_type = type(entry.action).__name__
            message = json.dumps(
                remove_empty_and_none(entry.action.to_dict()),
                default=str,
                ensure_ascii=False
            )
            all_data.append([
                eid,
                chat_id,
                action_type,
                user_id or 0,
                entry.date,
                message,
                user_map.get(user_id, []),
                usernames
            ])

            if eid > new_last_id:
                new_last_id = eid

        if len(events.events) < 100:
            break
        else:
            max_id = max(e.id for e in events.events)

    if all_data:
        clickhouse.insert('telegram_user_bot.admin_actions2', all_data, [
            'event_id',
            'chat_id',
            'action_type',
            'user_id',
            'date',
            'message',
            'usernames',
            'chat_usernames'
        ])
        logging.info(f"[{usernames}] Inserted {len(all_data)} entries. Last ID: {new_last_id}")

def remove_empty_and_none(obj):
    if isinstance(obj, dict):
        cleaned = {
            k: remove_empty_and_none(v)
            for k, v in obj.items()
            if v is not None
        }
        return {k: v for k, v in cleaned.items() if v not in (None, {}, [])}
    elif isinstance(obj, list):
        cleaned = [remove_empty_and_none(v) for v in obj if v is not None]
        return [v for v in cleaned if v not in (None, {}, [])]
    else:
        return obj