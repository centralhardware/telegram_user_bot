import asyncio
import re

CHAT_ID = -1001633660171
HASHTAG_PREFIX = "#грбн"
RESPONSE_TEXT = "/start@y9catbot"


async def handle_catbot_trigger(event):
    if event.chat_id != CHAT_ID:
        return

    text = event.raw_text.strip()
    if not re.search(r"\B" + re.escape(HASHTAG_PREFIX) + r"\S*", text):
        return

    response = await event.reply(RESPONSE_TEXT)
    await asyncio.sleep(0)
    await event.client.delete_messages(event.chat_id, response.id)
