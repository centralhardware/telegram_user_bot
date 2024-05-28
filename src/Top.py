import clickhouse_connect

from config import config

clickhouse = clickhouse_connect.get_client(host=config.db_host, database=config.db_database, port=8123,
                                           username=config.db_user, password=config.db_password)


async def top(event):
    word = event.raw_text.split(" ")[1]
    res = clickhouse.query("""
            select *
            from (select any(user_id), count(*) as count
                from chats_log
                where chat_id=-1001633660171 and has(tokens(lowerUTF8(message)), %(word)s)
                group by user_id
                limit 10
                UNION ALL
                select 428985392, count(*) as count
                from telegram_messages_new
                where id=-1001633660171 and has(tokens(lowerUTF8(message)), %(word)s))
            order by count desc 
    """, {"word": word})
    msg = ""
    for row in res.result_rows:
        if row[1] == 0: pass
        user = await event.client.get_entity(row[0])
        if user.usernames is None:
            username = user.username
        else:
            username = user.usernames[0].username

        msg = msg + f"{res.result_rows.index(row) + 1}: {username} - {row[1]}\n"

    await event.client.send_message(event.chat, msg, reply_to=event.message.id)
