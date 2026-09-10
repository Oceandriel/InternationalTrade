"""全站配置：所有公司信息 / 联系方式 / SEO / 邮件 / 端口均来自 .env 环境变量。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- 运行环境 ----
    app_env: str = "production"
    site_domain: str = "https://www.example.com"
    nginx_http_port: int = 8080

    # ---- 公司信息 ----
    company_name: str = "NovaForge Industries Ltd."
    company_tagline: str = "Precision Manufacturing, Engineered for the World."
    company_short: str = "NOVAFORGE"
    company_description: str = (
        "ISO 9001 certified manufacturer of precision machined components, "
        "industrial automation modules and custom fabrication."
    )
    company_founded_year: int = 2008
    company_employees: int = 320
    company_countries: str = "40+"
    company_factory_area: int = 18000

    # ---- 联系方式 ----
    company_email: str = "sales@example.com"
    company_phone: str = "+86 21 8888 6666"
    company_whatsapp: str = ""
    company_address: str = "Shanghai, China"
    company_hours: str = "Mon - Sat, 9:00 - 18:00 (GMT+8)"

    # ---- 社交媒体（留空自动隐藏） ----
    linkedin_url: str = ""
    facebook_url: str = ""
    youtube_url: str = ""
    instagram_url: str = ""

    # ---- SEO ----
    seo_title: str = "B2B Manufacturer & Industrial Supplier"
    seo_description: str = (
        "ISO 9001 certified manufacturer supplying precision components and "
        "industrial products to clients worldwide. Request a factory-direct quote."
    )
    seo_keywords: str = (
        "B2B manufacturer, precision manufacturing, OEM supplier, "
        "factory direct, industrial components"
    )
    seo_og_image: str = ""

    # ---- 数据库 ----
    database_url: str = "sqlite:///./data/inquiries.db"

    # ---- SMTP 邮件 ----
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_from_name: str = "Website Notification"
    mail_to: str = ""
    smtp_use_ssl: bool = True

    @property
    def domain_clean(self) -> str:
        """去掉结尾斜杠的域名。"""
        return self.site_domain.rstrip("/")

    @property
    def email_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.mail_to)


settings = Settings()
