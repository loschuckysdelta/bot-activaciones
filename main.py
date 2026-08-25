import telebot

from bot.start import registrar_start
from bot.register import registrar_register
from bot.me import registrar_me
from bot.activate import registrar_activate
from bot.cmds import registrar_cmds
from bot.buy import registrar_buy
from bot.dar import registrar_dar
from bot.beta import registrar_beta


# =========================
# CONFIGURACIÓN DEL BOT
# =========================

TOKEN = "8792179780:AAEWRReycQpJKfVNMYp-rJYX3x2G9kuAhks"

bot = telebot.TeleBot(
    TOKEN,
    parse_mode="HTML"
)


# =========================
# REGISTRAR COMANDOS
# =========================

registrar_start(bot)
registrar_register(bot)
registrar_me(bot)
registrar_activate(bot)
registrar_cmds(bot)
registrar_buy(bot)
registrar_dar(bot)
registrar_beta(bot)


# =========================
# INICIAR BOT
# =========================

if __name__ == "__main__":
    print("🤖 Bot iniciado correctamente.")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )