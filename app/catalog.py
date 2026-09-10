"""产品目录：从 catalog.json 读取，图片由文生图 API 动态生成（URL 自动编码）。

模板使用者只需编辑 catalog.json 即可增删产品，无需改动代码。
"""
import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

_CATALOG_PATH = Path(__file__).parent / "catalog.json"
_IMAGE_API = "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image"


@lru_cache(maxsize=1)
def _load() -> dict:
    data = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    for product in data["products"]:
        prompt = product.get("image_prompt", "")
        size = product.get("image_size", "square")
        product["image"] = f"{_IMAGE_API}?prompt={quote(prompt)}&image_size={size}"
    return data


def get_products() -> list[dict]:
    return _load()["products"]


def get_categories() -> list[str]:
    return _load()["categories"]


def get_featured_products(limit: int = 6) -> list[dict]:
    products = get_products()
    featured = [p for p in products if p.get("featured")]
    return (featured or products)[:limit]


def get_product(slug: str) -> dict | None:
    return next((p for p in get_products() if p["slug"] == slug), None)
