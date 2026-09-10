"""询盘邮件通知：客户提交后 -> 通知公司销售邮箱 + 自动回复客户确认函。

SMTP 未配置（SMTP_HOST 为空）时自动跳过发送，仅将询盘入库，
保证本地开发 / 未配置邮箱时网站仍可正常运行。
"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from .config import settings
from .models import Inquiry

logger = logging.getLogger("uvicorn.error")


def _send_email(to_email: str, subject: str, html: str, text: str, reply_to: str = "") -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((settings.smtp_from_name, settings.smtp_from or settings.smtp_user))
    msg["To"] = to_email
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    context = ssl.create_default_context()
    if settings.smtp_use_ssl or settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=context, timeout=20) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from or settings.smtp_user, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from or settings.smtp_user, [to_email], msg.as_string())


def _notification_html(inq: Inquiry) -> str:
    rows = [
        ("Name", inq.name),
        ("Email", inq.email),
        ("Company", inq.company or "-"),
        ("Country", inq.country or "-"),
        ("Phone", inq.phone or "-"),
        ("Product Interest", inq.product_interest or "-"),
        ("Submitted At", inq.created_at.strftime("%Y-%m-%d %H:%M UTC")),
        ("IP Address", inq.ip_address or "-"),
    ]
    rows_html = "".join(
        f'<tr><td style="padding:8px 16px;border:1px solid #e5e2da;font-weight:600;'
        f'background:#f7f5f0;width:180px;">{label}</td>'
        f'<td style="padding:8px 16px;border:1px solid #e5e2da;">{value}</td></tr>'
        for label, value in rows
    )
    return f"""\
<div style="font-family:Arial,Helvetica,sans-serif;max-width:640px;margin:0 auto;">
  <div style="background:#0e1014;color:#fff;padding:28px 32px;">
    <div style="font-size:20px;letter-spacing:2px;font-weight:700;">{settings.company_short}</div>
    <div style="margin-top:8px;font-size:14px;color:#b9bcc4;">New inquiry from {settings.domain_clean}</div>
  </div>
  <div style="padding:28px 32px;">
    <h2 style="margin:0 0 20px;font-size:20px;color:#0e1014;">New Customer Inquiry</h2>
    <table style="border-collapse:collapse;width:100%;font-size:14px;">{rows_html}</table>
    <p style="margin:20px 0 8px;font-weight:600;">Message:</p>
    <div style="background:#f7f5f0;border:1px solid #e5e2da;padding:16px;font-size:14px;
                white-space:pre-wrap;line-height:1.7;">{inq.message}</div>
    <p style="margin:24px 0 0;font-size:13px;color:#6b6f76;">
      Reply directly to this email to respond to the customer (Reply-To is set to the customer).
    </p>
  </div>
</div>"""


def _notification_text(inq: Inquiry) -> str:
    return (
        "New customer inquiry\n"
        f"Name: {inq.name}\nEmail: {inq.email}\nCompany: {inq.company or '-'}\n"
        f"Country: {inq.country or '-'}\nPhone: {inq.phone or '-'}\n"
        f"Product Interest: {inq.product_interest or '-'}\n"
        f"Submitted: {inq.created_at:%Y-%m-%d %H:%M UTC}\nIP: {inq.ip_address or '-'}\n\n"
        f"Message:\n{inq.message}\n"
    )


def _confirmation_html(inq: Inquiry) -> str:
    return f"""\
<div style="font-family:Arial,Helvetica,sans-serif;max-width:640px;margin:0 auto;">
  <div style="background:#0e1014;color:#fff;padding:28px 32px;">
    <div style="font-size:20px;letter-spacing:2px;font-weight:700;">{settings.company_short}</div>
  </div>
  <div style="padding:28px 32px;color:#14151a;line-height:1.8;font-size:15px;">
    <h2 style="margin:0 0 16px;font-size:22px;">Thank you for your inquiry, {inq.name}.</h2>
    <p>We have received your request regarding
       <strong>{inq.product_interest or 'our products'}</strong>.
       Our export sales team will get back to you within <strong>24 hours</strong>
       (business days).</p>
    <p style="color:#6b6f76;font-size:14px;">If your request is urgent, please contact us directly:</p>
    <ul style="font-size:14px;color:#6b6f76;padding-left:20px;">
      <li>Email: {settings.company_email}</li>
      <li>Phone / WhatsApp: {settings.company_phone}</li>
    </ul>
    <p style="margin-top:28px;font-size:14px;">Best regards,<br>
       <strong>{settings.company_name}</strong><br>{settings.company_tagline}</p>
  </div>
</div>"""


def _confirmation_text(inq: Inquiry) -> str:
    return (
        f"Dear {inq.name},\n\n"
        "Thank you for your inquiry. We have received your request and our export sales "
        "team will get back to you within 24 business hours.\n\n"
        f"For urgent matters: {settings.company_email} / {settings.company_phone}\n\n"
        f"Best regards,\n{settings.company_name}\n{settings.company_tagline}\n"
    )


def send_inquiry_emails(inq: Inquiry) -> None:
    """发送通知邮件 + 客户确认函；任何邮件异常都不影响询盘入库结果。"""
    if not settings.email_configured:
        logger.warning("SMTP not configured — inquiry #%s saved to database but no email sent.", inq.id)
        return
    try:
        _send_email(
            to_email=settings.mail_to,
            subject=f"[New Inquiry] {inq.product_interest or 'General'} — {inq.name} ({inq.company or '-'})",
            html=_notification_html(inq),
            text=_notification_text(inq),
            reply_to=inq.email,
        )
        _send_email(
            to_email=inq.email,
            subject=f"Thank you for contacting {settings.company_name}",
            html=_confirmation_html(inq),
            text=_confirmation_text(inq),
        )
        logger.info("Inquiry emails sent for #%s (notify %s, confirm %s)", inq.id, settings.mail_to, inq.email)
    except Exception:
        logger.exception("Failed to send inquiry emails for inquiry #%s", inq.id)
