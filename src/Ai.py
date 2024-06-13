import logging
import textwrap

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from telethon.helpers import TotalList

from config import config
from TelegramUtils import client2

genai.configure(api_key=config.gemini_api_key)

async def get_messages(message, client, res = [], count = 0):
    reply = await client.get_messages(message.chat.id, ids = message.reply_to_msg_id)
    if isinstance(reply, TotalList) or count >= 15:
        return res

    res.append(reply.raw_text)
    count = count+1
    return await get_messages(reply, client, res, count)


async def answer(event):
    model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest',
                                  system_instruction='ты лаконичный ассистент, который отвечает точно')
    query = event.raw_text.replace('!ai', '')

    context = await get_messages(event.message, event.client)
    context.reverse()
    chat = model.start_chat(history = context)
    response = chat.send_message(
        query,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
        })
    try:
        res = textwrap.wrap(response.text, 4000, break_long_words=True, replace_whitespace=False)
    except BaseException:
        try:
            ratings_lines = []
            for candidate in response.candidates:
                lines = []
                lines.append(f"index: {candidate.index}")
                lines.append(f"finish_reason: {candidate.finish_reason.name}")
                for s_r in candidate.safety_ratings:
                    lines.append(
                        f"safety_ratings {{\n  "
                        f"category: {s_r.category.name}\n  "
                        f"probability: {s_r.probability.name}\n}}"
                    )
                ratings_lines.append("\n".join(lines))
            await client2.send_message(event.chat_id, "\n----\n".join(ratings_lines), reply_to=event.message.id)
        except BaseException:
            pass
        return
    logging.info(f"ask ai {query} answer {response.text}")
    for line in res:
        await client2.send_message(event.chat.id, line + '\n\n gemini AI', reply_to=event.message.id)
