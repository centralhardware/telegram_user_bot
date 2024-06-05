import logging

import google.generativeai as genai

from config import config

genai.configure(api_key=config.gemini_api_key)
model = genai.GenerativeModel(model_name='gemini-1.5-flash')


async def answer(event):
    query = event.raw_text.replace('!ai', '')
    response = model.generate_content(f"ответь на языке вопроса коротко максимально аргументировано на следующее сообщение, добавиь в конце ремарку какой версией AI это сообщение сгенерировано: {query}")
    logging.info(f"ask ai {query} answer {response.text}")
    await event.client.delete_messages(event.chat, message_ids=[event.message.id])
    if event.message.reply_to_msg_id is not None:
        await event.client.send_message(event.chat, response.text, reply_to=event.message.reply_to_msg_id)
    else:
        await event.client.send_message(event.chat, response.text, reply_to=event.message.id)