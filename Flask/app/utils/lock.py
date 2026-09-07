"""Redis 分布式锁：锁对象 + with 上下文管理器"""
import time
import uuid
from contextlib import contextmanager

from ..extensions import redis_client


class RedisLock:
    """基于 Redis SET NX 的分布式锁，防止误删他人锁"""
    def __init__(self, key, timeout=10):
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.value = str(uuid.uuid4())

    def acquire(self, retry=3, delay=0.1):
        for _ in range(retry):
            if redis_client.set(self.key, self.value, nx=True, ex=self.timeout):
                return True
            time.sleep(delay)
        return False

    def release(self):
        """Lua 脚本保证只释放属于自己的锁"""
        lua = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            redis_client.eval(lua, 1, self.key, self.value)
        except Exception:
            pass


@contextmanager
def distributed_lock(key, timeout=10):
    lock = RedisLock(key, timeout)
    if not lock.acquire():
        raise Exception(f"获取锁失败: {key}")
    try:
        yield
    finally:
        lock.release()
