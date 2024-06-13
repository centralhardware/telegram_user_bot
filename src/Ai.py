import logging
import textwrap

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import config
from TelegramUtils import client2

genai.configure(api_key=config.gemini_api_key)

chats = {}


async def answer(event):
    model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')
    query = event.raw_text.replace('!ai', '')

    if event.message.reply_to_msg_id is None or event.message.reply_to_msg_id not in chats:
        chats[event.message.id] = model.start_chat()

    if event.message.reply_to_msg_id is None:
        msg_id = event.message.id
    else:
        msg_id = event.message.reply_to_msg_id

    if len(chats[msg_id].history) >= 10:
        await client2.send_message(event.chat.id, 'Достигнут лимит', reply_to=event.message.id)
        return

    response = chats[msg_id].send_message(
        f"ты лаконичный ассистент, который отвечает точно: {query}",
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
        res = await client2.send_message(event.chat.id, line + '\n\n gemini AI', reply_to=event.message.id)
    chats[res.id] = chats[msg_id]