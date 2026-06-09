"""Envío de alertas por WhatsApp vía CallMeBot (API gratuita, uso personal)."""
from __future__ import annotations

import requests
from loguru import logger

from binance_p2p import Offer
from config import config

API_URL = "https://api.callmebot.com/whatsapp.php"


def _build_text(offers: list[Offer], min_price: float) -> str:
    best = offers[0]
    lines = [
        f"🔔 *{config.asset} a {min_price:.3f} {config.fiat}* — {config.bank_display_name}",
        f"Compra de {config.order_amount_usd:.0f} {config.fiat}",
        "",
        f"Mejor oferta: *{best.price:.3f}* "
        f"(límite {best.min_amount:.0f}-{best.max_amount:.0f} {config.fiat})",
        f"Anunciante: {best.nickname} ({best.finish_rate:.1f}%)",
        f"👉 {best.link}",
    ]
    if len(offers) > 1:
        lines.append("")
        lines.append("Otras: " + ", ".join(f"{o.price:.3f}" for o in offers[1:4]))
    return "\n".join(lines)


def send_alert(offers: list[Offer], min_price: float) -> None:
    """Envía el mensaje de WhatsApp con la mejor oferta y el link directo."""
    if not offers:
        return

    text = _build_text(offers, min_price)

    if config.dry_run:
        logger.info(f"[DRY_RUN] WhatsApp NO enviado:\n{text}")
        return

    params = {
        "phone": config.callmebot_phone,
        "text": text,
        "apikey": config.callmebot_apikey,
    }
    resp = requests.get(API_URL, params=params, timeout=20)
    resp.raise_for_status()

    # CallMeBot SIEMPRE responde 200; el estado real va en el cuerpo HTML.
    body = resp.text
    low = body.lower()
    if "queued" in low or "message sent" in low or "message to:" in low and "error" not in low:
        logger.success(f"WhatsApp aceptado por CallMeBot para {config.callmebot_phone}")
    else:
        logger.error(f"CallMeBot no aceptó el mensaje: {body[:300]}")
        raise RuntimeError(f"CallMeBot rechazó el envío: {body[:200]}")


if __name__ == "__main__":
    # Test aislado
    from binance_p2p import get_offers

    real = get_offers(config.bank_payment_type, asset=config.asset, fiat=config.fiat)[:5]
    if not real:
        real = [Offer(0.997, 100, 500, "TEST123", "TestUser", 50, 99.5)]
    send_alert(real, real[0].price)
    print("Test de WhatsApp ejecutado.")
