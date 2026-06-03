from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.dependencies import get_hf_service, get_review_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await get_review_service().close()
    await get_hf_service().close()


app = FastAPI(title="PRReviewIQ", version="0.1.0", lifespan=lifespan)
app.include_router(router)
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parent / "static"),
    name="static",
)
