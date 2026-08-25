import os
import uuid
import requests
from telebot import types


# =========================================================
# CONFIGURACIÓN
# =========================================================

URL_IMAGEN = "https://i.postimg.cc/PqxzbJ4Z/image.png"

# API DE LICENCIAS
API_INFO_USER = (
    "https://server-yape.vercel.app/api/chucky/info_user"
)

API_ACTIVATE_USER = (
    "https://server-yape.vercel.app/api/chucky/activate_user"
)

# API DE CRÉDITOS
API_PANEL = "https://activaciones.vercel.app"

API_USER = f"{API_PANEL}/api/user"
API_DEDUCT_CREDITS = f"{API_PANEL}/api/deduct_credits"


# =========================================================
# PRECIOS
# =========================================================

PRECIO_YAPE = 15
PRECIO_BCP = 7
PRECIO_IBK = 7
PRECIO_BBVA = 7


# =========================================================
# IMAGEN
# =========================================================

CARPETA_IMAGENES = "assets/imagenes"
NOMBRE_ARCHIVO = "logo_activacion.png"

RUTA_IMAGEN = os.path.join(
    CARPETA_IMAGENES,
    NOMBRE_ARCHIVO
)

FILE_ID_CACHE = None


# =========================================================
# SESIONES TEMPORALES
# =========================================================

SESIONES = {}


# =========================================================
# HTTP SESSION
# =========================================================

http = requests.Session()


# =========================================================
# ASEGURAR IMAGEN
# =========================================================

def asegurar_imagen():

    if not os.path.exists(CARPETA_IMAGENES):

        os.makedirs(
            CARPETA_IMAGENES,
            exist_ok=True
        )

    if os.path.exists(RUTA_IMAGEN):
        return

    try:

        respuesta = http.get(
            URL_IMAGEN,
            stream=True,
            timeout=10
        )

        if respuesta.status_code == 200:

            with open(
                RUTA_IMAGEN,
                "wb"
            ) as archivo:

                for chunk in respuesta.iter_content(
                    chunk_size=1024
                ):

                    if chunk:
                        archivo.write(chunk)

    except Exception as e:

        print(
            f"[ACTIVATE] Error descargando imagen: {e}"
        )


# =========================================================
# CONSULTAR USUARIO DE LICENCIAS
# =========================================================

def consultar_usuario_yape(correo):

    try:

        respuesta = http.get(
            API_INFO_USER,
            params={
                "email": correo
            },
            timeout=10
        )

        if respuesta.status_code == 404:

            return {
                "ok": False,
                "tipo": "no_encontrado"
            }

        respuesta.raise_for_status()

        datos = respuesta.json()

        return {
            "ok": True,
            "datos": datos
        }

    except requests.RequestException as e:

        print(
            f"[ACTIVATE] Error info_user: {e}"
        )

        return {
            "ok": False,
            "tipo": "conexion"
        }

    except ValueError:

        return {
            "ok": False,
            "tipo": "json"
        }


# =========================================================
# CONVERTIR DATOS A LICENCIAS
# =========================================================

def obtener_licencias(datos):

    return {

        "yape": bool(
            datos.get("status", False)
        ),

        "bcp": bool(
            datos.get("bcp", False)
        ),

        "ibk": bool(
            datos.get("ibk", False)
        ),

        "bbva": bool(
            datos.get("bbva", False)
        )
    }


# =========================================================
# CONSULTAR CRÉDITOS TELEGRAM
# =========================================================

def consultar_creditos(telegram_id):

    try:

        respuesta = http.get(
            API_USER,
            params={
                "id": str(telegram_id)
            },
            timeout=10
        )

        if respuesta.status_code == 404:

            return {
                "ok": False,
                "tipo": "no_registrado"
            }

        respuesta.raise_for_status()

        datos = respuesta.json()

        usuario = datos.get(
            "user",
            datos.get(
                "usuario",
                datos
            )
        )

        creditos = usuario.get(
            "credits",
            usuario.get(
                "creditos",
                0
            )
        )

        try:

            creditos = int(creditos)

        except (TypeError, ValueError):

            creditos = 0

        return {
            "ok": True,
            "creditos": creditos,
            "datos": usuario
        }

    except requests.RequestException as e:

        print(
            f"[CREDITOS] Error consultando usuario: {e}"
        )

        return {
            "ok": False,
            "tipo": "conexion"
        }

    except ValueError:

        return {
            "ok": False,
            "tipo": "json"
        }


