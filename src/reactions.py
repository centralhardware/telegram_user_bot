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

    reaction_list = []
    count_list = []

    if not event.reactions or not event.reactions.results:
        logging.info(" → All reactions removed")
    else:
        for reaction in event.reactions.results:
            reaction_str = getattr(reaction.reaction, 'emoticon', str(reaction.reaction))
            reaction_str = reaction_str.encode('utf-16', 'surrogatepass').decode('utf-16')
            count = reaction.count
            logging.info(f" → Reaction: {reaction_str} × {count}")
            reaction_list.append(reaction_str)
            count_list.append(count)

    row = [[
        msg_id,
        chat_id,
        reaction_list,
        count_list,
        datetime.utcnow()
    ]]

    clickhouse.insert('telegram_user_bot.reactions',
                      row,
                      [
                          'message_id',
                          'chat_id',
                          'reactions',
                          'counts',
                          'date'
                      ])
