"""Carga y validación de configuración desde el entorno (.env)."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from loguru import logger

load_dotenv()


def _get_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        logger.error(f"Variable {key} no es un número válido; usando {default}")
        return default


def _get_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        logger.error(f"Variable {key} no es un entero válido; usando {default}")
        return default


@dataclass(frozen=True)
class Config:
    # Mercado / banco
    bank_payment_type: str   # payType de Binance (ver discover_paytypes.py)
    bank_display_name: str   # nombre legible para los mensajes de alerta
    asset: str               # cripto a comprar (ej. USDT)
    fiat: str                # moneda fiat (ej. USD, VES, PEN)

    # Alertas
    price_threshold: float
    order_amount_usd: float
    poll_interval_seconds: int
    cooldown_minutes: int

    # Email
    email_enabled: bool
    gmail_user: str
    gmail_app_password: str
    alert_email: str

    # WhatsApp
    whatsapp_enabled: bool
    callmebot_phone: str
    callmebot_apikey: str

    # Telegram
    telegram_enabled: bool
    telegram_bot_token: str
    telegram_chat_id: str

    # Operación
    dry_run: bool

    @classmethod
    def load(cls) -> "Config":
        bank_payment_type = os.getenv("BANK_PAYMENT_TYPE", "").strip()
        cfg = cls(
            bank_payment_type=bank_payment_type,
            bank_display_name=os.getenv("BANK_DISPLAY_NAME", bank_payment_type).strip(),
            asset=os.getenv("ASSET", "USDT").strip().upper(),
            fiat=os.getenv("FIAT", "USD").strip().upper(),
            price_threshold=_get_float("PRICE_THRESHOLD", 0.998),
            order_amount_usd=_get_float("ORDER_AMOUNT_USD", 300),
            poll_interval_seconds=_get_int("POLL_INTERVAL_SECONDS", 60),
            cooldown_minutes=_get_int("COOLDOWN_MINUTES", 30),
            email_enabled=_get_bool("EMAIL_ENABLED", True),
            gmail_user=os.getenv("GMAIL_USER", "").strip(),
            gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", "").strip(),
            alert_email=os.getenv("ALERT_EMAIL", "").strip(),
            whatsapp_enabled=_get_bool("WHATSAPP_ENABLED", False),
            callmebot_phone=os.getenv("CALLMEBOT_PHONE", "").strip(),
            callmebot_apikey=os.getenv("CALLMEBOT_APIKEY", "").strip(),
            telegram_enabled=_get_bool("TELEGRAM_ENABLED", False),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
            dry_run=_get_bool("DRY_RUN", False),
        )
        cfg._validate()
        return cfg

    def _validate(self) -> None:
        problems: list[str] = []

        if not self.bank_payment_type:
            problems.append("BANK_PAYMENT_TYPE vacío: define el payType del banco (ver discover_paytypes.py)")

        if self.email_enabled and not self.dry_run:
            if not self.gmail_user or not self.gmail_app_password or not self.alert_email:
                problems.append(
                    "EMAIL_ENABLED=true pero falta GMAIL_USER / GMAIL_APP_PASSWORD / ALERT_EMAIL"
                )

        if self.whatsapp_enabled and not self.dry_run:
            if not self.callmebot_phone or not self.callmebot_apikey:
                problems.append(
                    "WHATSAPP_ENABLED=true pero falta CALLMEBOT_PHONE / CALLMEBOT_APIKEY"
                )

        if self.telegram_enabled and not self.dry_run:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                problems.append(
                    "TELEGRAM_ENABLED=true pero falta TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID"
                )

        if not (self.email_enabled or self.whatsapp_enabled or self.telegram_enabled):
            problems.append(
                "Ningún canal habilitado: activa EMAIL_ENABLED, TELEGRAM_ENABLED y/o WHATSAPP_ENABLED"
            )

        if problems:
            for p in problems:
                logger.error(f"Config inválida: {p}")
            sys.exit(1)


# Instancia global reutilizable
config = Config.load()
