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
                where chat_id=-1001633660171 and has(tokens(lowerUTF8(message)), lowerUTF8(%(word)s)) and not startsWith(message, '!top ')
                group by user_id
                limit 10
                UNION ALL
                select 428985392, count(*) as count
                from telegram_messages_new
                where id=-1001633660171 and has(tokens(lowerUTF8(message)), lowerUTF8(%(word)s)) and not startsWith(message, '!top '))
            order by count desc
            limit 10
    """, {"word": word})
    msg = ""
    for row in res.result_rows:
        if row[1] == 0: continue
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
            first_name=''
            last_name=''

        msg = msg + f"{res.result_rows.index(row) + 1}: {first_name} {last_name} {username} - {row[1]}\n"

    await event.client.send_message(event.chat.id, msg, reply_to=event.message.id)
