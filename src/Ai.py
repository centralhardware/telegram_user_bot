import logging

import google.generativeai as genai

from config import config

genai.configure(api_key=config.gemini_api_key)
model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')


async def answer(event):
    query = event.raw_text.replace('!ai', '')
    response = model.generate_content(f"Представь что ты самый лучший в мире эксперт в ИТ и ответь на заданный тебе вопрос одним сообщением аргументировано на языке вопроса стараясь чтобы все было понятно после прочтения минимизируй размер ответа без потери смысла старайся использовать минимальной количество строчек но сохраняя принятое форматирование кода: {query}")
    logging.info(f"ask ai {query} answer {response.text}")
    if event.message.reply_to_msg_id is not None:
        await event.client.send_message(event.chat, response.text + '\n\n gemini AI', reply_to=event.message.reply_to_msg_id)
    else:
        await event.client.send_message(event.chat, response.text + '\n\n gemini AI', reply_to=event.message.id)