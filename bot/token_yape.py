import html
import requests
from telebot import types


# =========================================================
# CONFIGURACIÓN
# =========================================================

API_CREAR_TOKEN = "https://server-yape.vercel.app/api/xpress/create_token"
API_DESCONTAR = "https://activaciones.vercel.app/api/deduct_credits"

API_KEY = "MELEYS"

ADMIN_IDS = [
    8635600472
]

# Precio de cada token
COSTOS_TOKEN = {
    7: 5,
    15: 10,
    30: 15
}

# Selección temporal de cada usuario
SELECCION_TOKEN = {}


# =========================================================
# TEXTO DEL MENÚ
# =========================================================

def texto_menu(obj, dias):

    usuario = obj.from_user

    username = (
        f"@{usuario.username}"
        if usuario.username
        else usuario.first_name or "Sin username"
    )

    costo = COSTOS_TOKEN.get(dias, 0)

    return (
        "<b>[#YapeXpress] ➣ GENERAR TOKEN</b>\n\n"

        "👨‍💼 <b>| TU ESTADO</b>\n"
        f"- Usuario ➣ {html.escape(username)}\n\n"

        "⚙️ <b>| CONFIGURACIÓN</b>\n"
        f"- Duración ➣ <b>{dias} días</b>\n"
        f"- Costo ➣ <b>{costo} créditos</b>\n\n"

        "📌 <b>| INFORMACIÓN</b>\n"
        "- Selecciona la duración del token.\n"
        "- Luego presiona generar."
    )


# =========================================================
# BOTONERA PRINCIPAL
# =========================================================

def teclado_token(user_id):

    dias = SELECCION_TOKEN.get(user_id, 7)

    teclado = types.InlineKeyboardMarkup(row_width=2)

    btn7 = types.InlineKeyboardButton(
        "✅ 7 días • 5 créditos"
        if dias == 7
        else "⬜ 7 días • 5 créditos",
        callback_data="token_dias_7"
    )

    btn15 = types.InlineKeyboardButton(
        "✅ 15 días • 10 créditos"
        if dias == 15
        else "⬜ 15 días • 10 créditos",
        callback_data="token_dias_15"
    )

    btn30 = types.InlineKeyboardButton(
        "✅ 30 días • 15 créditos"
        if dias == 30
        else "⬜ 30 días • 15 créditos",
        callback_data="token_dias_30"
    )

    generar = types.InlineKeyboardButton(
        "🎟 GENERAR TOKEN",
        callback_data="token_generar"
    )

    cancelar = types.InlineKeyboardButton(
        "❌ CANCELAR",
        callback_data="token_cancelar"
    )

    teclado.add(btn7)
    teclado.add(btn15)
    teclado.add(btn30)
    teclado.add(generar)
    teclado.add(cancelar)

    return teclado


# =========================================================
# BOTONERA TOKEN GENERADO
# =========================================================

def teclado_final():

    teclado = types.InlineKeyboardMarkup()

    teclado.add(
        types.InlineKeyboardButton(
            "🔄 GENERAR OTRO",
            callback_data="token_volver"
        )
    )

    teclado.add(
        types.InlineKeyboardButton(
            "❌ CERRAR",
            callback_data="token_cancelar"
        )
    )

    return teclado


# =========================================================
# REGISTRAR COMANDOS
# =========================================================

