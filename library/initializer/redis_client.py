
import redis
from library.config.config import load_config


class RedisClient(object):
    """
    Usage:
        >>> from library.initializer.redis_client import RedisClient
        >>> redis_client = RedisClient().get_client()
        >>> print(redis_client.set('test', 'hello world'))
        >>> print(redis_client.get('test'))
    """

    def __init__(self, redis_config: dict = load_config('db.redis_config')):
        pool = redis.ConnectionPool(**redis_config)
        self.redis_client = redis.Redis(connection_pool=pool)

    def get_client(self):
        return self.redis_client
