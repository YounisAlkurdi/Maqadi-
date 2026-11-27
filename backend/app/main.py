from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(title="Maqadi (طلبات البيت)", version="0.1.0")

    if settings.cors_origin_list:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    api_router = APIRouter(prefix="/api/v1")

    @api_router.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(api_router)

    if FRONTEND_DIR.is_dir():
        application.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

    return application


app = create_app()
