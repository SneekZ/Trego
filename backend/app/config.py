from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COOKIE_SETTINGS = {
    "httponly": False,
    "secure": False,
    "samesite": "lax"
}

from app.handlers.oauth import routerOauth
from app.handlers.data import routerData

app.include_router(routerOauth, prefix="", tags=["User"])
app.include_router(routerData, prefix="", tags=["Data"])

