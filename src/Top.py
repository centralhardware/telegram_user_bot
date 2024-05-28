import clickhouse_connect

from config import config

clickhouse = clickhouse_connect.get_client(host=config.db_host, database=config.db_database, port=8123,
                                           username=config.db_user, password=config.db_password)



async def top(event):
    word = event.raw_text.split(" ")[1]
    res = clickhouse.query("""
            select any(user_id), count(*) as count
            from chats_log
            where chat_id=-1001633660171 and has(tokens(message), %(word)s)
            group by user_id
            order by count(*) desc
            limit 10
    """, {"word": word})
    msg = ""
    for row in res.result_rows:
        i = 1
        user = await event.client.get_entity(row[0])
        if user.usernames is None:
            username = user.username
        else:
            username = user.usernames[0].username

        msg = msg + f"{i}: {username} - {row[1]}\n"
        i=i+1

    await event.client.send_message(event.chat, msg)