# =========================================================
# DESCONTAR CRÉDITOS
# =========================================================

def descontar_creditos(
    telegram_id,
    cantidad
):

    payload = {
        "telegramId": str(telegram_id),
        "amount": abs(cantidad)
    }

    try:

        respuesta = http.post(
            API_DEDUCT_CREDITS,
            json=payload,
            timeout=10
        )

        if respuesta.ok:

            print(
                f"[CREDITOS] Éxito al descontar en {API_DEDUCT_CREDITS} con payload: {payload}"
            )

            return True

        print(
            f"[CREDITOS] Falló status={respuesta.status_code} respuesta={respuesta.text}"
        )

    except requests.RequestException as e:

        print(
            f"[CREDITOS] Error de red en {API_DEDUCT_CREDITS}: {e}"
        )

    return False


# =========================================================
# CALCULAR PRECIO (SOLO COBRA LICENCIAS NUEVAS)
# =========================================================

def calcular_precio(
    original,
    nuevas
):

    total = 0

    if not original["yape"] and nuevas["yape"]:
        total += PRECIO_YAPE

    if not original["bcp"] and nuevas["bcp"]:
        total += PRECIO_BCP

    if not original["ibk"] and nuevas["ibk"]:
        total += PRECIO_IBK

    if not original["bbva"] and nuevas["bbva"]:
        total += PRECIO_BBVA

    return total


# =========================================================
# GENERAR TEXTO
# =========================================================

def generar_texto(
    correo,
    licencias,
    precio=0,
    creditos=0
):

    yape = "✅" if licencias["yape"] else "⬜"
    bcp = "✅" if licencias["bcp"] else "⬜"
    ibk = "✅" if licencias["ibk"] else "⬜"
    bbva = "✅" if licencias["bbva"] else "⬜"

    return (
        f"[<b>#YapeXpress</b>] ➣ ACTIVAR LICENCIAS\n\n"

        f"[📧] <b>CLIENTE</b>\n"
        f"- Correo ➣ <code>{correo}</code>\n\n"

        f"[👨‍💼] <b>TU ESTADO</b>\n"
        f"- Sistema ➣ ACTIVO\n"
        f"- Créditos ➣ <b>{creditos} disponibles</b>\n\n"

        f"[🔐] <b>LICENCIAS DISPONIBLES</b>\n"

        f"{yape} <b>YAPE</b> ➣ {PRECIO_YAPE} créditos\n"
        f"{bcp} <b>BCP</b> ➣ {PRECIO_BCP} créditos\n"
        f"{ibk} <b>INTERBANK</b> ➣ {PRECIO_IBK} créditos\n"
        f"{bbva} <b>BBVA</b> ➣ {PRECIO_BBVA} créditos\n\n"

        ""
    )


# =========================================================
# GENERAR TECLADO
# =========================================================

