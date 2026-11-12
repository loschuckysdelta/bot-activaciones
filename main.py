"""Arranque de bot de Telegram (sin .env).

1. Instala: py -m pip install -r requirements.txt
2. Pega un token NUEVO: py main.py
"""
import logging

# Coloca aquí un token recién generado en @BotFather.
# Importante: el token del ZIP original quedó expuesto; revócalo.
TOKEN = "8792179780:AAGVXCW6B9F4CmU-NIVDxwMCN6rhw8GvGiw"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def iniciar():
    if not TOKEN.strip() or TOKEN.startswith("PEGA_AQUI"):
        raise SystemExit("❌ Pega tu token NUEVO de BotFather en TOKEN de main.py")

    try:
        import telebot
    except ImportError as exc:
        raise SystemExit(
            "❌ Falta pyTelegramBotAPI. Instala con: py -m pip install -r requirements.txt"
        ) from exc

    from bot.start import registrar_start
    from bot.register import registrar_register
    from bot.me import registrar_me
    from bot.activate import registrar_activate
    from bot.cmds import registrar_cmds
    from bot.buy import registrar_buy
    from bot.dar import registrar_dar
    from bot.beta import registrar_beta
    from bot.token_yape import registrar_token_yape

    bot = telebot.TeleBot(TOKEN.strip(), parse_mode="HTML", threaded=True, num_threads=8)
    registrar_start(bot)
    registrar_register(bot)
    registrar_me(bot)
    registrar_activate(bot)
    registrar_cmds(bot)
    registrar_buy(bot)
    registrar_dar(bot)
    registrar_beta(bot)
    registrar_token_yape(bot)

    logging.info("🤖 Bot iniciado. Conectando a Telegram...")
    try:
        bot.remove_webhook()
    except Exception as exc:
        logging.warning("No se pudo eliminar un webhook anterior: %s", exc)
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)


if __name__ == "__main__":
    iniciar()
