"""Orquesta los canales de notificación (email + WhatsApp).

Cada canal es independiente: si uno falla, se loguea el error y se continúa
con el otro, para no perder la alerta por un fallo parcial.
"""
from __future__ import annotations

from loguru import logger

import email_sender
import telegram_sender
import whatsapp_sender
from binance_p2p import Offer
from config import config


def send_alert(offers: list[Offer], min_price: float) -> None:
    """Notifica por todos los canales habilitados."""
    if config.email_enabled:
        try:
            email_sender.send_alert(offers, min_price)
        except Exception as exc:  # noqa: BLE001 — aislar fallo de canal
            logger.error(f"Canal email falló: {exc}")

    if config.telegram_enabled:
        try:
            telegram_sender.send_alert(offers, min_price)
        except Exception as exc:  # noqa: BLE001 — aislar fallo de canal
            logger.error(f"Canal Telegram falló: {exc}")

    if config.whatsapp_enabled:
        try:
            whatsapp_sender.send_alert(offers, min_price)
        except Exception as exc:  # noqa: BLE001 — aislar fallo de canal
            logger.error(f"Canal WhatsApp falló: {exc}")
