"""Envío de alertas por email vía Gmail SMTP."""
from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from loguru import logger

from binance_p2p import Offer
from config import config

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def _build_html(offers: list[Offer], min_price: float) -> str:
    rows = "\n".join(
        f"""
        <tr>
          <td style="padding:8px;border:1px solid #ddd;font-weight:bold;color:#d35400">{o.price:.3f}</td>
          <td style="padding:8px;border:1px solid #ddd">{o.min_amount:.0f} - {o.max_amount:.0f} {config.fiat}</td>
          <td style="padding:8px;border:1px solid #ddd">{escape(o.nickname)}</td>
          <td style="padding:8px;border:1px solid #ddd">{o.finish_rate:.1f}%</td>
          <td style="padding:8px;border:1px solid #ddd">
            <a href="{escape(o.link, quote=True)}" style="background:#f0b90b;color:#000;padding:6px 12px;
               text-decoration:none;border-radius:4px;font-weight:bold">Comprar</a>
          </td>
        </tr>"""
        for o in offers
    )
    return f"""\
    <html><body style="font-family:Arial,sans-serif">
      <h2>🔔 Alerta P2P — {config.asset} a {min_price:.3f} {config.fiat}</h2>
      <p>Se alcanzó tu umbral de precio para <b>{config.bank_display_name}</b>.
         Compra de <b>{config.order_amount_usd:.0f} {config.fiat}</b>.</p>
      <table style="border-collapse:collapse;width:100%">
        <thead>
          <tr style="background:#fafafa">
            <th style="padding:8px;border:1px solid #ddd">Precio</th>
            <th style="padding:8px;border:1px solid #ddd">Límites</th>
            <th style="padding:8px;border:1px solid #ddd">Anunciante</th>
            <th style="padding:8px;border:1px solid #ddd">% compl.</th>
            <th style="padding:8px;border:1px solid #ddd">Acción</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="color:#888;font-size:12px;margin-top:16px">
        Ejecuta la orden manualmente desde el link. Monitor P2P Binance.</p>
    </body></html>"""


def send_alert(offers: list[Offer], min_price: float) -> None:
    """Envía el email de alerta con las mejores ofertas."""
    if not offers:
        return

    subject = (
        f"🔔 P2P {config.asset} a {min_price:.3f} {config.fiat} — "
        f"{config.bank_display_name} (compra {config.order_amount_usd:.0f} {config.fiat})"
    )

    if config.dry_run:
        logger.info(f"[DRY_RUN] Email NO enviado. Asunto: {subject}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.gmail_user
    msg["To"] = config.alert_email
    msg.attach(MIMEText(_build_html(offers, min_price), "html"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(config.gmail_user, config.gmail_app_password)
        server.send_message(msg)
    logger.success(f"Email enviado a {config.alert_email}")


if __name__ == "__main__":
    # Test aislado: envía un email de prueba con ofertas reales
    from binance_p2p import get_offers

    real = get_offers(config.bank_payment_type, asset=config.asset, fiat=config.fiat)[:5]
    if not real:
        real = [Offer(0.997, 100, 500, "TEST123", "TestUser", 50, 99.5)]
    send_alert(real, real[0].price)
    print("Test de email ejecutado.")
