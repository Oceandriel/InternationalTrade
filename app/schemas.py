"""询盘表单校验（Pydantic v2）。"""
import re

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class InquiryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=200)
    company: str = Field("", max_length=120)
    country: str = Field("", max_length=80)
    phone: str = Field("", max_length=40)
    product_interest: str = Field("", max_length=160)
    message: str = Field(..., min_length=10, max_length=4000)

    # 蜜罐字段：正常用户看不到、不会填；机器人填写即判定垃圾提交
    website: str = Field("", max_length=100)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError("Please enter a valid email address.")
        return v

    @field_validator("name", "company", "country", "phone", "product_interest", "message")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()
