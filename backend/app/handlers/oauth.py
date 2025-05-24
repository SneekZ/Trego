from typing import Optional
import google.oauth2.credentials
import google_auth_oauthlib.flow
from fastapi.exceptions import HTTPException
from fastapi import Request, APIRouter, Response
from fastapi.responses import RedirectResponse
import os
import dotenv

from db.database import get_db
import db.handlers as userDb

dotenv.load_dotenv()

routerOauth = APIRouter()

@routerOauth.get("/login/")
async def login():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('client_secret.json',
    scopes=[
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/fitness.activity.read',
        'https://www.googleapis.com/auth/fitness.body.read',
        'https://www.googleapis.com/auth/fitness.body_temperature.read',
        'https://www.googleapis.com/auth/fitness.sleep.read'
    ])

    appUrl = os.getenv("APP_URL")

    flow.redirect_uri = f'{appUrl}/auth'

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        login_hint='hint@example.com'
    )

    return RedirectResponse(authorization_url)

@routerOauth.get("/auth/")
async def auth(code: str = None, error: str = None):
    frontendUrl = os.getenv("FRONTEND_URL")
    if error:
        return RedirectResponse(f"frontendUrl/error?error={error}")
    return RedirectResponse(frontendUrl)