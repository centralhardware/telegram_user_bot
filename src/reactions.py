import logging
from datetime import datetime

import clickhouse_connect
from telethon.tl.types import UpdateMessageReactions

from config import config

clickhouse = clickhouse_connect.get_client(host=config.db_host, database=config.db_database, port=8123,
                                           username=config.db_user, password=config.db_password,
                                           settings={'async_insert': '1', 'wait_for_async_insert': '0'})

async def reaction_handler(event):
    if not isinstance(event, UpdateMessageReactions):
        return

    msg_id = event.msg_id
    chat_id = getattr(event.peer, 'channel_id', None) or getattr(event.peer, 'chat_id', None)
    logging.info(f"📩 Message ID {msg_id} in Chat {chat_id} got updated reactions")


    rows = []
    if not event.reactions or not event.reactions.results:
        logging.info(f"❌ All reactions removed from message {msg_id} in chat {chat_id}")
        rows.append([
            msg_id,
            chat_id,
            '',
            0,
            datetime.utcnow()
        ])
    else:
        for reaction in event.reactions.results:
            reaction_str = getattr(reaction.reaction, 'emoticon', str(reaction.reaction))
            count = reaction.count
            logging.info(f" → Reaction: {reaction_str} × {count}")
            rows.append([
                msg_id,
                chat_id,
                reaction_str,
                count,
                datetime.utcnow()
            ])

    if rows:
        clickhouse.insert('telegram_user_bot.telegram_reactions',
                          rows,
                          [
                              'message_id',
                              'chat_id',
                              'reaction',
                              'count',
                              'date'
                          ])