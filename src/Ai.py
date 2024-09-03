async def answer(event):
    await event.client.send_message(event.chat.id, 'а все', reply_to=event.message.id)