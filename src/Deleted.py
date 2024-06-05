import clickhouse_connect

from config import config
from TelegramUtils import client2

clickhouse = clickhouse_connect.get_client(host=config.db_host, database=config.db_database, port=8123,
                                           username=config.db_user, password=config.db_password)


async def deleted(event):
    res = clickhouse.query(
        """
        select user_id, count(user_id)
        from deleted_log deleted
        join (select * from chats_log where chat_id=-1001633660171) log on log.message_id = deleted.message_id
        where chat_id=-1001633660171
        group by user_id
        order by count(user_id) desc
        limit 10
        """
    )
    msg = ""
    for row in res.result_rows:
        try:
            user = await event.client.get_entity(row[0])
            if user.usernames is None:
                username = user.username
            else:
                username = user.usernames[0].username
            first_name = user.first_name
            last_name = user.last_name
        except Exception:
            username = row[0]

        msg = msg + f"{res.result_rows.index(row) + 1} : {first_name} {last_name} {username} - {row[1]}\n"

    await client2.send_message(event.chat.id, msg, reply_to=event.message.id)
