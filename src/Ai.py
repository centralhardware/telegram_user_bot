import logging
import textwrap

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from telethon.helpers import TotalList

from config import config
from TelegramUtils import client2

genai.configure(api_key=config.gemini_api_key)


async def get_messages(message, client, res, count=0):
    reply = await client.get_messages(message.chat.id, ids=message.reply_to_msg_id)
    if isinstance(reply, TotalList) or count >= 15:
        return res

    user = await client.get_entity(reply.from_id)
    if user.usernames is None:
        username = user.username
    else:
        username = user.usernames[0].username

    if 'gemini AI' in reply.raw_text:
        role = 'model'
    else:
        role = 'user'
    if role == 'user':
        res.append({'role': role, 'parts': [
            f"Сообщение от {user.first_name} / {user.last_name} / {username}" + ': ' + reply.raw_text.replace('!ai',
                                                                                                          '').replace(
                ' gemini AI', '')]})
    else:
        res.append({'role': role, 'parts': [reply.raw_text.replace('!ai', '').replace(' gemini AI', '')]})
    count = count + 1
    return await get_messages(reply, client, res, count)


async def answer(event):
    model = genai.GenerativeModel(model_name='gemini-1.5-pro-latest',
                                  system_instruction='ты лаконичный ассистент, который отвечает точно. Messages from user in chat come in the following format: Сообщение от {user name} / {user_last_name} / {user nickname}: {message content} Both name and nickname may be empty. Не выводи префикс сообщения до тех пор пока этого не попросили явно. При отправке кода выводи имя языка на той же строчке что и открывающие обратные ковычки')
    query = event.raw_text.replace('!ai', '').replace('!ии', '')

    context = await get_messages(event.message, event.client, [])
    context.reverse()

    user = await event.client.get_entity(event.message.sender.id)
    if user.usernames is None:
        username = user.username
    else:
        username = user.usernames[0].username


    context.append({'role': 'user', 'parts': [f"Сообщение от {user.first_name} / {user.last_name} / {username}" + ': ' +query]})
    response = model.generate_content(
        context,
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
