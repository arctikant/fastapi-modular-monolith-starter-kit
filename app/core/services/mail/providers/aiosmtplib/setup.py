from typing import TypedDict

from app.core.configs import app_config


class SMTPConfig(TypedDict, total=False):
    hostname: str | None
    port: int
    username: str | None
    password: str | None
    use_tls: bool


smtp_config: SMTPConfig = {
    'hostname': app_config.SMTP_HOST,
    'port': app_config.SMTP_PORT,
    'username': app_config.SMTP_USER,
    'password': app_config.SMTP_PASSWORD,
    'use_tls': app_config.SMTP_TLS,
}
