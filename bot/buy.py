import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

def registrar_buy(bot):

    # URLs de las imágenes
    IMG_INICIAL = "https://i.postimg.cc/kgfSZ9x4/image.png"
    IMG_ACTIVACIONES = "https://i.postimg.cc/zBjFynjv/image.png"
    IMG_VOUCHERS = "https://i.postimg.cc/pr4jTd1T/image.png"

    # Textos
    TEXTO_INICIAL = (
        "💳 <b>TARIFARIO Y PLANES DISPONIBLES</b>\n"
        "•···························•····························•\n\n"
        "🎯 Selecciona una de las opciones del menú:\n\n"
        "•···························•····························•"
    )

    TEXTO_ACTIVACIONES = (
        "🔪 <b>LOS CHUCKYS — COMPRA DE CRÉDITOS</b>\n"
        "•···························•····························•\n\n"
        "🪙 <b>50 CRÉDITOS</b> — S/ 50\n"
        "🪙 <b>100 CRÉDITOS</b> — S/ 95 (🔥 5% de ahorro)\n"
        "🪙 <b>200 CRÉDITOS</b> — S/ 180 (🔥 10% de ahorro)\n"
        "🪙 <b>500 CRÉDITOS</b> — S/ 400 (🔥 20% de ahorro)\n\n"
        "✅ Compra segura | ⚡ Entrega inmediata\n\n"
        "•···························•····························•\n\n"
        "🛒 <b>Selecciona el paquete que deseas comprar 👇</b>"
    )

    TEXTO_VOUCHERS = (
        "⚡ <b>PLANES DISPONIBLES - VOUCHERS</b> ⚡\n"
        "•···························•····························•\n\n"
        "🔥 <b>OFERTA ESPECIAL:</b>\n"
        "🟢 <b>30 DÍAS — S/ 5</b> (¡Disponible!)\n\n"
        "❌ <b>7 DÍAS — S/ 3</b> (AGOTADO)\n"
        "❌ <b>15 DÍAS — S/ 10</b> (AGOTADO)\n\n"
        "💜 <b>VOUCHERS DISPONIBLES:</b>\n"
        "Yape • Plin • BIM • SIP • Agora • Prexpe • Panda • BCP • Interbank • BBVA • Banco Ripley • Banco Falabella • Caja Arequipa • Scotiabank\n\n"
        "•···························•····························•\n\n"
        "🛒 <b>Haz clic en el botón de abajo para comprar 👇</b>"
    )

    # Caché de archivos ya alojados en Telegram: evita subir imágenes en cada toque.
    cache_fotos = {}
    bloqueo_fotos = threading.Lock()
    urls_fotos = {
        "inicial": IMG_INICIAL,
        "activaciones": IMG_ACTIVACIONES,
        "vouchers": IMG_VOUCHERS,
    }

    def obtener_foto(nombre):
        # La primera vez se usa la URL; después, el file_id de Telegram.
        with bloqueo_fotos:
            return cache_fotos.get(nombre, urls_fotos[nombre])

    def guardar_foto(nombre, mensaje):
        fotos = getattr(mensaje, "photo", None)
        if fotos:
            with bloqueo_fotos:
                cache_fotos[nombre] = fotos[-1].file_id

    # --- BOTONERAS ---
    def teclado_inicial():
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="🚀 Bot de Activaciones (Créditos)", callback_data="buy_activaciones"))
        markup.add(InlineKeyboardButton(text="⚡ Bot de Vouchers", callback_data="buy_vouchers"))
        return markup

    def teclado_activaciones():
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(
            text="🪙 50 Créditos — S/ 50", 
            url="https://t.me/tuchuckynet_x?text=Hola%2C%20quiero%20comprar%2050%20cr%C3%A9ditos%20por%20S%2F%2050"
        ))
        markup.add(InlineKeyboardButton(
            text="🪙 100 Créditos — S/ 95 (5% dto)", 
            url="https://t.me/tuchuckynet_x?text=Hola%2C%20quiero%20comprar%20100%20cr%C3%A9ditos%20por%20S%2F%2095"
        ))
        markup.add(InlineKeyboardButton(
            text="🪙 200 Créditos — S/ 180 (10% dto)", 
            url="https://t.me/tuchuckynet_x?text=Hola%2C%20quiero%20comprar%20200%20cr%C3%A9ditos%20por%20S%2F%20180"
        ))
        markup.add(InlineKeyboardButton(
            text="🪙 500 Créditos — S/ 400 (20% dto)", 
            url="https://t.me/tuchuckynet_x?text=Hola%2C%20quiero%20comprar%20500%20cr%C3%A9ditos%20por%20S%2F%20400"
        ))
        markup.add(InlineKeyboardButton(text="🏠 Menú Principal", callback_data="buy_inicio"))
        return markup

    def teclado_vouchers():
        markup = InlineKeyboardMarkup()
        # Botón directo para la oferta de 30 días por S/ 5
        markup.add(InlineKeyboardButton(
            text="🔥 Oferta 30 Días — S/ 5", 
            url="https://t.me/tuchuckynet_x?text=Hola%2C%20quiero%20adquirir%20la%20oferta%20de%20Vouchers%20de%2030%20d%C3%ADas%20por%20S%2F%205"
        ))
        markup.add(InlineKeyboardButton(text="🏠 Menú Principal", callback_data="buy_inicio"))
        return markup

    # Comando inicial
    @bot.message_handler(commands=["buy", "comprar", "precios"])
    def buy(message):
        try:
            resultado = bot.send_photo(
                message.chat.id,
                photo=obtener_foto("inicial"),
                caption=TEXTO_INICIAL,
                parse_mode="HTML",
                reply_markup=teclado_inicial()
            )
            guardar_foto("inicial", resultado)
        except Exception as error:
            print(f"[BUY] No se pudo enviar la foto: {error}")
            bot.send_message(
                message.chat.id,
                TEXTO_INICIAL,
                parse_mode="HTML",
                reply_markup=teclado_inicial()
            )

    # Manejador ultrarrápido
    @bot.callback_query_handler(func=lambda call: bool(call.data) and call.data.startswith("buy_"))
    def callback_buy_plans(call):
        # El aviso de Telegram no espera a que termine la actualización de imagen.
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        opciones = {
            "buy_inicio": ("inicial", TEXTO_INICIAL, teclado_inicial),
            "buy_activaciones": ("activaciones", TEXTO_ACTIVACIONES, teclado_activaciones),
            "buy_vouchers": ("vouchers", TEXTO_VOUCHERS, teclado_vouchers),
        }
        opcion = opciones.get(call.data)
        if not opcion:
            return
        nombre, texto, teclado = opcion
        contenido = getattr(call.message, "content_type", "photo")
        try:
            if contenido == "text":
                # Si /buy utilizó el respaldo de texto, los botones también funcionan.
                bot.edit_message_text(
                    texto, chat_id, message_id,
                    parse_mode="HTML", reply_markup=teclado()
                )
            else:
                resultado = bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=InputMediaPhoto(
                        obtener_foto(nombre), caption=texto, parse_mode="HTML"
                    ),
                    reply_markup=teclado()
                )
                guardar_foto(nombre, resultado)
        except Exception as error:
            print(f"[BUY] No se pudo cambiar la foto: {error}")
            # Respaldo: conservar todos los textos y botones incluso si la foto falla.
            try:
                if contenido == "text":
                    bot.send_message(chat_id, texto, parse_mode="HTML", reply_markup=teclado())
                else:
                    bot.edit_message_caption(
                        chat_id=chat_id, message_id=message_id,
                        caption=texto, parse_mode="HTML", reply_markup=teclado()
                    )
            except Exception as error_respaldo:
                print(f"[BUY] Tampoco se pudo actualizar el respaldo: {error_respaldo}")
