from fastapi.exceptions import HTTPException
from fastapi import Request, APIRouter
import dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
import json
import aiohttp
import time

from app.redis import Redis
from app.handlers.oauth import SCOPES

dotenv.load_dotenv()

routerData = APIRouter()

def getSessionToken(request: Request) -> str:
    sessionToken = request.cookies.get("sessionToken")
    if not sessionToken:
        raise HTTPException(401, "Пользователь не авторизован")

    return sessionToken

async def getAccessToken(sessionToken: str) -> str | None:
    fromRedis = await Redis().getAccessToken(sessionToken)
    if fromRedis:
        return fromRedis.decode()

    refreshToken = await Redis().getRefreshCode(sessionToken)
    if not refreshToken:
        raise HTTPException("400", "Refresh Token не найден")

    with open('client_secret.json') as file:
        clientInfo = json.load(file)['web']

    data = {
        "client_id": clientInfo["client_id"],
        "client_secret": clientInfo["client_secret"],
        "refresh_token": refreshToken,
        "grant_type": "refresh_token"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(clientInfo['token_uri'], data=data) as resp:
            if resp.status != 200:
                raise HTTPException("400", f"Ошибка при получении токена: {resp.status}")

            response_json = await resp.json()
            await Redis().setAccessToken(sessionToken, response_json["access_token"], response_json["expires_in"])
            return response_json["access_token"]

async def requestGoogle(accessToken: str, url: str, dataTypeName: str, days: int = 1) -> dict:
    end_time = int(time.time() * 1000)
    start_time = end_time - days * 86400000

    body = {
        "aggregateBy": {"dataTypeName": dataTypeName},
        "bucketByTime": {"durationMillis": days * 86400000},
        "startTimeMillis": start_time,
        "endTimeMillis": end_time
    }

    headers = {
        "Authorization": f"Bearer {accessToken}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=body) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise HTTPException("400", f"Ошибка при получении данных из Google: {text}")

            response_json = await resp.json()
            return response_json

@routerData.get("/heartRate/")
async def heartRate(request: Request):
    sessionToken = getSessionToken(request)
    accessToken = await getAccessToken(sessionToken)

    data = await requestGoogle(accessToken, "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate", "com.google.heart_rate.bpm")

    try:
        heartRate = data["bucket"][0]["dataset"][0]["point"][0]["value"]

        avgHeartRate = int(heartRate[0]["fpVal"])
        maxHeartRate = int(heartRate[1]["fpVal"])
        minHeartRate = int(heartRate[2]["fpVal"])

        return {
            "heartRate": {
                "min": minHeartRate,
                "max": maxHeartRate,
                "avg": avgHeartRate,
            }
        }
    except Exception:
        raise HTTPException("400", "Данные не были получены")

@routerData.get("/sleep/")
async def sleep(request: Request):
    sessionToken = getSessionToken(request)
    accessToken = await getAccessToken(sessionToken)

    data = await requestGoogle(accessToken, "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate", "com.google.activity.segment", days=7)

    return data

    try:
        heartRate = data["bucket"][0]["dataset"][0]["point"][0]["value"]

        avgHeartRate = int(heartRate[0]["fpVal"])
        maxHeartRate = int(heartRate[1]["fpVal"])
        minHeartRate = int(heartRate[2]["fpVal"])

        return {
            "heartRate": {
                "min": minHeartRate,
                "max": maxHeartRate,
                "avg": avgHeartRate,
            }
        }
    except Exception:
        raise HTTPException("400", "Данные не были получены")