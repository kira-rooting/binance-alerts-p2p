"""Estado persistente para el cooldown anti-spam (sobrevive reinicios)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from loguru import logger

STATE_FILE = Path(__file__).parent / "state.json"


def _read() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(f"state.json ilegible ({exc}); se reinicia")
    return {}


def _write(data: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        logger.error(f"No se pudo escribir state.json: {exc}")


def in_cooldown(cooldown_minutes: int) -> bool:
    """True si aún no pasó el cooldown desde la última alerta."""
    last = _read().get("last_alert_ts", 0)
    elapsed = time.time() - last
    return elapsed < cooldown_minutes * 60


def mark_alert() -> None:
    """Registra el timestamp de la alerta recién enviada."""
    data = _read()
    data["last_alert_ts"] = time.time()
    _write(data)
