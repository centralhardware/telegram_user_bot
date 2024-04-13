from aiohttp import web


class MessageSender:
    def __init__(self, client):
        self.client = client

    async def handle_post(self, request):
        try:
            username = request.query['username']
            text = request.query['text']
        except Exception:
            return web.Response(status=400)
        result = await self.handle(username, text)
        if result:
            return web.Response(status=200, body='ok')

    async def handle(self, username, text):
        chat = await self.client.get_input_entity(username)
        async with self.client.conversation(chat) as conv:
            await conv.send_message(text)
            return True
