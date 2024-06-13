import logging
import textwrap

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import config
from TelegramUtils import client2

genai.configure(api_key=config.gemini_api_key)


async def answer(event):
    model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest')
    query = event.raw_text.replace('!ai', '')
    response = model.generate_content(
        f"ты лаконичный ассистент, который отвечает точно: {query}",
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
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
