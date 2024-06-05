import logging

import google.generativeai as genai

from config import config

genai.configure(api_key=config.gemini_api_key)
model = genai.GenerativeModel(model_name='gemini-1.5-flash')

async def answer(event):
    reply_msg = await event.client.get_messages(event.chat_id, ids=event.message.reply_to_msg_id)
    logging.info(f"ask ai {reply_msg.raw_text}")
    response = model.generate_content(f"ответь на языке вопроса коротко максимально аргументировано на следующее сообщение, добавиь в конце ремарку какой версией AI это сообщение сгенерировано: {reply_msg.raw_text}")
    logging.info(f"ask ai {reply_msg.raw_text} answer {response.text}")
    await event.client.edit_message(event.message, response.text)