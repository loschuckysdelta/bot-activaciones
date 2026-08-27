import html
import requests
from telebot import types


# =========================================================
# CONFIGURACIÓN
# =========================================================

API_URL = "https://server-yape.vercel.app/api/xpress/create_token"
API_KEY = "MELEYS"

# IDs que pueden generar tokens
ADMIN_IDS = [
    8635600472
]

# Guarda la duración seleccionada por cada usuario
SELECCION_TOKEN = {}


# =========================================================
# OBTENER USUARIO
# =========================================================

def obtener_usuario(obj):
    return obj.from_user


# =========================================================
# MENÚ PRINCIPAL
# =========================================================

def texto_menu(obj, dias):

    usuario = obtener_usuario(obj)

    if usuario.username:
        username = f"@{usuario.username}"
    else:
        username = usuario.first_name or "Sin username"

    return (
        "<b>[#YapeXpress] ➣ GENERAR TOKEN</b>\n\n"

        "👨‍💼 <b>| TU ESTADO</b>\n"
        f"- Usuario ➣ {html.escape(username)}\n"
        "- Saldo ➣ ∞ ILIMITADO\n\n"

        "⚙️ <b>| CONFIGURACIÓN</b>\n"
        f"- Duración ➣ <b>{dias} días</b>\n\n"

        "📌 <b>| INFORMACIÓN</b>\n"
        "- Selecciona la duración del token.\n"
        "- Luego presiona generar."
    )


# =========================================================
# BOTONERA
# =========================================================

def teclado_token(user_id):

    dias = SELECCION_TOKEN.get(user_id, 7)

    teclado = types.InlineKeyboardMarkup(row_width=2)

    boton_7 = types.InlineKeyboardButton(
        "✅ 7 días" if dias == 7 else "⬜ 7 días",
        callback_data="token_dias_7"
    )

    boton_15 = types.InlineKeyboardButton(
        "✅ 15 días" if dias == 15 else "⬜ 15 días",
        callback_data="token_dias_15"
    )

    boton_30 = types.InlineKeyboardButton(
        "✅ 30 días" if dias == 30 else "⬜ 30 días",
        callback_data="token_dias_30"
    )

    boton_generar = types.InlineKeyboardButton(
        "🎟 GENERAR TOKEN",
        callback_data="token_generar"
    )

    boton_cancelar = types.InlineKeyboardButton(
        "❌ CANCELAR",
        callback_data="token_cancelar"
    )

    teclado.add(
        boton_7,
        boton_15
    )

    teclado.add(
        boton_30
    )

    teclado.add(
        boton_generar
    )

    teclado.add(
        boton_cancelar
    )

    return teclado


# =========================================================
# BOTONERA DESPUÉS DE GENERAR
# =========================================================

def teclado_token_generado():

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
# REGISTRAR TOKEN YAPE
# =========================================================

