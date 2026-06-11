"""Envío de alertas por Telegram vía Bot API (gratis, instantáneo y confiable).

Setup (2 min):
  1. En Telegram habla con @BotFather → /newbot → copia el TOKEN.
  2. Abre tu bot y envíale cualquier mensaje (ej. /start).
  3. Ejecuta:  .venv/bin/python telegram_sender.py
     Si TELEGRAM_CHAT_ID está vacío, este script descubre tu chat_id y te lo
     muestra para que lo pegues en el .env. Si ya está, envía un mensaje de prueba.
"""
from __future__ import annotations

from html import escape

import requests
from loguru import logger

from binance_p2p import Offer
from config import config

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _api(method: str, **params) -> dict:
    url = API_BASE.format(token=config.telegram_bot_token, method=method)
    resp = requests.post(url, json=params, timeout=20)
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error en {method}: {data.get('description', data)}")
    return data["result"]


def _build_text(offers: list[Offer], min_price: float) -> str:
    """Mensaje en HTML. El apodo del anunciante viene de Binance y es texto libre
    controlado por terceros, así que se escapa antes de incrustarlo en el HTML."""
    best = offers[0]
    lines = [
        f"🔔 <b>{config.asset} a {min_price:.3f} {config.fiat}</b> — {escape(config.bank_display_name)}",
        f"Compra de {config.order_amount_usd:.0f} {config.fiat}",
        "",
        f"Mejor oferta: <b>{best.price:.3f}</b> "
        f"(límite {best.min_amount:.0f}-{best.max_amount:.0f} {config.fiat})",
        f"Anunciante: {escape(best.nickname)} ({best.finish_rate:.1f}%)",
    ]
    if len(offers) > 1:
        lines.append("")
        lines.append("Otras: " + ", ".join(f"{o.price:.3f}" for o in offers[1:4]))
    return "\n".join(lines)


def send_alert(offers: list[Offer], min_price: float) -> None:
    """Envía la alerta con un botón directo a la mejor oferta."""
    if not offers:
        return

    text = _build_text(offers, min_price)

    if config.dry_run:
        logger.info(f"[DRY_RUN] Telegram NO enviado:\n{text}")
        return

    best = offers[0]
    _api(
        "sendMessage",
        chat_id=config.telegram_chat_id,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup={
            "inline_keyboard": [[{"text": "👉 Comprar en Binance", "url": best.link}]]
        },
    )
    logger.success(f"Telegram enviado a chat_id={config.telegram_chat_id}")


def _discover_chat_id() -> None:
    """Lee getUpdates y muestra el chat_id del último mensaje recibido."""
    url = API_BASE.format(token=config.telegram_bot_token, method="getUpdates")
    data = requests.get(url, timeout=20).json()
    if not data.get("ok"):
        print(f"Error: {data.get('description', data)}")
        return
    updates = data.get("result", [])
    if not updates:
        print(
            "No hay mensajes. Abre tu bot en Telegram, envíale /start "
            "y vuelve a ejecutar este script."
        )
        return
    seen: dict[int, str] = {}
    for u in updates:
        chat = (u.get("message") or u.get("edited_message") or {}).get("chat", {})
        if "id" in chat:
            name = chat.get("username") or chat.get("first_name") or "?"
            seen[chat["id"]] = name
    print("Chat(s) detectados (pega el id en TELEGRAM_CHAT_ID del .env):")
    for cid, name in seen.items():
        print(f"  chat_id={cid}  ({name})")


if __name__ == "__main__":
    if not config.telegram_bot_token:
        print("Falta TELEGRAM_BOT_TOKEN en el .env (créalo con @BotFather).")
    elif not config.telegram_chat_id:
        print("TELEGRAM_CHAT_ID vacío → descubriendo tu chat_id…\n")
        _discover_chat_id()
    else:
        from binance_p2p import get_offers

        real = get_offers(config.bank_payment_type, asset=config.asset, fiat=config.fiat)[:5]
        if not real:
            real = [Offer(1.012, 100, 500, "TEST123", "TestUser", 50, 99.5)]
        send_alert(real, real[0].price)
        print("Test de Telegram ejecutado.")
