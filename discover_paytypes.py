"""Lista los métodos de pago disponibles en Binance P2P para un fiat.

Úsalo para encontrar el identificador exacto del payType de tu banco
(el valor que va en BANK_PAYMENT_TYPE):

    python discover_paytypes.py            # todos los métodos para USD
    python discover_paytypes.py banco      # filtra por texto (ej. nombre del banco)
"""
from __future__ import annotations

import sys

from binance_p2p import list_trade_methods


def main() -> None:
    fiat = "USD"
    needle = sys.argv[1].lower() if len(sys.argv) > 1 else None

    methods = list_trade_methods(fiat)
    print(f"{len(methods)} métodos de pago para {fiat}\n")
    print(f"{'identifier':<28} | {'tradeMethodName'}")
    print("-" * 60)
    for m in methods:
        identifier = m.get("identifier", "")
        name = m.get("tradeMethodName", "")
        if needle and needle not in identifier.lower() and needle not in name.lower():
            continue
        print(f"{identifier:<28} | {name}")


if __name__ == "__main__":
    main()