def registrar_token_yape(bot):

    # =====================================================
    # /token
    # =====================================================

    @bot.message_handler(commands=["token"])
    def comando_token(message):

        user_id = message.from_user.id

        # SOLO ADMIN
        if user_id not in ADMIN_IDS:

            bot.reply_to(
                message,
                "❌ <b>No tienes permisos para usar este comando.</b>"
            )

            return

        # Por defecto 7 días
        SELECCION_TOKEN[user_id] = 7

        bot.send_message(
            message.chat.id,
            texto_menu(message, 7),
            reply_markup=teclado_token(user_id),
            parse_mode="HTML"
        )

    # =====================================================
    # SELECCIONAR 7 DÍAS
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_dias_7"
    )
    def seleccionar_7(call):

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

        bot.answer_callback_query(
            call.id,
            "✅ 7 días seleccionado"
        )

    # =====================================================
    # SELECCIONAR 15 DÍAS
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_dias_15"
    )
    def seleccionar_15(call):

        user_id = call.from_user.id

        if user_id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ No tienes permisos.",
                show_alert=True
            )

            return

        SELECCION_TOKEN[user_id] = 15

        try:

            bot.edit_message_text(
                texto_menu(call, 15),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_token(user_id),
                parse_mode="HTML"
            )

        except Exception:
            pass

        bot.answer_callback_query(
            call.id,
            "✅ 15 días seleccionado"
        )

    # =====================================================
    # SELECCIONAR 30 DÍAS
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_dias_30"
    )
    def seleccionar_30(call):

        user_id = call.from_user.id

        if user_id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ No tienes permisos.",
                show_alert=True
            )

            return

        SELECCION_TOKEN[user_id] = 30

        try:

            bot.edit_message_text(
                texto_menu(call, 30),
                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_token(user_id),
                parse_mode="HTML"
            )

        except Exception:
            pass

        bot.answer_callback_query(
            call.id,
            "✅ 30 días seleccionado"
        )

    # =====================================================
    # GENERAR TOKEN
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_generar"
    )
    def generar_token(call):

        user_id = call.from_user.id

        # SOLO ADMIN
        if user_id not in ADMIN_IDS:

            bot.answer_callback_query(
                call.id,
                "❌ No tienes permisos.",
                show_alert=True
            )

            return

        # Obtener días seleccionados
        dias = SELECCION_TOKEN.get(user_id, 7)

        bot.answer_callback_query(
            call.id,
            "⏳ Generando token..."
        )

        try:

            # =================================================
            # PETICIÓN API
            # =================================================

            response = requests.post(
                API_URL,
                headers={
                    "x-api-key": API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "days": dias
                },
                timeout=20
            )

            # =================================================
            # ERROR HTTP
            # =================================================

            if not response.ok:

                respuesta_error = html.escape(
                    response.text[:1500]
                )

                bot.edit_message_text(
                    "❌ <b>| ERROR AL GENERAR TOKEN</b>\n\n"

                    f"📡 Código ➣ "
                    f"<code>{response.status_code}</code>\n\n"

                    "📝 Respuesta:\n"
                    f"<code>{respuesta_error}</code>",

                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML"
                )

                return

            # =================================================
            # LEER JSON
            # =================================================

            try:

                data = response.json()

            except ValueError:

                respuesta = html.escape(
                    response.text[:1500]
                )

                bot.edit_message_text(
                    "❌ <b>La API no devolvió JSON válido.</b>\n\n"
                    f"<code>{respuesta}</code>",

                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode="HTML"
                )

                return

            # =================================================
            # BUSCAR TOKEN EN RESPUESTA
            # =================================================

            token = (
                data.get("token")
                or data.get("key")
                or data.get("license")
                or data.get("licenseKey")
            )

            # Algunas APIs meten el token dentro de data
            if not token and isinstance(data.get("data"), dict):

                token = (
                    data["data"].get("token")
                    or data["data"].get("key")
                    or data["data"].get("license")
                    or data["data"].get("licenseKey")
                )

            # =================================================
            # SI NO ENCUENTRA TOKEN
            # =================================================

            if not token:

                respuesta = html.escape(
                    str(data)[:2000]
                )

                bot.edit_message_text(
                    "⚠️ <b>| RESPUESTA DE LA API</b>\n\n"

                    "La API respondió correctamente, "
                    "pero no encontré el campo del token.\n\n"

                    f"<code>{respuesta}</code>",

                    call.message.chat.id,
                    call.message.message_id,
                    reply_markup=teclado_token_generado(),
                    parse_mode="HTML"
                )

                return

            # Escapar token para HTML
            token_seguro = html.escape(str(token))

            # =================================================
            # MENSAJE FINAL
            # =================================================

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
                f"- Duración del servicio: <b>{dias} días</b>."
            )

            bot.edit_message_text(
                texto_final,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_token_generado(),
                parse_mode="HTML"
            )

        # =====================================================
        # TIMEOUT
        # =====================================================

        except requests.exceptions.Timeout:

            bot.edit_message_text(
                "❌ <b>La API tardó demasiado en responder.</b>\n\n"
                "Intenta nuevamente.",

                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_token_generado(),
                parse_mode="HTML"
            )

        # =====================================================
        # ERROR DE CONEXIÓN
        # =====================================================

        except requests.exceptions.RequestException as error:

            error_seguro = html.escape(str(error))

            bot.edit_message_text(
                "❌ <b>Error de conexión con la API.</b>\n\n"
                f"<code>{error_seguro}</code>",

                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_token_generado(),
                parse_mode="HTML"
            )

        # =====================================================
        # OTRO ERROR
        # =====================================================

        except Exception as error:

            error_seguro = html.escape(str(error))

            bot.edit_message_text(
                "❌ <b>Error inesperado.</b>\n\n"
                f"<code>{error_seguro}</code>",

                call.message.chat.id,
                call.message.message_id,
                reply_markup=teclado_token_generado(),
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
    # CANCELAR / CERRAR
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data == "token_cancelar"
    )
    def token_cancelar(call):

        user_id = call.from_user.id

        SELECCION_TOKEN.pop(
            user_id,
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