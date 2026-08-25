from telebot import types

def registrar_start(bot):

    @bot.message_handler(commands=["start"])
    def start(message):
        teclado = types.InlineKeyboardMarkup(row_width=2)

        # Botones con enlaces directos (URL)
        btn_web = types.InlineKeyboardButton("🌐 WEB (Android/IPhone)", url="https://tu-sitio-web.com")
        btn_apk = types.InlineKeyboardButton("⬇️ APK (Android)", url="https://tu-enlace-apk.com")
        btn_comprar = types.InlineKeyboardButton("💰 Comprar créditos", url="https://t.me/dev_lguss")

        teclado.add(btn_web, btn_apk)
        teclado.add(btn_comprar)

        # URL de la imagen actualizada
        foto_banner = "https://i.postimg.cc/3wrnmCrv/image.png" 

        caption_texto = (
            f"Hola, que tal <b>{message.from_user.first_name or 'usuario'}</b>? Bienvenido a <b>YapeXpress</b>!\n\n"
            "Para utilizar este bot primero debes registrarte utilizando:\n"
            "/register\n\n"
            "[ 👤 ] Para visualizar tu perfil /me\n"
            "[ 🧾 ] Para visualizar comandos /cmds\n"
            "[ 💰 ] Para visualizar los precios /buy\n"
            "[ ❓ ] Si tienes alguna consulta respecto a <b>YapeXpress</b> puedes contactar con (@dev_lguss)"
        )

        bot.send_photo(
            message.chat.id,
            photo=foto_banner,
            caption=caption_texto,
            parse_mode="HTML",
            reply_markup=teclado
        )