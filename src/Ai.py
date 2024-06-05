import logging

import google.generativeai as genai

from config import config

genai.configure(api_key=config.gemini_api_key)
model = genai.GenerativeModel(model_name='gemini-1.5-flash')


async def answer(event):
    query = event.raw_text.split(':')[1]
    response = model.generate_content(f"ответь на языке вопроса коротко максимально аргументировано на следующее сообщение, добавиь в конце ремарку какой версией AI это сообщение сгенерировано: {query}")
    logging.info(f"ask ai {query} answer {response.text}")
    await event.client.send_message(event.chat, response.text, reply_to=event.message.id)