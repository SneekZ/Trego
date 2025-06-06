from typing import Optional
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.auth.transport.requests import Request
import google_auth_oauthlib.flow
from fastapi.exceptions import HTTPException
from fastapi import Request, APIRouter 
from fastapi.responses import RedirectResponse
import os
import dotenv
import json

from db.database import get_db
import db.handlers as userDb
from app.utils.sha256 import sha256
from app.redis import Redis

SCOPES = [
        'https://www.googleapis.com/auth/userinfo.email',
        'openid',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/fitness.activity.read',
        'https://www.googleapis.com/auth/fitness.sleep.read',
        'https://www.googleapis.com/auth/fitness.heart_rate.read'
    ]

dotenv.load_dotenv()

routerOauth = APIRouter()

@routerOauth.get("/login/")
async def login():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secret.json', 
        scopes=SCOPES
    )

    appUrl = os.getenv("APP_URL")

    flow.redirect_uri = f'{appUrl}/auth'

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        login_hint='hint@example.com'
    )

    return RedirectResponse(authorization_url)

@routerOauth.get("/auth/")
async def auth(code: Optional[str] = None, error: Optional[str] = None):
    frontendUrl = os.getenv("FRONTEND_URL")
    if error:
        return RedirectResponse(f"{frontendUrl}/error?error={error}")

    if not code:
        raise HTTPException(status_code=400, detail="Отсутствует код авторизации")

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES 
    )

    flow.redirect_uri = f"{os.getenv('APP_URL')}/auth"

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'       
    )

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка получения токена: {str(e)}")

    credentials = flow.credentials
    request_session = google_requests.Request()

    try:
        idinfo = id_token.verify_oauth2_token(
            credentials._id_token, request_session, audience=None
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка проверки токена: {str(e)}")

    userId = idinfo.get("sub")
    if not userId:
        raise HTTPException(status_code=400, detail="Id не получен из токена")

    sessionToken = sha256(userId)


    await Redis().setRefreshCode(sessionToken, credentials.refresh_token)

    return RedirectResponse(f"{os.getenv("FRONTEND_URL")}/?sessionToken={sessionToken}")

def getAccessToken(refresh_token: str) -> str:
    try:
        with open('client_secret.json', 'r') as f:
            client_data = json.load(f)

        client_id = client_data['installed']['client_id']
        client_secret = client_data['installed']['client_secret']
        token_uri = client_data['installed']['token_uri']

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret
        )

        request = Request()
        credentials.refresh(request)

        return credentials.token,

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обновления access_token: {str(e)}")