def registrar_token_yape(bot):

    # =====================================================
    # /token
    # =====================================================

    @bot.message_handler(commands=["token"])
    def comando_token(message):

        user_id = message.from_user.id

        if user_id not in ADMIN_IDS:
            bot.reply_to(
                message,
                "❌ <b>No tienes permisos para usar este comando.</b>"
            )
            return

        SELECCION_TOKEN[user_id] = 7

        bot.send_message(
            message.chat.id,
            texto_menu(message, 7),
            reply_markup=teclado_token(user_id),
            parse_mode="HTML"
        )

    # =====================================================
    # FUNCIÓN CAMBIAR DÍAS
    # =====================================================

    def cambiar_dias(call, dias):

        user_id = call.from_user.id

        if user_id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ No tienes permisos.",
                show_alert=True
            )

            return

        SELECCION_TOKEN[user_id] = dias

        try:
            bot.edit_message_text(
                texto_menu(call, dias),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_token(user_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

        bot.answer_callback_query(
            call.id,
            f"✅ {dias} días seleccionado"
        )

    # =====================================================
    # 7 DÍAS
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_dias_7"
    )
    def seleccionar_7(call):
        cambiar_dias(call, 7)

    # =====================================================
    # 15 DÍAS
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_dias_15"
    )
    def seleccionar_15(call):
        cambiar_dias(call, 15)

    # =====================================================
    # 30 DÍAS
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_dias_30"
    )
    def seleccionar_30(call):
        cambiar_dias(call, 30)

    # =====================================================
    # GENERAR TOKEN
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_generar"
    )
    def generar_token(call):

        user_id = call.from_user.id

        if user_id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ No tienes permisos.",
                show_alert=True
            )

            return

        dias = SELECCION_TOKEN.get(user_id, 7)
        costo = COSTOS_TOKEN[dias]

        bot.answer_callback_query(
            call.id,
            "⏳ Generando token..."
        )

        # =================================================
        # PASO 1: GENERAR TOKEN
        # =================================================

        try:

            respuesta_token = requests.post(
                API_CREAR_TOKEN,
                headers={
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "days": dias
                },
                timeout=20
            )

        except requests.exceptions.RequestException as error:

            bot.edit_message_text(
                "❌ <b>No se pudo conectar con la API de tokens.</b>\n\n"
                f"<code>{html.escape(str(error))}</code>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_final(),
                parse_mode="HTML"
            )

            return

        # =================================================
        # COMPROBAR RESPUESTA
        # =================================================

        if not respuesta_token.ok:

            bot.edit_message_text(
                "❌ <b>ERROR AL GENERAR TOKEN</b>\n\n"
                f"📡 Código ➣ <code>{respuesta_token.status_code}</code>\n\n"
                f"<code>{html.escape(respuesta_token.text[:1500])}</code>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_final(),
                parse_mode="HTML"
            )

            return

        try:
            data = respuesta_token.json()
        except ValueError:

            bot.edit_message_text(
                "❌ <b>La API de tokens no devolvió JSON válido.</b>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_final(),
                parse_mode="HTML"
            )

            return

        # =================================================
        # BUSCAR TOKEN
        # =================================================

        token = (
            data.get("token")
            or data.get("key")
            or data.get("license")
            or data.get("licenseKey")
        )

        # Buscar dentro de data
        if not token and isinstance(data.get("data"), dict):

            token = (
                data["data"].get("token")
                or data["data"].get("key")
                or data["data"].get("license")
                or data["data"].get("licenseKey")
            )

        if not token:

            bot.edit_message_text(
                "❌ <b>La API respondió pero no encontré el token.</b>\n\n"
                f"<code>{html.escape(str(data)[:1500])}</code>",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_final(),
                parse_mode="HTML"
            )

            return

        # =================================================
        # PASO 2: DESCONTAR CRÉDITOS
        # =================================================

        try:

            respuesta_creditos = requests.post(
                API_DESCONTAR,
                json={
                    "telegramId": str(user_id),
                    "amount": costo
                },
                timeout=15
            )

        except requests.exceptions.RequestException as error:

            bot.edit_message_text(
                "⚠️ <b>EL TOKEN FUE GENERADO</b>\n\n"
                "Pero ocurrió un error al conectar con "
                "la API de créditos.\n\n"
                f"<code>{html.escape(str(error))}</code>",
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )

            return

        # =================================================
        # ERROR AL DESCONTAR
        # =================================================

        if not respuesta_creditos.ok:

            try:

                error_data = respuesta_creditos.json()

                mensaje_error = (
                    error_data.get("message")
                    or error_data.get("error")
                    or respuesta_creditos.text
                )

            except ValueError:

                mensaje_error = respuesta_creditos.text

            bot.edit_message_text(
                "❌ <b>NO SE PUDIERON DESCONTAR LOS CRÉDITOS</b>\n\n"

                f"📅 Duración ➣ <b>{dias} días</b>\n"
                f"💰 Costo ➣ <b>{costo} créditos</b>\n\n"

                f"📝 {html.escape(str(mensaje_error))}\n\n"

                "💳 Para comprar créditos usa /buy",

                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_final(),
                parse_mode="HTML"
            )

            return

        # =================================================
        # TOKEN + CRÉDITOS OK
        # =================================================

        token_seguro = html.escape(str(token))

        texto_final = (
            "✨ <b>| YAPE AUTOCOMPLETADO</b>\n\n"

            f"Token de autocompletado por "
            f"<b>{dias} días</b> generado:\n\n"

            f"<blockquote><code>{token_seguro}</code></blockquote>\n\n"

            "📲 <b>| ¿CÓMO ACTIVARLO?</b>\n"
            "1. Presiona el ícono de la personita 👤\n"
            "2. Ingresa a Configuración\n"
            "3. Busca el apartado \"Autocompletado\"\n"
            "4. Pega el token y confirma la activación\n\n"

            "⚡ <b>| IMPORTANTE</b>\n"
            "- El token no tiene fecha de vencimiento.\n"
            "- El token es válido para una única activación.\n"
            f"- Duración del servicio: <b>{dias} días</b>.\n\n"

            f"💰 Créditos usados ➣ <b>{costo}</b>"
        )

        bot.edit_message_text(
            texto_final,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=teclado_final(),
            parse_mode="HTML"
        )

    # =====================================================
    # GENERAR OTRO
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_volver"
    )
    def token_volver(call):

        user_id = call.from_user.id

        if user_id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ No tienes permisos.",
                show_alert=True
            )

            return

        SELECCION_TOKEN[user_id] = 7

        try:

            bot.edit_message_text(
                texto_menu(call, 7),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_token(user_id),
                parse_mode="HTML"
            )

        except Exception:
            pass

        bot.answer_callback_query(call.id)

    # =====================================================
    # CANCELAR
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_cancelar"
    )
    def cancelar(call):

        SELECCION_TOKEN.pop(
            call.from_user.id,
            None
        )

        bot.answer_callback_query(
            call.id,
            "❌ Cerrado"
        )

        try:

            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )

        except Exception:
            pass
