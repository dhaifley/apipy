"""
An appilcation programing interface service.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import resources, login, users
from .db import init_db
from .config import settings

app = FastAPI(
    title=settings.SERVICE_NAME,
    description=settings.SERVICE_DESCRIPTION,
    version=settings.SERVICE_VERSION,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

@app.on_event("startup")
def on_startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resources.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(login.router, prefix=settings.API_PREFIX)
