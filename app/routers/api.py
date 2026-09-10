"""询盘 API：接收客户询盘 -> 校验 -> 存入 SQLite -> 触发邮件通知。"""
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..email_service import send_inquiry_emails
from ..models import Inquiry
from ..schemas import InquiryCreate

router = APIRouter(prefix="/api", tags=["inquiry"])

# 简易内存限流：同一 IP 每小时最多 5 条（容器重启自动清零，无需额外依赖）
_submissions: dict[str, deque[float]] = defaultdict(deque)
RATE_LIMIT = 5
RATE_WINDOW_SECONDS = 3600


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


@router.post("/inquiries")
async def create_inquiry(
    payload: InquiryCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    # 蜜罐：机器人通常会填写隐藏的 website 字段；静默返回成功，不入库
    if payload.website:
        return {"ok": True, "message": "Thank you. We will get back to you shortly."}

    ip = _client_ip(request)
    now = time.time()
    bucket = _submissions[ip]
    while bucket and now - bucket[0] > RATE_WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many submissions. Please try again later or email us directly.")
    bucket.append(now)

    inquiry = Inquiry(
        name=payload.name,
        email=payload.email,
        company=payload.company,
        country=payload.country,
        phone=payload.phone,
        product_interest=payload.product_interest,
        message=payload.message,
        ip_address=ip,
        user_agent=request.headers.get("user-agent", "")[:300],
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)

    # 邮件发送内部已捕获异常，不会影响接口返回（询盘已入库，不丢数据）
    send_inquiry_emails(inquiry)

    return {
        "ok": True,
        "message": (
            "Thank you for your inquiry. Our export sales team will reply "
            "within 24 business hours. A confirmation email has been sent to your inbox."
        ),
    }
