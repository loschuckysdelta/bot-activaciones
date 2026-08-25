import io
import time
import base64
import requests
from datetime import datetime
from telebot import types

# ========================================================
# 1. ENDPOINTS DE LAS APIs
# ========================================================

URL_VOUCHERS = "https://chucky-vouchers.vercel.app/api"
URL_ACTIVACIONES = "https://activaciones.vercel.app/api"

X_TOKEN = "4d5a7b9c1e2f3a4b5c6d7e8f9a0b1c2d"

ADMIN_IDS = [8635600472]


# ========================================================
# 2. ALMACENAMIENTO EN MEMORIA
# ========================================================

GRUPOS_AUTORIZADOS = {}
COOLDOWN_ANTISPAM = {}
USOS_USUARIOS_DIARIOS = {}


# ========================================================
# 3. SERVICIOS
# ========================================================

NOMBRES_SERVICIOS = {
    "yape": "Yape",
    "plin": "Plin",
    "bim": "Bim",
    "sip": "Sip",
    "agora": "Agora",
    "lemon": "Lemon",
    "panda": "Panda",
    "prexpe": "Prexpe",
    "bcp": "BCP",
    "ibk": "Interbank",
    "bbva": "BBVA",
    "scotiabank": "Scotiabank",
    "ripley": "Ripley",
    "falabella": "Falabella",
    "caja": "Caja"
}


# ========================================================
# 4. CONSULTAR DÍAS DEL USUARIO
# ========================================================

def consultar_dias_api(user_id):
    """
    Consulta los días del usuario.

    days > 0:
        consultas ilimitadas

    days == 0:
        plan gratuito de 3 consultas por día
    """

    headers = {
        "X-TOKEN": X_TOKEN
    }

    url = f"{URL_ACTIVACIONES}/user?id={user_id}"

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:

            data = response.json()

            # Respuesta esperada:
            #
            # {
            #   "success": true,
            #   "user": {
            #       "telegramId": "...",
            #       "credits": 0,
            #       "days": 10
            #   }
            # }

            if data.get("success") is True and "user" in data:

                user = data["user"]

                dias_restantes = int(
                    user.get("days", 0) or 0
                )

                if dias_restantes > 0:
                    return True, dias_restantes

                return False, 0

        else:

            print(
                f"⚠️ Error consultando usuario: "
                f"{response.status_code} - {response.text}"
            )

    except Exception as e:

        print(
            f"Error consultando días API: {e}"
        )

    return False, 0


# ========================================================
# 5. EVALUAR PERMISO
# ========================================================

