"""Ciclo de monitoreo: consulta precios, evalúa umbral y dispara alertas."""
from __future__ import annotations

from loguru import logger

import notifier
import state
from binance_p2p import get_offers
from config import config


def check_prices() -> None:
    """Un ciclo de monitoreo. Lo invoca el scheduler periódicamente."""
    try:
        offers = get_offers(config.bank_payment_type, asset=config.asset, fiat=config.fiat)
    except Exception as exc:  # noqa: BLE001 — un fallo no debe matar el scheduler
        logger.error(f"Error consultando Binance P2P: {exc}")
        return

    # Solo ofertas donde realmente se puede comprar el monto objetivo
    valid = [o for o in offers if o.accepts_amount(config.order_amount_usd)]
    if not valid:
        logger.info(
            f"Sin ofertas que acepten {config.order_amount_usd:.0f} {config.fiat} "
            f"(total ofertas: {len(offers)})"
        )
        return

    min_price = valid[0].price
    logger.info(
        f"Precio mín. (acepta {config.order_amount_usd:.0f} {config.fiat}): "
        f"{min_price:.3f} {config.fiat} | umbral: {config.price_threshold:.3f} | "
        f"ofertas válidas: {len(valid)}"
    )

    if min_price > config.price_threshold:
        return

    if state.in_cooldown(config.cooldown_minutes):
        logger.info(f"Umbral alcanzado pero en cooldown ({config.cooldown_minutes} min); no se notifica")
        return

    logger.success(f"¡Umbral alcanzado! {min_price:.3f} <= {config.price_threshold:.3f}. Notificando…")
    notifier.send_alert(valid[:5], min_price)
    state.mark_alert()
