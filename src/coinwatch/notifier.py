"""Notification channels: log, Telegram, Discord, Email."""

from __future__ import annotations

import json
import smtplib
import urllib.request

from email.message import EmailMessage

from .config import Config


def notify(config: Config, message: str) -> None:
    """Fan a rendered report out to every enabled channel."""
    message = message or ""
    settings = config.notify

    if str(settings.get("log", True)).lower() not in ("false", "0", "no"):
        if message.strip():
            print(message)

    # An empty report means "nothing happened" — never spam external channels.
    if not message.strip():
        return

    _telegram(settings, message)
    _discord(settings, message)
    _email(settings, message)


def _post_json(url: str, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception:  # noqa: BLE001 - one bad channel must not break the run
        pass


def _telegram(settings: dict, message: str) -> None:
    token = settings.get("telegram_token")
    chat_id = settings.get("telegram_chat_id")
    if not token or not chat_id:
        return
    _post_json(
        f"https://api.telegram.org/bot{token}/sendMessage",
        {"chat_id": chat_id, "text": message},
    )


def _discord(settings: dict, message: str) -> None:
    webhook = settings.get("discord_webhook")
    if not webhook:
        return
    # Discord hard-caps embeds/content at 2000 chars.
    _post_json(webhook, {"content": message[:1900]})


def _email(settings: dict, message: str) -> None:
    host = settings.get("email_smtp_host")
    recipient = settings.get("email_to")
    if not host or not recipient:
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = "CoinWatch Alert"
        msg["From"] = settings.get("email_smtp_user") or "coinwatch@localhost"
        msg["To"] = recipient
        msg.set_content(message)

        with smtplib.SMTP(host, int(settings.get("email_smtp_port", 587))) as server:
            server.starttls()
            user = settings.get("email_smtp_user")
            if user:
                server.login(user, settings.get("email_smtp_pass", ""))
            server.send_message(msg)
    except Exception:  # noqa: BLE001
        pass
