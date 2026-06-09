# Monitor P2P Binance — alerta de precio de compra de cripto

Vigila las ofertas P2P de Binance para comprar una cripto (ej. USDT) con el banco
y la moneda fiat que configures. Cuando el precio mínimo (en ofertas que aceptan tu
monto de compra) baja del umbral, envía una alerta por **email (Gmail)** y
**Telegram** con un **link directo** a la mejor oferta para que ejecutes la compra
manualmente. El banco, la cripto y el fiat se eligen en el `.env`
(`BANK_PAYMENT_TYPE`, `ASSET`, `FIAT`).

> ⚠️ Solo usa el endpoint **público de lectura** de Binance. No coloca órdenes
> automáticamente (la API oficial no lo permite y hacerlo viola los ToS).

## Setup

1. **Dependencias** (ya instaladas en `.venv`):
   ```bash
   python -m venv .venv && .venv/bin/pip install -r requirements.txt
   ```

2. **Credenciales** — copia y completa el `.env`:
   ```bash
   cp .env.example .env
   ```

   - **Gmail App Password** (requiere 2FA activado):
     https://myaccount.google.com/apppasswords → genera una y ponla en `GMAIL_APP_PASSWORD`.
   - **Telegram** (recomendado — instantáneo y confiable, setup 2 min):
     1. En Telegram habla con **@BotFather** → `/newbot` → copia el TOKEN en `TELEGRAM_BOT_TOKEN`.
     2. Abre tu bot y envíale `/start`.
     3. Ejecuta `.venv/bin/python telegram_sender.py` → te muestra tu **chat_id** → ponlo en `TELEGRAM_CHAT_ID`.
   - **CallMeBot WhatsApp** (opcional, menos confiable):
     1. Agrega el contacto **+34 644 10 28 72** en WhatsApp.
     2. Envíale: `I allow callmebot to send me messages`
     3. Recibes tu **API key** → ponla en `CALLMEBOT_APIKEY` y tu número en `CALLMEBOT_PHONE`.

3. **Encuentra el payType de tu banco** y ponlo en `BANK_PAYMENT_TYPE`:
   ```bash
   .venv/bin/python discover_paytypes.py            # lista todos los métodos
   .venv/bin/python discover_paytypes.py banco      # filtra por nombre
   ```

## Pruebas

```bash
.venv/bin/python binance_p2p.py            # lee ofertas reales
.venv/bin/python email_sender.py           # envía email de prueba
.venv/bin/python telegram_sender.py        # descubre chat_id o envía prueba
.venv/bin/python whatsapp_sender.py        # envía WhatsApp de prueba
DRY_RUN=true .venv/bin/python main.py       # ciclo completo sin enviar nada
```

## Ejecución continua (systemd)

```bash
cp p2p-monitor.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now p2p-monitor
journalctl --user -u p2p-monitor -f        # logs en vivo
```

## Configuración (`.env`)

| Variable | Descripción |
|---|---|
| `BANK_PAYMENT_TYPE` | payType de Binance del banco (descúbrelo con `discover_paytypes.py`) |
| `BANK_DISPLAY_NAME` | Nombre legible del banco que aparece en las alertas |
| `ASSET` | Cripto a comprar (ej. `USDT`) |
| `FIAT` | Moneda fiat del banco (ej. `USD`, `VES`, `PEN`) |
| `PRICE_THRESHOLD` | Alerta cuando el precio ≤ este valor (en `FIAT`) |
| `ORDER_AMOUNT_USD` | Filtra ofertas que permitan comprar este monto (en `FIAT`) |
| `POLL_INTERVAL_SECONDS` | Frecuencia de chequeo |
| `COOLDOWN_MINUTES` | Evita alertas repetidas |
| `EMAIL_ENABLED` / `TELEGRAM_ENABLED` / `WHATSAPP_ENABLED` | Activa cada canal |
| `DRY_RUN` | `true` = loguea sin enviar nada |
