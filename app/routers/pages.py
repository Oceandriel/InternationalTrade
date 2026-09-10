"""页面路由：首页 / 产品列表 / 产品详情 / 关于 / 联系 / sitemap / robots。"""
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

from .. import catalog
from ..config import settings
from ..templating import templates

router = APIRouter()


def _base_ctx(request: Request, title: str, description: str, canonical_path: str = "", **extra) -> dict:
    ctx = {
        "request": request,
        "page_title": title if title.endswith(settings.company_short) or settings.company_short in title
        else f"{title} | {settings.company_short}",
        "page_description": description,
        "canonical": f"{settings.domain_clean}{canonical_path or request.url.path}",
        "current_path": request.url.path,
    }
    ctx.update(extra)
    return ctx


@router.get("/", response_class=Response)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=_base_ctx(
            request,
            title=settings.seo_title,
            description=settings.seo_description,
            canonical_path="/",
            featured=catalog.get_featured_products(3),
        ),
    )


@router.get("/products", response_class=Response)
async def products(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context=_base_ctx(
            request,
            title="Products & Capabilities",
            description=f"Explore {settings.company_short} product lines: precision machining, industrial automation, "
            f"metal fabrication, hydraulic systems and smart lighting. Factory-direct OEM/ODM supply.",
            canonical_path="/products",
            products=catalog.get_products(),
            categories=catalog.get_categories(),
        ),
    )


@router.get("/products/{slug}", response_class=Response)
async def product_detail(request: Request, slug: str):
    product = catalog.get_product(slug)
    if product is None:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context=_base_ctx(request, title="Product Not Found", description=settings.seo_description),
            status_code=404,
        )
    related = [p for p in catalog.get_products() if p["category"] == product["category"] and p["slug"] != slug][:3]
    if len(related) < 3:
        related += [p for p in catalog.get_products() if p["slug"] not in {product["slug"], *(r["slug"] for r in related)}]
    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context=_base_ctx(
            request,
            title=f"{product['name']}",
            description=product["description"][:160],
            product=product,
            related=related[:3],
        ),
    )


@router.get("/about", response_class=Response)
async def about(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context=_base_ctx(
            request,
            title="About Us",
            description=f"{settings.company_name} — {settings.company_description} "
            f"Founded in {settings.company_founded_year}, serving clients in {settings.company_countries} countries.",
            canonical_path="/about",
        ),
    )


@router.get("/contact", response_class=Response)
async def contact(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context=_base_ctx(
            request,
            title="Contact Us & Request a Quote",
            description=f"Contact {settings.company_name} for a factory-direct quote. "
            f"Email {settings.company_email} or send an inquiry — we reply within 24 business hours.",
            canonical_path="/contact",
            products=catalog.get_products(),
        ),
    )


@router.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------- SEO ----

@router.get("/sitemap.xml", response_class=Response)
async def sitemap(request: Request):
    paths = [
        ("/", "weekly", "1.0"),
        ("/products", "weekly", "0.9"),
        ("/about", "monthly", "0.6"),
        ("/contact", "monthly", "0.7"),
    ]
    for p in catalog.get_products():
        paths.append((f"/products/{p['slug']}", "monthly", "0.8"))

    urls_xml = "\n".join(
        f"  <url>\n    <loc>{settings.domain_clean}{path}</loc>\n"
        f"    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n  </url>"
        for path, freq, pri in paths
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls_xml}\n</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots(request: Request):
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        f"Sitemap: {settings.domain_clean}/sitemap.xml\n"
    )
