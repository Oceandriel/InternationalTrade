"""FastAPI 应用入口。"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import init_db
from .routers import api, pages
from .templating import templates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

BASE_DIR = Path(__file__).parent


# 幂等建表：不依赖 lifespan，确保任何启动方式（uvicorn / 测试 / 多 worker）下表都存在
init_db()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("Database ready. Email notifications: %s", "ON" if settings.email_configured else "OFF (SMTP not set)")
    yield


app = FastAPI(
    title=settings.company_name,
    description=settings.company_description,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(pages.router)
app.include_router(api.router)


def _error_context(request: Request, title: str) -> dict:
    return {
        "request": request,
        "page_title": title,
        "page_description": settings.seo_description,
        "canonical": f"{settings.domain_clean}{request.url.path}",
        "current_path": request.url.path,
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context=_error_context(request, f"Page Not Found | {settings.company_short}"),
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.exception("Server error: %s", exc)
    return templates.TemplateResponse(
        request=request,
        name="500.html",
        context=_error_context(request, f"Server Error | {settings.company_short}"),
        status_code=500,
    )