def generar_teclado(
    token,
    licencias
):

    teclado = types.InlineKeyboardMarkup()

    txt_yape = "✅ YAPE" if licencias["yape"] else "⬜ YAPE"
    txt_bcp = "✅ BCP" if licencias["bcp"] else "⬜ BCP"
    txt_ibk = "✅ IBK" if licencias["ibk"] else "⬜ IBK"
    txt_bbva = "✅ BBVA" if licencias["bbva"] else "⬜ BBVA"

    teclado.row(
        types.InlineKeyboardButton(
            txt_yape,
            callback_data=f"lic:yape:{token}"
        )
    )

    teclado.row(
        types.InlineKeyboardButton(
            txt_bcp,
            callback_data=f"lic:bcp:{token}"
        ),
        types.InlineKeyboardButton(
            txt_ibk,
            callback_data=f"lic:ibk:{token}"
        ),
        types.InlineKeyboardButton(
            txt_bbva,
            callback_data=f"lic:bbva:{token}"
        )
    )

    teclado.row(
        types.InlineKeyboardButton(
            "➡ CONTINUAR",
            callback_data=f"lic:confirmar:{token}"
        )
    )

    teclado.row(
        types.InlineKeyboardButton(
            "⬅️ VOLVER / SALIR",
            callback_data=f"lic:volver:{token}"
        )
    )

    teclado.row(
        types.InlineKeyboardButton(
            "❌ CANCELAR",
            callback_data=f"lic:cancelar:{token}"
        )
    )

    return teclado


# =========================================================
# REGISTRAR HANDLERS
# =========================================================

