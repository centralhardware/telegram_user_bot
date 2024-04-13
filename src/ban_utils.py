import redis

from src.config import Config

config = Config()
r = redis.Redis(host=config.redis_host, port=config.redis_port, decode_responses=True)
async def ban(event):
    await r.sadd('banned', event.raw_text.replace('!ban ', ''))
