from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def registrar_cmds(bot):

    # URL de tu imagen en Postimages
    URL_IMAGEN = "https://i.postimg.cc/5tLCt1w2/image.png"

    # Textos de las secciones
    TEXTO_PRINCIPAL = (
        "📋 <b>COMANDOS DISPONIBLES</b>\n\n"
        "Selecciona una sección:"
    )

    TEXTO_ACTIVACIONES = (
        "🚀 <b>ACTIVACIONES YAPE</b>\n\n"
        "/activate correo@gmail.com\n"
        "Activa una cuenta de un cliente registrado.\n\n"
        "/token\n"
        "Genera token de autocompletado.\n\n"
        "/info correo@gmail.com\n"
        "Ver información del cliente.\n\n"
        "/historial\n"
        "Ver el historial de tus activaciones."
    )

    TEXTO_VOUCHERS = (
        "🧾 <b>PLAN VOUCHERS</b>\n\n"
        "/ejemplos\n"
        "Ver galería de ejemplos.\n\n"
        "/yape monto|nombre|3digitos\n"
        "/plin monto|nombre|3digitos\n"
        "/bim monto|nombre|3digitos\n"
        "/sip monto|nombre|3digitos\n"
        "/agora monto|nombre|3digitos\n"
        "/lemon monto|nombre|3digitos\n"
        "/panda monto|nombre\n"
        "/prexpe monto|nombre\n"
        "/bcp monto|nombre|3digitos\n"
        "/ibk monto|nombre|3digitos\n"
        "/bbva monto|nombre|3digitos\n"
        "/scotiabank monto|nombre|3digitos\n"
        "/falabella monto|nombre|3digitos\n"
        "/ripley monto|nombre|3digitos\n"
        "/caja monto|nombre|3digitos\n"
        "Genera vouchers de pago."
    )

    # Teclados
    def teclado_principal():
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚀 ACTIVACIONES YAPE", callback_data="menu_activaciones"))
        markup.add(InlineKeyboardButton("⭐ PLAN VOUCHERS", callback_data="menu_vouchers"))
        return markup

    def teclado_activaciones():
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💰 Comprar créditos", url="https://t.me/tu_enlace_de_compra"))
        markup.add(InlineKeyboardButton("🔙 Volver", callback_data="menu_principal"))
        return markup

    def teclado_vouchers():
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⭐ Adquirir plan de vouchers", url="https://t.me/tu_enlace_de_compra"))
        markup.add(InlineKeyboardButton("🔙 Volver", callback_data="menu_principal"))
        return markup

    # Comando /cmds (y alias)
    @bot.message_handler(commands=["cmds", "commands", "help"])
    def cmds(message):
        bot.send_photo(
            message.chat.id,
            photo=URL_IMAGEN,
            caption=TEXTO_PRINCIPAL,
            parse_mode="HTML",
            reply_markup=teclado_principal()
        )

    # Manejador de los botones inline
    @bot.callback_query_handler(func=lambda call: bool(call.data) and call.data.startswith("menu_"))
    def callback_menu(call):
        # Confirmar el toque inmediatamente para quitar la rueda de espera.
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        message_id = call.message.message_id

        opciones = {
            "menu_activaciones": (TEXTO_ACTIVACIONES, teclado_activaciones),
            "menu_vouchers": (TEXTO_VOUCHERS, teclado_vouchers),
            "menu_principal": (TEXTO_PRINCIPAL, teclado_principal),
        }
        opcion = opciones.get(call.data)
        if not opcion:
            return
        texto, teclado = opcion
        try:
            # Todas las secciones comparten la misma foto: solo actualizar el pie.
            bot.edit_message_caption(
                chat_id=chat_id,
                message_id=message_id,
                caption=texto,
                parse_mode="HTML",
                reply_markup=teclado()
            )
        except Exception as error:
            # Si Telegram no permite editar (mensaje viejo/sin foto), no bloquear el bot.
            print(f"[CMDS] No se pudo actualizar el menú: {error}")
