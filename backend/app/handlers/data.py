from fastapi.exceptions import HTTPException
from fastapi import Request, APIRouter, Query
from typing import Optional
import dotenv
import json
import aiohttp
import time
import asyncio

from app.redis import Redis
from app.handlers.consts import WEIGHTS, TRAINING_GOALS, TRAINING_TYPES

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
        raise HTTPException(400, "Refresh Token не найден")

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
                raise HTTPException(400, f"Ошибка при получении токена: {resp.status}")

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
                text = await resp.json()
                raise HTTPException(400, f"Ошибка при получении данных из Google: {text.get("error", None).get("message", "неизвестная ошибка")}")

            response_json = await resp.json()
            return response_json

async def getHeartRateData(request: Request, days: Optional[int] = Query(1, gt=0)):
    sessionToken = getSessionToken(request)
    accessToken = await getAccessToken(sessionToken)

    data = await requestGoogle(accessToken, "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate", "com.google.heart_rate.bpm", days=days)

    try:
        heartRate = data["bucket"][0]["dataset"][0]["point"][0]["value"]

        avgHeartRate = int(heartRate[0]["fpVal"])
        maxHeartRate = int(heartRate[1]["fpVal"])
        minHeartRate = int(heartRate[2]["fpVal"])

        return {
            "min": minHeartRate,
            "max": maxHeartRate,
            "avg": avgHeartRate,
        }
    except Exception:
        raise HTTPException(400, "Данные не были получены")

async def getSleepData(request: Request, days: Optional[int] = Query(1, gt=0)):
    sessionToken = getSessionToken(request)
    accessToken = await getAccessToken(sessionToken)

    data = await requestGoogle(accessToken, "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate", "com.google.activity.segment", days=days)

    try:
        sleepData = data["bucket"][0]["dataset"][0]["point"]
        for sd in sleepData:
            if sd["originDataSourceId"] == "raw:com.google.activity.segment:com.xiaomi.hm.health:GoogleFitSyncHelper- steps segments1":
                return sd["value"][1]["intVal"]

    except Exception:
        raise HTTPException(400, "Данные не были получены")

async def getStepsData(request: Request, days: Optional[int] = Query(1, gt=0)):
    sessionToken = getSessionToken(request)
    accessToken = await getAccessToken(sessionToken)

    data = await requestGoogle(accessToken, "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate", "com.google.step_count.delta", days=days)

    try:
        stepsCount= data["bucket"][0]["dataset"][0]["point"][0]["value"][0]["intVal"]
        return stepsCount

    except Exception:
        raise HTTPException(400, "Данные не были получены")

async def getCaloriesData(request: Request, days: Optional[int] = Query(1, gt=0)):
    sessionToken = getSessionToken(request)
    accessToken = await getAccessToken(sessionToken)

    data = await requestGoogle(accessToken, "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate", "com.google.calories.expended", days=days)

    try:
        stepsCount= data["bucket"][0]["dataset"][0]["point"][0]["value"][0]["fpVal"]
        return stepsCount

    except Exception:
        raise HTTPException(400, "Данные не были получены")
    
async def getLoadData(request: Request):
    data = await asyncio.gather(
        getStepsData(request, 2),
        getStepsData(request, 7),
        getCaloriesData(request, 1),
        getCaloriesData(request, 7)
    )

    return WEIGHTS["w8"] * (data[0] / data[1]) + WEIGHTS["w9"] * (data[2] / data[3])

def elemByFraction(value, items):
    n = len(items)
    index = int(value * n)
    if index == n:
        index = n - 1
    return items[index]

@routerData.get("/trainingByLoad/")
async def getTrainingByLoad(request: Request, goalId: int = Query(0, ge=0, lt=len(TRAINING_GOALS))):
    load = await getLoadData(request)

    return elemByFraction(load, TRAINING_TYPES[goalId])

