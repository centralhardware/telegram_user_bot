import logging

import google.generativeai as genai

from config import config
from TelegramUtils import client2

genai.configure(api_key=config.gemini_api_key)


async def answer(event):
    model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')
    query = event.raw_text.replace('!ai', '')
    response = model.generate_content(
        f"Представь что ты самый лучший в мире эксперт в ИТ и ответь на заданный тебе вопрос одним сообщением аргументировано на языке вопроса стараясь чтобы все было понятно после прочтения минимизируй размер ответа без потери смысла старайся использовать минимальной количество строчек но сохраняя принятое форматирование кода: {query}")
    logging.info(f"ask ai {query} answer {response.text}")
    if event.chat_id == -1001633660171:
        if event.message.reply_to_msg_id is not None:
            await client2.send_message(event.chat.id, response.text + '\n\n gemini AI',
                               reply_to=event.message.reply_to_msg_id)
        else:
            await client2.send_message(event.chat.id, response.text + '\n\n gemini AI', reply_to=event.message.id)
    else:
        await event.client.edit_message(event.message, response.text + '\n\n gemini AI')
