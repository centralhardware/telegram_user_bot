import clickhouse_connect

from config import config
from main import create_telegram_client

clickhouse = clickhouse_connect.get_client(host=config.db_host, database=config.db_database, port=8123,
                                           username=config.db_user, password=config.db_password)
client2 = create_telegram_client('session/alex2', config.telephone2)


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
        user = await event.client.get_entity(row[0])
        if user.usernames is None:
            username = user.username
        else:
            username = user.usernames[0].username

        msg = msg + f"{res.result_rows.index(row) + 1}: {user.first_name} {user.last_name} {username} - {row[1]}\n"

    await client2.send_message(event.chat, msg, reply_to=event.message.id)
