import json
import logging
from datetime import datetime

import clickhouse_connect
from telethon.tl.functions.channels import GetAdminLogRequest

from config import config

clickhouse = clickhouse_connect.get_client(host=config.db_host, database=config.db_database, port=8123,
                                           username=config.db_user, password=config.db_password,
                                           settings={'async_insert': '1', 'wait_for_async_insert': '0'})


def get_last_id_from_clickhouse(chat_id):
    result = clickhouse.query(f"""
        SELECT max(event_id) AS last_id
        FROM telegram_user_bot.admin_actions
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

        for entry in events.events:
            eid = entry.id
            user_id = getattr(entry.user_id, 'user_id', entry.user_id)
            action_type = type(entry.action).__name__
            message = json.dumps(entry.action.to_dict(), default=str)

            all_data.append([
                eid,
                chat_id,
                action_type,
                user_id or 0,
                entry.date,
                message
            ])

            if eid > new_last_id:
                new_last_id = eid

        if len(events.events) < 100:
            break
        else:
            max_id = max(e.id for e in events.events)

    if all_data:
        clickhouse.insert('telegram_user_bot.admin_actions', all_data, [
            'event_id',
            'chat_id',
            'action_type',
            'user_id',
            'date',
            'message'
        ])
        logging.info(f"[{datetime.utcnow()}] [{chat_id}] Inserted {len(all_data)} entries. Last ID: {new_last_id}")
    else:
        logging.info(f"[{datetime.utcnow()}] [{chat_id}] No new entries.")