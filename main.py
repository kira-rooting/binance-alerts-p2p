"""Entry point: arranca el scheduler de monitoreo P2P."""
from __future__ import annotations

import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger

from config import config
from scheduler_job import check_prices


def main() -> None:
    logger.info("=" * 60)
    logger.info(
        f"Monitor P2P Binance {config.fiat}/{config.asset} — {config.bank_display_name}"
    )
    logger.info(
        f"payType={config.bank_payment_type} | umbral={config.price_threshold:.3f} | "
        f"monto={config.order_amount_usd:.0f} {config.fiat} | "
        f"intervalo={config.poll_interval_seconds}s | cooldown={config.cooldown_minutes}min"
    )
    logger.info(
        f"Canales: email={'ON' if config.email_enabled else 'OFF'} "
        f"telegram={'ON' if config.telegram_enabled else 'OFF'} "
        f"whatsapp={'ON' if config.whatsapp_enabled else 'OFF'} | "
        f"DRY_RUN={'ON' if config.dry_run else 'OFF'}"
    )
    logger.info("=" * 60)

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        check_prices,
        "interval",
        seconds=config.poll_interval_seconds,
        next_run_time=None,  # se define abajo para correr de inmediato
        max_instances=1,
        coalesce=True,
    )

    # Ejecuta una vez al arrancar y luego cada intervalo
    check_prices()

    def _shutdown(*_):
        logger.info("Deteniendo monitor…")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
