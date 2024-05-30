import clickhouse_connect

from config import config

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
        user = await event.client.get_entity(row[0])
        if user.usernames is None:
            username = user.username
        else:
            username = user.usernames[0].username
        msg = msg + f"{res.result_rows.index(row) + 1} : {user.first_name} {user.last_name} {username} - {row[1]}\n"

    await event.client.send_message(event.chat, msg, reply_to=event.message.id)
