from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from easyhire_scout.core.config import settings
from easyhire_scout.api.v1 import router as v1_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],    # TODO: Configure specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(v1_router, prefix=settings.API_V1_STR)
    return app

app = create_app()