def evaluar_permiso(chat_id, user_id):

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    ahora = time.time()

    # ====================================================
    # A. SI EL COMANDO VIENE DE UN GRUPO
    # ====================================================

    if chat_id < 0:

        # -----------------------------------------------
        # Verificar grupo autorizado
        # -----------------------------------------------

        if chat_id not in GRUPOS_AUTORIZADOS:

            return False, (
                "❌ <b>Grupo no autorizado</b>\n\n"
                "Este grupo no está autorizado para usar el bot."
            )

        datos_grupo = GRUPOS_AUTORIZADOS[chat_id]

        # -----------------------------------------------
        # Reiniciar contador si cambió el día
        # -----------------------------------------------

        if datos_grupo["fecha"] != fecha_hoy:

            datos_grupo["fecha"] = fecha_hoy
            datos_grupo["usos_hoy"] = 0

        # -----------------------------------------------
        # AntiSpam personalizado
        # -----------------------------------------------

        anti_spam = datos_grupo.get(
            "anti_spam",
            5
        )

        ultimo_uso = COOLDOWN_ANTISPAM.get(
            chat_id,
            0
        )

        tiempo_transcurrido = ahora - ultimo_uso

        if tiempo_transcurrido < anti_spam:

            tiempo_espera = max(
                1,
                int(anti_spam - tiempo_transcurrido)
            )

            return False, (
                "⚠️ <b>AntiSpam Activado</b>\n\n"
                f"⏱ Espera <b>{tiempo_espera} segundos</b> "
                "antes de realizar otra consulta."
            )

        # -----------------------------------------------
        # Revisar límite diario
        # -----------------------------------------------

        if (
            datos_grupo["usos_hoy"]
            >= datos_grupo["limite_diario"]
        ):

            return False, (
                "⚠️ <b>Límite diario alcanzado</b>\n\n"
                f"📊 Este grupo ya utilizó sus "
                f"<b>{datos_grupo['limite_diario']} "
                "consultas</b> de hoy."
            )

        # -----------------------------------------------
        # Registrar consulta
        # -----------------------------------------------

        datos_grupo["usos_hoy"] += 1

        COOLDOWN_ANTISPAM[chat_id] = ahora

        restantes_grupo = (
            datos_grupo["limite_diario"]
            - datos_grupo["usos_hoy"]
        )

        return True, (
            "👥 <b>Grupo Autorizado</b>\n"
            f"📊 Consultas: "
            f"<b>{datos_grupo['usos_hoy']}/"
            f"{datos_grupo['limite_diario']}</b>\n"
            f"🔎 Restantes: <b>{restantes_grupo}</b>\n"
            f"⏱ AntiSpam: <b>{anti_spam}s</b>"
        )

    # ====================================================
    # B. CHAT PRIVADO - ANTISPAM DE 5 SEGUNDOS
    # ====================================================

    ultimo_uso = COOLDOWN_ANTISPAM.get(
        chat_id,
        0
    )

    tiempo_transcurrido = ahora - ultimo_uso

    if tiempo_transcurrido < 5:

        tiempo_espera = max(
            1,
            int(5 - tiempo_transcurrido)
        )

        return False, (
            "⚠️ <b>AntiSpam Activado:</b> "
            f"Espera {tiempo_espera}s antes "
            "de enviar otro comando."
        )

    # ====================================================
    # C. CONSULTAR DÍAS DEL USUARIO
    # ====================================================

    tiene_dias, cantidad_dias = consultar_dias_api(
        user_id
    )

    # ====================================================
    # D. TIENE DÍAS = CONSULTAS ILIMITADAS
    # ====================================================

    if tiene_dias:

        COOLDOWN_ANTISPAM[chat_id] = ahora

        return True, (
            "🌟 <b>Plan con días activo</b>\n"
            f"📅 Días restantes: <b>{cantidad_dias}</b>\n"
            "♾️ Consultas: <b>Ilimitadas</b>"
        )

    # ====================================================
    # E. NO TIENE DÍAS = PLAN GRATUITO
    # ====================================================

    registro = USOS_USUARIOS_DIARIOS.get(
        user_id,
        {
            "fecha": fecha_hoy,
            "usos": 0
        }
    )

    # -----------------------------------------------
    # Reiniciar las 3 consultas al cambiar de día
    # -----------------------------------------------

    if registro["fecha"] != fecha_hoy:

        registro = {
            "fecha": fecha_hoy,
            "usos": 0
        }

    # -----------------------------------------------
    # Ya gastó las 3 consultas
    # -----------------------------------------------

    if registro["usos"] >= 3:

        USOS_USUARIOS_DIARIOS[user_id] = registro

        return False, (
            "⚠️ <b>Plan Gratuito agotado</b>\n\n"
            "Ya utilizaste tus "
            "<b>3 consultas gratuitas de hoy.</b>\n\n"
            "📅 Vuelve mañana para obtener otras "
            "3 consultas o adquiere días para tener "
            "consultas ilimitadas."
        )

    # -----------------------------------------------
    # Consumir una consulta
    # -----------------------------------------------

    registro["usos"] += 1

    USOS_USUARIOS_DIARIOS[user_id] = registro

    COOLDOWN_ANTISPAM[chat_id] = ahora

    usos_restantes = 3 - registro["usos"]

    return True, (
        "🎁 <b>Plan Gratuito</b>\n"
        f"🔎 Consulta: <b>{registro['usos']}/3</b>\n"
        f"📊 Te quedan: "
        f"<b>{usos_restantes}</b> consultas hoy"
    )


# ========================================================
# 6. SOLICITAR VOUCHER A LA API
# ========================================================

