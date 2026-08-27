from telebot import types


def registrar_start(bot):

    @bot.message_handler(commands=["start"])
    def start(message):
        teclado = types.InlineKeyboardMarkup(row_width=2)

        # Botones con enlaces directos
        btn_web = types.InlineKeyboardButton(
            "🌐 WEB (Android/IPhone)",
            url="https://ypfk-plus.vercel.app/"
        )

        btn_apk = types.InlineKeyboardButton(
            "⬇️ APK (Android)",
            url="https://tu-enlace-apk.com"
        )

        btn_comprar = types.InlineKeyboardButton(
            "💰 Comprar créditos",
            url="https://t.me/tuchuckynet_x"
        )

        teclado.add(btn_web, btn_apk)
        teclado.add(btn_comprar)

        foto_banner = "https://i.postimg.cc/3wrnmCrv/image.png"

        nombre = message.from_user.first_name or "usuario"

        caption_texto = (
            f"Hola, ¿qué tal <b>{nombre}</b>? Bienvenido a <b>YapeXpress</b>!\n\n"
            "Para utilizar este bot primero debes registrarte utilizando:\n"
            "/register\n\n"
            "[ 👤 ] Para visualizar tu perfil /me\n"
            "[ 🧾 ] Para visualizar comandos /cmds\n"
            "[ 💰 ] Para visualizar los precios /buy\n"
            "[ ❓ ] Si tienes alguna consulta respecto a <b>YapeXpress</b> "
            "puedes contactar con @tuchuckynet_x"
        )

        bot.send_photo(
            message.chat.id,
            photo=foto_banner,
            caption=caption_texto,
            parse_mode="HTML",
            reply_markup=teclado
        )