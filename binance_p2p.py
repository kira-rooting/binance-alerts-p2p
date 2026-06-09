"""Consulta el endpoint público de búsqueda P2P de Binance.

Solo lectura, sin autenticación. Devuelve ofertas donde NOSOTROS compramos USDT
(anunciante vende), filtradas por método de pago y ordenadas por precio ascendente.

Nota: en la API de Binance `tradeType` es la acción del usuario. Para comprar USDT
se usa `tradeType="BUY"` (el lado que muestra la pestaña "Comprar" de la web).
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests
from loguru import logger

SEARCH_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
TRADE_METHODS_URL = "https://p2p.binance.com/bapi/c2c/v1/public/c2c/agent/trade-methods"
# Dominio app.binance.com → abre la app de Binance en móvil. Muestra un aviso
# de "QR Code expired" (el parámetro ?code= colisiona con el login por QR), pero
# igual aterriza en la lista de comercios P2P para elegir la mejor oferta.
AD_LINK = "https://app.binance.com/en/adv?code={adv_no}"

_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "clienttype": "web",
}


@dataclass
class Offer:
    price: float
    min_amount: float
    max_amount: float
    adv_no: str
    nickname: str
    month_orders: int
    finish_rate: float

    @property
    def link(self) -> str:
        return AD_LINK.format(adv_no=self.adv_no)

    def accepts_amount(self, amount: float) -> bool:
        """True si se puede comprar `amount` (en fiat) en esta oferta."""
        return self.min_amount <= amount <= self.max_amount


def _request_with_retry(url: str, payload: dict, retries: int = 3) -> dict:
    """POST con reintentos y backoff exponencial."""
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, json=payload, headers=_HEADERS, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            wait = 2 ** attempt
            logger.warning(f"Intento {attempt}/{retries} falló ({exc}); reintento en {wait}s")
            if attempt < retries:
                time.sleep(wait)
    raise RuntimeError(f"Binance P2P no respondió tras {retries} intentos") from last_exc


def get_offers(
    pay_type: str,
    *,
    asset: str = "USDT",
    fiat: str = "USD",
    rows: int = 20,
) -> list[Offer]:
    """Devuelve ofertas donde compramos USDT (anunciante vende), precio asc."""
    payload = {
        "page": 1,
        "rows": rows,
        "payTypes": [pay_type] if pay_type else [],
        "asset": asset,
        "tradeType": "BUY",
        "fiat": fiat,
        "publisherType": None,
        "merchantCheck": False,
    }
    data = _request_with_retry(SEARCH_URL, payload)
    raw = data.get("data") or []

    offers: list[Offer] = []
    for item in raw:
        adv = item.get("adv", {})
        advertiser = item.get("advertiser", {})
        try:
            offers.append(
                Offer(
                    price=float(adv["price"]),
                    min_amount=float(adv["minSingleTransAmount"]),
                    max_amount=float(adv["maxSingleTransAmount"]),
                    adv_no=adv["advNo"],
                    nickname=advertiser.get("nickName", "?"),
                    month_orders=int(advertiser.get("monthOrderCount", 0)),
                    finish_rate=round(float(advertiser.get("monthFinishRate", 0)) * 100, 1),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.debug(f"Oferta omitida por datos incompletos: {exc}")

    offers.sort(key=lambda o: o.price)
    return offers


def list_trade_methods(fiat: str = "USD", retries: int = 3) -> list[dict]:
    """Lista los métodos de pago disponibles para un fiat (para descubrir el payType).

    Este endpoint es GET (a diferencia del de búsqueda, que es POST).
    """
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                TRADE_METHODS_URL, params={"fiat": fiat}, headers=_HEADERS, timeout=15
            )
            resp.raise_for_status()
            return resp.json().get("data") or []
        except (requests.RequestException, ValueError) as exc:
            last_exc = exc
            wait = 2 ** attempt
            logger.warning(f"Intento {attempt}/{retries} falló ({exc}); reintento en {wait}s")
            if attempt < retries:
                time.sleep(wait)
    raise RuntimeError(f"trade-methods no respondió tras {retries} intentos") from last_exc


if __name__ == "__main__":
    # Test de lectura rápido. Toma el payType del argumento o de BANK_PAYMENT_TYPE.
    import os
    import sys

    pay = sys.argv[1] if len(sys.argv) > 1 else os.getenv("BANK_PAYMENT_TYPE", "")
    if not pay:
        print("Uso: python binance_p2p.py <payType>  (o define BANK_PAYMENT_TYPE en .env)")
        sys.exit(1)
    asset = os.getenv("ASSET", "USDT")
    fiat = os.getenv("FIAT", "USD")
    print(f"Buscando ofertas para COMPRAR {asset}/{fiat} con payType='{pay}'...\n")
    result = get_offers(pay, asset=asset, fiat=fiat)
    if not result:
        print("Sin ofertas (revisa el payType con discover_paytypes.py)")
    for o in result[:10]:
        print(
            f"{o.price:>8.3f} USD | {o.min_amount:>7.0f}-{o.max_amount:<7.0f} | "
            f"{o.finish_rate:>5.1f}% | {o.nickname[:20]:<20} | {o.link}"
        )
