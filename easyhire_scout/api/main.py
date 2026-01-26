from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from easyhire_scout.api.v1 import router as v1_router

def create_app() -> FastAPI:
    app = FastAPI(title="EasyHire Scout API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],    # TODO: Configure specific origins in production
        allow_credentials=True,
        allow_methods=["*"],    # Allows all HTTP methods [Refinement needed]
        allow_headers=["*"],    # Allows all headers [Refinement needed]
    )
    app.include_router(v1_router, prefix="/v1")
    return app

app = create_app()