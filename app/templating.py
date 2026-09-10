"""Jinja2 模板实例（全局共享），注入全站配置供所有模板使用。"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi.templating import Jinja2Templates

from . import catalog
from .config import settings

BASE_DIR = Path(__file__).parent

_IMAGE_API = "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image"


def img(prompt: str, size: str = "landscape_16_9") -> str:
    """模板内调用：生成文生图 URL（自动 URL 编码）。"""
    return f"{_IMAGE_API}?prompt={quote(prompt)}&image_size={size}"


templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
# 模板内通过 {{ s.xxx }} / {{ settings.xxx }} 读取 .env 配置
templates.env.globals["s"] = templates.env.globals["settings"] = settings
templates.env.globals["img"] = img
templates.env.globals["catalog"] = catalog
templates.env.globals["now_year"] = datetime.now(timezone.utc).year
