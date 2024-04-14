import redis

from config import config

r = redis.Redis(host=config.redis_host, port=config.redis_port, decode_responses=True)


async def ban(event):
    await r.sadd('banned', event.raw_text.replace('!ban ', ''))