def solicitar_voucher_api(endpoint, payload):

    url = f"{URL_VOUCHERS}{endpoint}"

    headers = {
        "X-TOKEN": X_TOKEN,
        "Content-Type": "application/json"
    }

    try:

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=20
        )

        if response.status_code == 200:

            data = response.json()

            if data.get("status") and "base64" in data:

                b64_string = data["base64"]

                if "," in b64_string:
                    b64_string = b64_string.split(",")[1]

                return (
                    base64.b64decode(b64_string),
                    None
                )

            return (
                None,
                "Respuesta inválida de la API de vouchers."
            )

        else:

            print(
                f"⚠️ Error {response.status_code} "
                f"en {endpoint}: {response.text}"
            )

            return (
                None,
                f"Error HTTP {response.status_code}: "
                f"{response.text}"
            )

    except Exception as e:

        return (
            None,
            f"Error de conexión: {str(e)}"
        )


# ========================================================
# 7. REGISTRAR BETA
# ========================================================

def registrar_beta(bot):

    # ====================================================
    # /addgrupo
    #
    # EJEMPLO:
    #
    # /addgrupo -1001234567890 10 6
    #
    # -1001234567890 = ID grupo
    # 10 = consultas diarias
    # 6 = segundos AntiSpam
    # ====================================================

    @bot.message_handler(commands=["addgrupo"])
    def agregar_grupo(message):

        if message.from_user.id not in ADMIN_IDS:
            return

        try:

            partes = message.text.split()

            if len(partes) != 4:
                raise ValueError("Formato incorrecto")

            group_id = int(partes[1])
            limite_diario = int(partes[2])
            anti_spam = int(partes[3])

            if group_id >= 0:
                bot.reply_to(
                    message,
                    "❌ El ID debe ser de un grupo.\n\n"
                    "Ejemplo:\n"
                    "<code>/addgrupo -1001234567890 10 6</code>",
                    parse_mode="HTML"
                )
                return

            if limite_diario <= 0:
                bot.reply_to(
                    message,
                    "❌ El límite diario debe ser mayor a 0.",
                    parse_mode="HTML"
                )
                return

            if anti_spam < 0:
                bot.reply_to(
                    message,
                    "❌ El AntiSpam no puede ser negativo.",
                    parse_mode="HTML"
                )
                return

            GRUPOS_AUTORIZADOS[group_id] = {
                "limite_diario": limite_diario,
                "anti_spam": anti_spam,
                "usos_hoy": 0,
                "fecha": datetime.now().strftime("%Y-%m-%d")
            }

            bot.reply_to(
                message,
                "✅ <b>Grupo Autorizado</b>\n\n"
                f"🆔 ID: <code>{group_id}</code>\n"
                f"📊 Límite diario: "
                f"<b>{limite_diario}</b> consultas\n"
                f"⏱ AntiSpam: "
                f"<b>{anti_spam} segundos</b>",
                parse_mode="HTML"
            )

        except Exception:

            bot.reply_to(
                message,
                "⚠️ <b>Formato incorrecto</b>\n\n"
                "<code>/addgrupo ID_GRUPO LIMITE ANTISPAM</code>\n\n"
                "✅ Ejemplo:\n"
                "<code>/addgrupo -1001234567890 10 6</code>\n\n"
                "📊 10 = consultas por día\n"
                "⏱ 6 = segundos entre consultas",
                parse_mode="HTML"
            )

    # ====================================================
    # /delgrupo
    # ====================================================

    @bot.message_handler(commands=["delgrupo"])
    def eliminar_grupo(message):

        if message.from_user.id not in ADMIN_IDS:
            return

        try:

            partes = message.text.split()

            group_id = int(partes[1])

            if group_id in GRUPOS_AUTORIZADOS:

                del GRUPOS_AUTORIZADOS[group_id]

                # Limpiar también el cooldown
                COOLDOWN_ANTISPAM.pop(
                    group_id,
                    None
                )

                bot.reply_to(
                    message,
                    f"🗑️ Grupo "
                    f"<code>{group_id}</code> "
                    "eliminado con éxito.",
                    parse_mode="HTML"
                )

            else:

                bot.reply_to(
                    message,
                    "⚠️ El grupo no está registrado.",
                    parse_mode="HTML"
                )

        except Exception:

            bot.reply_to(
                message,
                "⚠️ Formato:\n"
                "<code>/delgrupo [ID_GRUPO]</code>",
                parse_mode="HTML"
            )

    # ====================================================
    # COMANDOS DISPONIBLES
    # ====================================================

    TODOS_LOS_COMANDOS = list(
        NOMBRES_SERVICIOS.keys()
    )

    # ====================================================
    # GESTOR GENERAL DE VOUCHERS
    # ====================================================

    @bot.message_handler(
        commands=TODOS_LOS_COMANDOS
    )
    def gestor_vouchers_general(message):

        chat_id = message.chat.id
        user_id = message.from_user.id

        comando = (
            message.text
            .split()[0]
            .replace("/", "")
            .lower()
        )

        endpoint = f"/{comando}"

        nombre_servicio = NOMBRES_SERVICIOS.get(
            comando,
            comando.capitalize()
        )

        texto_completo = message.text.strip()

        partes_comando = texto_completo.split(
            maxsplit=1
        )

        # =================================================
        # FORMATO INCORRECTO
        # =================================================

        if len(partes_comando) == 1:

            mensaje_ayuda = (
                f"⚠️ <b>Formato incorrecto.</b>\n"
                f"Uso: "
                f"<code>/{comando} "
                "monto|titular|3 dígitos|mensaje|destino"
                "</code>\n\n"

                "✅ <b>Ejemplo de uso:</b>\n"

                f"<code>/{comando} 150|Pedro Castillo\n"
                f"/{comando} 150|Pedro Castillo|999\n"
                f"/{comando} 150|Pedro Castillo|999|"
                "Pago realizado\n"
                f"/{comando} 150|Pedro Castillo|999|"
                "Pago realizado|Plin</code>"
            )

            bot.reply_to(
                message,
                mensaje_ayuda,
                parse_mode="HTML"
            )

            return

        # =================================================
        # EVALUAR PERMISO
        # =================================================

        permitido, info_plan = evaluar_permiso(
            chat_id,
            user_id
        )

        if not permitido:

            bot.reply_to(
                message,
                info_plan,
                parse_mode="HTML"
            )

            return

        # =================================================
        # LEER PARÁMETROS
        # =================================================

        args_raw = partes_comando[1]

        parametros = [
            arg.strip()
            for arg in args_raw.split("|")
        ]

        monto = (
            parametros[0]
            if len(parametros) > 0
            else "0"
        )

        titular = (
            parametros[1]
            if len(parametros) > 1
            else ""
        )

        payload_voucher = {
            "id": str(user_id),
            "monto": monto,
            "nombre": titular
        }

        if (
            len(parametros) > 2
            and parametros[2]
        ):
            payload_voucher["digitos"] = parametros[2]

        if (
            len(parametros) > 3
            and parametros[3]
        ):
            payload_voucher["mensaje"] = parametros[3]

        if (
            len(parametros) > 4
            and parametros[4]
        ):
            payload_voucher["destino"] = parametros[4]

        # =================================================
        # MENSAJE GENERANDO
        # =================================================

        msg_espera = bot.reply_to(
            message,
            f"⏳ <i>Generando comprobante de "
            f"<b>{nombre_servicio}</b>...</i>",
            parse_mode="HTML"
        )

        # =================================================
        # SOLICITAR VOUCHER
        # =================================================

        img_bytes, error = solicitar_voucher_api(
            endpoint,
            payload_voucher
        )

        # =================================================
        # BORRAR MENSAJE DE ESPERA
        # =================================================

        try:

            bot.delete_message(
                chat_id,
                msg_espera.message_id
            )

        except Exception:
            pass

        # =================================================
        # VOUCHER GENERADO
        # =================================================

        if img_bytes:

            photo_file = io.BytesIO(
                img_bytes
            )

            photo_file.name = (
                "Screenshot_250826.png"
            )

            caption_respuesta = (
                f"✅ <b>Voucher "
                f"{nombre_servicio} generado</b>\n\n"

                f"💰 <b>Monto:</b> S/ {monto}\n"

                f"👤 <b>Titular:</b> "
                f"{titular}\n\n"

                "👤 <b>Estado del usuario:</b>\n"
                f"{info_plan}"
            )

            bot.send_document(
                chat_id,
                document=photo_file,
                caption=caption_respuesta,
                reply_to_message_id=message.message_id,
                parse_mode="HTML"
            )

        # =================================================
        # ERROR
        # =================================================

        else:

            bot.reply_to(
                message,
                f"❌ <b>Error:</b> {error}",
                parse_mode="HTML"
            )