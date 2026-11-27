from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.composition import create_lifespan
from app.config import get_settings
from app.interfaces.api.errors import register_exception_handlers
from app.interfaces.api.households import router as households_router
from app.interfaces.api.items import router as items_router
from app.interfaces.api.paste import router as paste_router

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title="Maqadi (طلبات البيت)",
        version="0.1.0",
        lifespan=create_lifespan(settings),
    )

    register_exception_handlers(application)

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

    api_router.include_router(households_router)
    api_router.include_router(items_router)
    api_router.include_router(paste_router)
    application.include_router(api_router)

    if FRONTEND_DIR.is_dir():
        application.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

    return application


app = create_app()
