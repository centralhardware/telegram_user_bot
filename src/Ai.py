import logging
import textwrap

import google.generativeai as genai

from config import config
from TelegramUtils import client2

genai.configure(api_key=config.gemini_api_key)


async def answer(event):
    model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')
    query = event.raw_text.replace('!ai', '')
    response = model.generate_content(
        f"ты лаконичный ассистент, который отвечает точно: {query}")
    try:
        res = textwrap.wrap(response.text, 4000, break_long_words=True, replace_whitespace=False)
    except BaseException:
        try:
            await client2.send_message(event.chat_id, response.prompt_feedback, reply_to=event.message.id)
        except BaseException:
            pass
        try:
            await client2.send_message(event.chat_id, response.candidates[0].finish_reason, reply_to=event.message.id)
        except BaseException:
            pass
        try:
            await client2.send_message(event.chat_id, response.candidates[0].safety_ratings, reply_to=event.message.id)
        except BaseException:
            pass
        return
    logging.info(f"ask ai {query} answer {response.text}")
    if event.chat_id == -1001633660171:
        if event.message.reply_to_msg_id is not None:
            for line in res:
                await client2.send_message(event.chat.id, line + '\n\n gemini AI',
                                           reply_to=event.message.reply_to_msg_id)
        else:
            for line in res:
                await client2.send_message(event.chat.id, line + '\n\n gemini AI', reply_to=event.message.id)
    else:
        for line in res:
            await event.client.edit_message(event.message, line + '\n\n gemini AI')
