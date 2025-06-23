import asyncio

CHAT_ID = -1001633660171
TRIGGER_TEXT = "#грбнпндельник"
RESPONSE_TEXT = "/start@y9catbot"


async def handle_catbot_trigger(event):
    if event.chat_id != CHAT_ID:
        return
    if event.raw_text.strip() != TRIGGER_TEXT:
        return

    response = await event.reply(RESPONSE_TEXT)
    await asyncio.sleep(0)
    await event.client.delete_messages(event.chat_id, response.id)