def registrar_activate(bot):

    asegurar_imagen()

    # =====================================================
    # /activate
    # =====================================================

    @bot.message_handler(commands=["activate"])
    def activate(message):

        global FILE_ID_CACHE

        args = message.text.split(maxsplit=1)

        if len(args) < 2:

            bot.reply_to(
                message,
                "⚠️ <b>USO INCORRECTO</b>\n\n"
                "Ingresa el correo:\n\n"
                "<code>/activate correo@gmail.com</code>",
                parse_mode="HTML"
            )

            return

        correo = args[1].strip().lower()

        resultado_creditos = consultar_creditos(
            message.from_user.id
        )

        if not resultado_creditos["ok"]:

            if resultado_creditos["tipo"] == "no_registrado":

                bot.reply_to(
                    message,
                    "❌ <b>NO ESTÁS REGISTRADO</b>\n\n"
                    "No se encontró tu cuenta en el sistema.",
                    parse_mode="HTML"
                )

                return

            bot.reply_to(
                message,
                "⚠️ <b>ERROR DE CRÉDITOS</b>\n\n"
                "No pude consultar tu saldo.",
                parse_mode="HTML"
            )

            return

        creditos = resultado_creditos["creditos"]

        consulta = consultar_usuario_yape(correo)

        if not consulta["ok"]:

            if consulta["tipo"] == "no_encontrado":

                bot.reply_to(
                    message,
                    "❌ <b>CORREO NO ENCONTRADO</b>\n\n"
                    f"📧 <code>{correo}</code>\n\n"
                    "El correo no existe en el sistema.",
                    parse_mode="HTML"
                )

                return

            bot.reply_to(
                message,
                "⚠️ <b>ERROR DEL SERVIDOR</b>\n\n"
                "No pude consultar las licencias.",
                parse_mode="HTML"
            )

            return

        datos = consulta["datos"]

        if datos.get("banned", False):

            bot.reply_to(
                message,
                "🚫 <b>USUARIO BLOQUEADO</b>\n\n"
                f"📧 <code>{correo}</code>\n\n"
                "No se pueden realizar activaciones.",
                parse_mode="HTML"
            )

            return

        licencias = obtener_licencias(datos)

        token = uuid.uuid4().hex[:10]

        SESIONES[token] = {
            "correo": correo,
            "telegram_id": message.from_user.id,
            "creditos": creditos,
            "licencias": licencias.copy(),
            "original": licencias.copy()
        }

        precio = calcular_precio(
            SESIONES[token]["original"],
            SESIONES[token]["licencias"]
        )

        texto = generar_texto(
            correo,
            licencias,
            precio,
            creditos
        )

        teclado = generar_teclado(
            token,
            licencias
        )

        try:

            if FILE_ID_CACHE:

                bot.send_photo(
                    message.chat.id,
                    FILE_ID_CACHE,
                    caption=texto,
                    reply_markup=teclado,
                    parse_mode="HTML"
                )

            elif os.path.exists(RUTA_IMAGEN):

                with open(RUTA_IMAGEN, "rb") as photo:

                    msg = bot.send_photo(
                        message.chat.id,
                        photo,
                        caption=texto,
                        reply_markup=teclado,
                        parse_mode="HTML"
                    )

                    FILE_ID_CACHE = msg.photo[-1].file_id

            else:

                msg = bot.send_photo(
                    message.chat.id,
                    URL_IMAGEN,
                    caption=texto,
                    reply_markup=teclado,
                    parse_mode="HTML"
                )

                FILE_ID_CACHE = msg.photo[-1].file_id

        except Exception as e:

            print(
                f"[ACTIVATE] Error enviando panel: {e}"
            )


    # =====================================================
    # BOTONES DE BANCOS Y YAPE
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("lic:yape:")
        or call.data.startswith("lic:bcp:")
        or call.data.startswith("lic:ibk:")
        or call.data.startswith("lic:bbva:")
    )
    def toggle_banco(call):

        partes = call.data.split(":")

        if len(partes) != 3:

            bot.answer_callback_query(
                call.id,
                "❌ Botón inválido."
            )

            return

        banco = partes[1]

        token = partes[2]

        sesion = SESIONES.get(token)

        if not sesion:

            bot.answer_callback_query(
                call.id,
                "⚠️ Esta operación expiró.",
                show_alert=True
            )

            return

        if call.from_user.id != sesion["telegram_id"]:

            bot.answer_callback_query(
                call.id,
                "❌ Este menú no te pertenece.",
                show_alert=True
            )

            return

        licencias = sesion["licencias"]

        if banco == "yape":
            licencias["yape"] = not licencias["yape"]

        elif banco == "bcp":
            licencias["bcp"] = not licencias["bcp"]

        elif banco == "ibk":
            licencias["ibk"] = not licencias["ibk"]

        elif banco == "bbva":
            licencias["bbva"] = not licencias["bbva"]

        precio = calcular_precio(
            sesion["original"],
            licencias
        )

        bot.answer_callback_query(call.id)

        try:

            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=generar_texto(
                    sesion["correo"],
                    licencias,
                    precio,
                    sesion["creditos"]
                ),
                reply_markup=generar_teclado(
                    token,
                    licencias
                ),
                parse_mode="HTML"
            )

        except Exception as e:

            print(
                f"[ACTIVATE] Error editando panel: {e}"
            )


    # =====================================================
    # CONFIRMAR
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("lic:confirmar:")
    )
    def confirmar(call):

        partes = call.data.split(":")

        if len(partes) != 3:

            bot.answer_callback_query(call.id)

            return

        token = partes[2]

        sesion = SESIONES.get(token)

        if not sesion:

            bot.answer_callback_query(
                call.id,
                "⚠️ Esta operación expiró.",
                show_alert=True
            )

            return

        if call.from_user.id != sesion["telegram_id"]:

            bot.answer_callback_query(
                call.id,
                "❌ Este menú no te pertenece.",
                show_alert=True
            )

            return

        telegram_id = sesion["telegram_id"]

        correo = sesion["correo"]

        original = sesion["original"]

        licencias = sesion["licencias"]

        precio = calcular_precio(
            original,
            licencias
        )

        if precio <= 0:

            bot.answer_callback_query(
                call.id,
                "⚠️ No hay licencias nuevas seleccionadas por activar.",
                show_alert=True
            )

            return

        resultado_creditos = consultar_creditos(telegram_id)

        if not resultado_creditos["ok"]:

            bot.answer_callback_query(
                call.id,
                "⚠️ No pude consultar tus créditos.",
                show_alert=True
            )

            return

        creditos = resultado_creditos["creditos"]

        if creditos < precio:

            faltan = precio - creditos

            bot.answer_callback_query(
                call.id,
                "❌ Créditos insuficientes.",
                show_alert=True
            )

            bot.send_message(
                call.message.chat.id,
                (
                    "❌ <b>CRÉDITOS INSUFICIENTES</b>\n\n"
                    f"💰 Tienes ➣ <b>{creditos} créditos</b>\n"
                    f"💳 Necesitas ➣ <b>{precio} créditos</b>\n"
                    f"📉 Te faltan ➣ <b>{faltan} créditos</b>\n\n"
                    "🛒 ¿Quieres comprar créditos?\n\n"
                    "Escribe:\n<code>/buy</code>"
                ),
                parse_mode="HTML"
            )

            return

        # =================================================
        # ACTIVAR EN API
        # =================================================

        try:

            payload = {
                "payment": True,
                "yape": licencias["yape"],
                "bcp": licencias["bcp"],
                "ibk": licencias["ibk"],
                "bbva": licencias["bbva"]
            }

            respuesta = http.post(
                API_ACTIVATE_USER,
                params={
                    "email": correo
                },
                json=payload,
                timeout=10
            )

            if respuesta.status_code == 404:

                bot.answer_callback_query(
                    call.id,
                    "❌ Usuario no encontrado.",
                    show_alert=True
                )

                return

            respuesta.raise_for_status()

        except requests.RequestException as e:

            print(
                f"[ACTIVATE] Error activate_user: {e}"
            )

            bot.answer_callback_query(
                call.id,
                "⚠️ Error activando la licencia.",
                show_alert=True
            )

            return

        # =================================================
        # DESCONTAR CRÉDITOS
        # =================================================

        descuento_ok = descontar_creditos(
            telegram_id,
            precio
        )

        if not descuento_ok:

            bot.answer_callback_query(
                call.id,
                "⚠️ Error descontando créditos.",
                show_alert=True
            )

            return

        consulta_actualizada = consultar_usuario_yape(correo)

        if consulta_actualizada["ok"]:

            nuevas_reales = obtener_licencias(
                consulta_actualizada["datos"]
            )

        else:

            nuevas_reales = licencias.copy()

        nuevos_creditos = creditos - precio

        try:

            teclado_salida = types.InlineKeyboardMarkup(row_width=2)
            teclado_salida.row(
                types.InlineKeyboardButton(
                    "⬅️ RETROCEDER",
                    callback_data=f"lic:volver:{token}"
                ),
                types.InlineKeyboardButton(
                    "❌ SALIR",
                    callback_data=f"lic:salir:{token}"
                )
            )

            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=generar_texto(
                    correo,
                    nuevas_reales,
                    0,
                    nuevos_creditos
                ),
                reply_markup=teclado_salida,
                parse_mode="HTML"
            )

        except Exception as e:

            print(
                f"[ACTIVATE] Error actualizando resultado: {e}"
            )

        bot.answer_callback_query(
            call.id,
            "✅ Activación completada.",
            show_alert=True
        )

        # La sesión se mantiene hasta pulsar RETROCEDER o SALIR.


    # =====================================================
    # VOLVER / SALIR
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("lic:volver:")
    )
    def volver_salir(call):

        partes = call.data.split(":")

        token = partes[2] if len(partes) == 3 else None

        bot.answer_callback_query(call.id)

        if token:
            SESIONES.pop(token, None)

        try:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )

        except Exception as e:
            print(
                f"[ACTIVATE] Error al volver/salir: {e}"
            )


    # =====================================================
    # SALIR
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("lic:salir:")
    )
    def salir(call):

        partes = call.data.split(":")
        token = partes[2] if len(partes) == 3 else None

        bot.answer_callback_query(call.id)

        if token:
            SESIONES.pop(token, None)

        try:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )

        except Exception as e:
            print(
                f"[ACTIVATE] Error al salir: {e}"
            )


    # =====================================================
    # CANCELAR
    # =====================================================

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("lic:cancelar:")
    )
    def cancelar(call):

        partes = call.data.split(":")

        token = partes[2] if len(partes) == 3 else None

        bot.answer_callback_query(call.id)

        if token:

            SESIONES.pop(token, None)

        try:

            bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )

        except Exception as e:

            print(
                f"[ACTIVATE] Error cancelando: {e}"
            )