import redis.asyncio as redis
import dotenv
import os
import datetime

dotenv.load_dotenv()

REDIS_CONFIG = {
    "host": os.getenv('REDIS_HOST'),
    "port": os.getenv('REDIS_PORT'),
    "password": os.getenv('REDIS_PASSWORD')
}

def redisSession():
    return redis.Redis(**REDIS_CONFIG, db=0)

class Redis:

    @staticmethod
    def redisSession():
        return redis.Redis(**REDIS_CONFIG, db=0)

    @staticmethod
    def datetimeToInt(ttl: datetime.datetime) -> int:
        return int((ttl - datetime.datetime.now()).total_seconds())

    async def setRefreshCode(self, sessionToken: str, code: str, ttl: datetime.datetime | int | None = None) -> None:
        if not code:
            return

        if type(ttl) == datetime.datetime:
            ttl = self.datetimeToInt(ttl)

        async with self.redisSession() as r:
            await r.set(f"refreshToken:{sessionToken}", code, ex=ttl)

    async def getRefreshCode(self, sessionToken: str) -> str | None:
        async with self.redisSession() as r:
            refreshToken = await r.get(f"refreshToken:{sessionToken}") 

        return refreshToken

    async def setAccessToken(self, sessionToken: str, code: str, ttl: datetime.datetime | int) -> None:
        if not code:
            return

        if type(ttl) == datetime.datetime:
            ttl = self.datetimeToInt(ttl)

        async with self.redisSession() as r:
            await r.set(f"accessToken:{sessionToken}", code, ex=ttl)

    async def getAccessToken(self, sessionToken: str) -> str | None:
        async with self.redisSession() as r:
            refreshToken = await r.get(f"accessToken:{sessionToken}") 

        return refreshToken