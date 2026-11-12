import base64
import io
import json
import os
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from telebot import types

# ========================================================
# 1. CONFIGURACIÓN DE API Y TOKENS
# ========================================================

URL_VOUCHERS = "https://chucky-vouchers.vercel.app/api"
URL_ACTIVACIONES = "https://activaciones.vercel.app/api"
X_TOKEN = "4d5a7b9c1e2f3a4b5c6d7e8f9a0b1c2d"

ADMIN_IDS = [8635600472]
LINK_ADMIN = "https://t.me/tuchuckynet_x"
LINK_DESCARGA = "https://ypfkplus.com/"
URL_IMAGEN_PROMO = "https://i.postimg.cc/4d7GwtKG/image.png"

# ========================================================
# 2. ARCHIVOS Y CACHÉ
# ========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_GRUPOS = os.path.join(BASE_DIR, "grupos_autorizados.json")
ARCHIVO_USOS_DIARIOS = os.path.join(BASE_DIR, "usos_diarios.json")

BLOQUEO_USOS = threading.RLock()
COOLDOWN_GRUPOS = {}
COOLDOWN_PRIVADO = {}
USOS_USUARIOS_DIARIOS = {}
RESET_DB_CONFIRMACIONES = {}
EJEMPLOS_CACHE = {}

# ========================================================
# 3. SERVICIOS Y CLASIFICACIÓN
# ========================================================

SERVICIOS_CON_GRATIS = ["yape"]
SERVICIOS_SOLO_CON_DIAS = [
    "plin", "bim", "sip", "agora", "lemon", "panda",
    "prexpe", "bcp", "ibk", "bbva", "scotiabank",
    "ripley", "falabella", "caja"
]

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
# FUNCIONES AUXILIARES DE PERSISTENCIA Y FORMATO
# ========================================================

def cargar_grupos():
    if not os.path.isfile(ARCHIVO_GRUPOS):
        return {}
    try:
        with open(ARCHIVO_GRUPOS, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        resultado = {}
        if not isinstance(datos, dict):
            return {}
        for grupo, info in datos.items():
            if not isinstance(info, dict):
                continue
            try:
                resultado[int(grupo)] = info
            except (TypeError, ValueError):
                continue
        return resultado
    except (OSError, ValueError, TypeError) as exc:
        print(f"Error leyendo grupos: {exc}")
        return {}


GRUPOS_AUTORIZADOS = cargar_grupos()


def guardar_grupos():
    try:
        temporal = ARCHIVO_GRUPOS + ".tmp"
        with open(temporal, "w", encoding="utf-8") as archivo:
            json.dump(GRUPOS_AUTORIZADOS, archivo, indent=2, ensure_ascii=False)
        os.replace(temporal, ARCHIVO_GRUPOS)
    except OSError as exc:
        print(f"Error guardando grupos: {exc}")


def convertir_antispam(valor):
    valor = str(valor).strip().lower()
    multiplicador = 60 if valor.endswith("m") else 1
    if valor.endswith(("m", "s")):
        valor = valor[:-1]
    segundos = int(valor) * multiplicador
    if segundos < 0:
        raise ValueError("El AntiSpam no puede ser negativo")
    return segundos


def texto_antispam(segundos):
    if segundos >= 60:
        mins = segundos // 60
        secs = segundos % 60
        return f"{mins}m {secs}s" if secs else f"{mins}m"
    return f"{segundos}s"


def _fecha_peru():
    try:
        return datetime.now(ZoneInfo("America/Lima")).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def _leer_usos():
    try:
        with open(ARCHIVO_USOS_DIARIOS, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return datos if isinstance(datos, dict) else {}
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        print(f"⚠️ No se pudieron leer los usos diarios: {error}")
        return {}


def _guardar_usos(datos):
    temporal = ARCHIVO_USOS_DIARIOS + ".tmp"
    with open(temporal, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    os.replace(temporal, ARCHIVO_USOS_DIARIOS)


# ========================================================
# 4. CONSULTAR DÍAS DEL USUARIO
# ========================================================

def consultar_dias_api(user_id):
    headers = {"X-TOKEN": X_TOKEN} if X_TOKEN else {}
    url = f"{URL_ACTIVACIONES}/user?id={user_id}"

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") is True and "user" in data:
                user = data["user"]
                dias_restantes = int(user.get("days", 0) or 0)
                if dias_restantes > 0:
                    return True, dias_restantes
                return False, 0
        else:
            print(f"⚠️ Error consultando usuario: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error consultando días API: {e}")

    return False, 0


# ========================================================
# 5. EVALUAR PERMISO (GRUPOS PUENTE Y PRIVADO)
# ========================================================

def evaluar_permiso(chat_id, user_id, comando):
    ahora = time.time()
    try:
        hoy_dt = datetime.now(ZoneInfo("America/Lima"))
    except Exception:
        hoy_dt = datetime.now()

    # --- Validación si es un Grupo Puente ---
    if chat_id < 0:
        if chat_id not in GRUPOS_AUTORIZADOS:
            return False, None, "grupo_no_autorizado"

        grupo_info = GRUPOS_AUTORIZADOS[chat_id]
        
        # Verificar si la licencia del grupo puente ha expirado
        fecha_exp_str = grupo_info.get("fecha_expiracion")
        if fecha_exp_str:
            try:
                fecha_exp = datetime.strptime(fecha_exp_str, "%Y-%m-%d").replace(tzinfo=ZoneInfo("America/Lima"))
            except Exception:
                fecha_exp = datetime.strptime(fecha_exp_str, "%Y-%m-%d")
                
            if hoy_dt > fecha_exp:
                return False, (
                    "⚠️ <b>¡La licencia de este Grupo Puente ha expirado!</b>\n\n"
                    "❌ El tiempo de alquiler o activación del grupo ha concluido y el bot ha suspendido el servicio.\n\n"
                    "📱 <b>¿Deseas renovar el Grupo Puente?</b>\n"
                    "✅ Contacta inmediatamente con el administrador para adquirir una nueva licencia."
                ), "grupo_expirado"

        anti_spam = int(grupo_info.get("anti_spam", 5))
        cooldown = COOLDOWN_GRUPOS.setdefault(chat_id, {})

        # Anti-spam personal dentro del grupo
        transcurrido = ahora - cooldown.get(user_id, 0)
        if transcurrido < anti_spam:
            espera = max(1, int(anti_spam - transcurrido + 0.999))
            return False, f"⏳ Espera <b>{texto_antispam(espera)}</b> antes de volver a usar un comando.", "antispam"

        cooldown[user_id] = ahora
        # Todos los comandos desbloqueados dentro del grupo puente
        return True, "👥 <b>Grupo Puente Autorizado</b>\n♾️ Todos los comandos desbloqueados", "ok"

    # --- Validación si es Chat Privado ---
    anti_spam = 5
    transcurrido = ahora - COOLDOWN_PRIVADO.get(user_id, 0)
    if transcurrido < anti_spam:
        espera = max(1, int(anti_spam - transcurrido + 0.999))
        return False, f"⏳ Espera <b>{texto_antispam(espera)}</b> antes de usar otro comando.", "antispam"

    tiene_dias, cantidad_dias = consultar_dias_api(user_id)

    # 1. Servicios exclusivos para usuarios con días en privado
    if comando in SERVICIOS_SOLO_CON_DIAS:
        if not tiene_dias:
            return False, (
                "⚠️ <b>¡Acceso restringido!</b>\n\n"
                f"El servicio <b>/{comando}</b> requiere que tengas <b>días activos</b> en tu perfil.\n\n"
                "📱 <b>¿Deseas adquirir días o la APP completa?</b>\n"
                "✅ Contacta al administrador."
            ), "requiere_dias"

        COOLDOWN_PRIVADO[user_id] = ahora
        return True, (
            "🌟 <b>Plan activo</b>\n"
            f"📅 Días restantes: <b>{cantidad_dias}</b>\n"
            f"♾️ Acceso concedido a /{comando}"
        ), "ok"

    # 2. Servicio /yape en privado
    if comando in SERVICIOS_CON_GRATIS:
        if tiene_dias:
            COOLDOWN_PRIVADO[user_id] = ahora
            return True, (
                "🌟 <b>Plan activo</b>\n"
                f"📅 Días restantes: <b>{cantidad_dias}</b>\n"
                "♾️ Consultas ilimitadas"
            ), "ok"

        with BLOQUEO_USOS:
            hoy_str = hoy_dt.strftime("%Y-%m-%d")
            datos = _leer_usos()
            datos = {k: v for k, v in datos.items() if isinstance(v, dict) and v.get("fecha") == hoy_str}
            clave = str(user_id)
            usados = int(datos.get(clave, {}).get("usos", 0))

            if usados >= 1:
                return False, (
                    "⚠️ <b>¡Tu consulta gratis diaria de Yape se agotó!</b>\n\n"
                    f"👤 Tu ID: <code>{user_id}</code>\n"
                    "📊 Usaste <b>1/1</b> consulta gratuita de Yape hoy.\n\n"
                    "📸 Consulta la oferta especial a continuación para obtener consultas ilimitadas.\n\n"
                    "📱 <b>¿Deseas comprar la APP o adquirir días?</b>\n"
                    "✅ Contacta al administrador o vuelve mañana."
                ), "limite_agotado"

            datos[clave] = {"fecha": hoy_str, "usos": usados + 1}
            try:
                _guardar_usos(datos)
            except OSError as error:
                print(f"❌ No se pudo guardar el contador diario: {error}")
                return False, "⚠️ No se pudo registrar tu consulta. Intenta nuevamente.", "error"

        COOLDOWN_PRIVADO[user_id] = ahora
        return True, (
            "🎁 <b>Plan gratuito</b>\n"
            f"📊 Consulta Yape diaria: <b>{usados + 1}/1</b>\n"
            "🔎 Restantes hoy: <b>0</b>"
        ), "ok"

    return False, "❌ Comando no reconocido.", "error"


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
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") and "base64" in data:
                b64_string = data["base64"]
                if "," in b64_string:
                    b64_string = b64_string.split(",")[1]
                return base64.b64decode(b64_string), None
            return None, "Respuesta inválida de la API de vouchers."
        else:
            print(f"⚠️ Error {response.status_code} en {endpoint}: {response.text}")
            return None, f"Error HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Error de conexión: {str(e)}"


def enviar_limite_alcanzado(bot, message, texto):
    botones = types.InlineKeyboardMarkup()
    botones.add(types.InlineKeyboardButton("📲 CONTACTAR AL ADMINISTRADOR", url=LINK_ADMIN))
    if LINK_DESCARGA:
        botones.add(types.InlineKeyboardButton("⬇️ DESCARGAR GRATIS", url=LINK_DESCARGA))

    promocion = (
        "🇵🇪 <b>¡OFERTA ESPECIAL!</b> 🇵🇪\n\n"
        "🔥 Solo por <b>S/ xxx</b>\n\n"
        "<b>¿Qué incluye?</b>\n\n"
        "✅ Saldo ilimitado\n"
        "✅ Notificaciones en tiempo real\n"
        "✅ Constancias por Gmail\n"
        "✅ Autocompletado OSIPTEL\n"
        "✅ Escáner QR con Inteligencia Artificial\n"
        "✅ Actualizaciones automáticas\n"
        "✅ Licencia permanente\n\n"
        "⬇️ <b>DESCARGAR GRATIS</b>\n"
        "https://ypfkplus.com/"
    )
    mensaje = texto + "\n\n" + promocion
    kwargs = {
        "parse_mode": "HTML",
        "reply_markup": botones,
        "reply_to_message_id": message.message_id,
    }
    try:
        bot.send_photo(message.chat.id, photo=URL_IMAGEN_PROMO, caption=mensaje, **kwargs)
    except Exception as exc:
        print(f"No se pudo enviar la imagen promocional: {exc}")
        bot.send_message(message.chat.id, mensaje, **kwargs)


# ========================================================
# 7. REGISTRAR BETA (Nombre requerido por main.py)
# ========================================================

def registrar_beta(bot):

    def _lista_ejemplos():
        return list(NOMBRES_SERVICIOS.items())

    def _texto_ejemplo(indice):
        servicios = _lista_ejemplos()
        comando, nombre = servicios[indice]
        total = len(servicios)

        return (
            f"🚀 <b>Voucher {nombre} ({indice + 1}/{total})</b>\n\n"
            f"🕹️ <b>Comando:</b>\n"
            f"<code>/{comando} monto|titular|3 dígitos o 9 dígitos|mensaje|destino</code>\n\n"
            f"✅ <b>Ejemplo de uso:</b>\n\n"
            f"<pre>"
            f"/{comando} 150|Pedro Castillo\n"
            f"/{comando} 150|Pedro Castillo|999\n"
            f"/{comando} 150|Pedro Castillo|999999999\n"
            f"/{comando} 150|Pedro Castillo|999|Pago realizado\n"
            f"/{comando} 150|Pedro Castillo|999|Pago realizado|Plin"
            f"</pre>"
        )

    def _botones_ejemplo(indice):
        servicios = _lista_ejemplos()
        total = len(servicios)
        anterior = (indice - 1) % total
        siguiente = (indice + 1) % total

        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.row(
            types.InlineKeyboardButton("⬅️", callback_data=f"ejemplo_{anterior}"),
            types.InlineKeyboardButton(f"{indice + 1}/{total}", callback_data="ejemplo_nada"),
            types.InlineKeyboardButton("➡️", callback_data=f"ejemplo_{siguiente}")
        )
        markup.row(types.InlineKeyboardButton("❌ Cerrar", callback_data="ejemplo_cerrar"))
        return markup

    def _generar_imagen_ejemplo(comando, user_id):
        if comando in EJEMPLOS_CACHE:
            return EJEMPLOS_CACHE[comando], None

        payload = {
            "id": str(user_id),
            "monto": "150",
            "nombre": "Pedro Castillo",
            "digitos": "999",
            "mensaje": "Pago realizado",
            "destino": "Plin"
        }

        imagen, error = solicitar_voucher_api(f"/{comando}", payload)
        if imagen:
            EJEMPLOS_CACHE[comando] = imagen
        return imagen, error

    def _archivo_imagen_ejemplo(imagen_bytes, comando):
        archivo = io.BytesIO(imagen_bytes)
        archivo.name = f"{comando}_ejemplo.png"
        archivo.seek(0)
        return archivo

    @bot.message_handler(commands=["ejemplos"])
    def mostrar_ejemplos(message):
        servicios = _lista_ejemplos()
        if not servicios:
            bot.reply_to(message, "⚠️ No hay servicios configurados.", parse_mode="HTML")
            return

        indice = 0
        comando, nombre = servicios[indice]
        msg_espera = bot.reply_to(message, f"⏳ <i>Generando ejemplo de <b>{nombre}</b>...</i>", parse_mode="HTML")

        imagen, error = _generar_imagen_ejemplo(comando, message.from_user.id)
        try:
            bot.delete_message(message.chat.id, msg_espera.message_id)
        except Exception:
            pass

        if not imagen:
            bot.reply_to(message, f"❌ <b>No se pudo generar el ejemplo de {nombre}.</b>\n\n<code>{error}</code>", parse_mode="HTML")
            return

        foto = _archivo_imagen_ejemplo(imagen, comando)
        bot.send_photo(
            chat_id=message.chat.id,
            photo=foto,
            caption=_texto_ejemplo(indice),
            reply_markup=_botones_ejemplo(indice),
            parse_mode="HTML",
            reply_to_message_id=message.message_id
        )

    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("ejemplo_"))
    def navegar_ejemplos(call):
        if call.data == "ejemplo_nada":
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
            return

        if call.data == "ejemplo_cerrar":
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            return

        try:
            indice = int(call.data.split("_", 1)[1])
        except Exception:
            return

        servicios = _lista_ejemplos()
        if indice < 0 or indice >= len(servicios):
            return

        comando, nombre = servicios[indice]
        try:
            bot.answer_callback_query(call.id, f"Generando {nombre}...")
        except Exception:
            pass

        imagen, error = _generar_imagen_ejemplo(comando, call.from_user.id)
        if not imagen:
            bot.send_message(call.message.chat.id, f"❌ <b>No se pudo generar el ejemplo de {nombre}.</b>\n\n<code>{error}</code>", parse_mode="HTML")
            return

        foto = _archivo_imagen_ejemplo(imagen, comando)
        media = types.InputMediaPhoto(media=foto, caption=_texto_ejemplo(indice), parse_mode="HTML")

        try:
            bot.edit_message_media(
                media=media,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=_botones_ejemplo(indice)
            )
        except Exception as e:
            print(f"⚠️ No se pudo editar el ejemplo: {e}")
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
            except Exception:
                pass
            foto.seek(0)
            bot.send_photo(
                chat_id=call.message.chat.id,
                photo=foto,
                caption=_texto_ejemplo(indice),
                reply_markup=_botones_ejemplo(indice),
                parse_mode="HTML"
            )

    @bot.message_handler(commands=["resetdb"])
    def resetear_base_datos(message):
        admin_id = message.from_user.id
        if admin_id not in ADMIN_IDS:
            bot.reply_to(message, "❌ <b>No tienes permiso para usar este comando.</b>", parse_mode="HTML")
            return

        partes = message.text.strip().split(maxsplit=1)
        if len(partes) == 1:
            RESET_DB_CONFIRMACIONES[admin_id] = time.time()
            bot.reply_to(
                message,
                "⚠️ <b>CONFIRMAR BORRADO TOTAL</b>\n\n"
                "Para confirmar escribe dentro de 60 segundos:\n\n"
                "<code>/resetdb confirmar</code>",
                parse_mode="HTML"
            )
            return

        if partes[1].strip().lower() != "confirmar":
            bot.reply_to(message, "⚠️ Confirmación inválida. Usa: <code>/resetdb confirmar</code>", parse_mode="HTML")
            return

        tiempo = RESET_DB_CONFIRMACIONES.get(admin_id, 0)
        if not tiempo or (time.time() - tiempo > 60):
            RESET_DB_CONFIRMACIONES.pop(admin_id, None)
            bot.reply_to(message, "⌛ La confirmación expiró. Usa <code>/resetdb</code>.", parse_mode="HTML")
            return

        try:
            GRUPOS_AUTORIZADOS.clear()
            COOLDOWN_GRUPOS.clear()
            COOLDOWN_PRIVADO.clear()
            USOS_USUARIOS_DIARIOS.clear()
            with open(ARCHIVO_GRUPOS, "w", encoding="utf-8") as archivo:
                json.dump({}, archivo, indent=4, ensure_ascii=False)
            _guardar_usos({})
            RESET_DB_CONFIRMACIONES.pop(admin_id, None)
            bot.reply_to(message, "✅ <b>Base de datos reiniciada completamente.</b>", parse_mode="HTML")
        except Exception as e:
            bot.reply_to(message, f"❌ <b>Error al reiniciar:</b> <code>{str(e)}</code>", parse_mode="HTML")

    @bot.message_handler(commands=["miid"])
    def ver_mi_id(message):
        if getattr(message, "sender_chat", None) is not None:
            bot.reply_to(message, "⚠️ <b>Estás enviando como anónimo o como el grupo.</b>", parse_mode="HTML")
            return
        bot.reply_to(
            message,
            f"👤 Telegram ID: <code>{message.from_user.id}</code>\n"
            f"👥 Chat ID: <code>{message.chat.id}</code>",
            parse_mode="HTML"
        )

    @bot.message_handler(commands=["addgrupo", "grupo", "chat"])
    def agregar_grupo(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        try:
            partes = message.text.strip().split(maxsplit=1)
            if len(partes) < 2:
                raise ValueError("Faltan parámetros")

            # Separar por pipe | -> ID_GRUPO | ANTISPAM | DIAS
            args = [arg.strip() for arg in partes[1].split("|")]
            if len(args) != 3:
                raise ValueError("Formato incorrecto")

            group_id = int(args[0])
            anti_spam = convertir_antispam(args[1])
            dias_vigencia = int(args[2])

            if group_id >= 0 or anti_spam < 0 or dias_vigencia <= 0:
                raise ValueError("Valores inválidos")

            # Calcular la fecha de expiración sumando los días a la fecha de Perú
            try:
                fecha_expiracion = (datetime.now(ZoneInfo("America/Lima")) + timedelta(days=dias_vigencia)).strftime("%Y-%m-%d")
            except Exception:
                fecha_expiracion = (datetime.now() + timedelta(days=dias_vigencia)).strftime("%Y-%m-%d")

            GRUPOS_AUTORIZADOS[group_id] = {
                "anti_spam": anti_spam,
                "dias_vigencia": dias_vigencia,
                "fecha_expiracion": fecha_expiracion
            }
            guardar_grupos()
            bot.reply_to(
                message,
                f"✅ <b>Grupo Puente Autorizado con Éxito</b>\n\n"
                f"🆔 ID del Chat: <code>{group_id}</code>\n"
                f"⏱ AntiSpam: <b>{texto_antispam(anti_spam)}</b>\n"
                f"📅 Duración: <b>{dias_vigencia} días</b>\n"
                f"⏳ Expira el: <b>{fecha_expiracion}</b>\n"
                f"🔓 <b>Estado:</b> Todos los comandos están desbloqueados en este grupo.",
                parse_mode="HTML"
            )
        except Exception:
            bot.reply_to(
                message,
                "⚠️ <b>Formato incorrecto para agregar grupo puente.</b>\n\n"
                "Uso:\n"
                "<code>/addgrupo ID_GRUPO | ANTISPAM | DÍAS</code>\n"
                "<i>(También puedes usar /grupo o /chat)</i>\n\n"
                "✅ Ejemplo:\n"
                "<code>/addgrupo -1001234567890 | 3s | 15</code>",
                parse_mode="HTML"
            )

    @bot.message_handler(commands=["delgrupo"])
    def eliminar_grupo(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        try:
            group_id = int(message.text.split()[1])
            if group_id in GRUPOS_AUTORIZADOS:
                del GRUPOS_AUTORIZADOS[group_id]
                guardar_grupos()
                COOLDOWN_GRUPOS.pop(group_id, None)
                bot.reply_to(message, f"🗑️ Grupo <code>{group_id}</code> eliminado.", parse_mode="HTML")
            else:
                bot.reply_to(message, "⚠️ El grupo no está registrado.", parse_mode="HTML")
        except Exception:
            bot.reply_to(message, "Uso: <code>/delgrupo [ID_GRUPO]</code>", parse_mode="HTML")

    TODOS_LOS_COMANDOS = list(NOMBRES_SERVICIOS.keys())

    @bot.message_handler(commands=TODOS_LOS_COMANDOS)
    def gestor_vouchers_general(message):
        chat_id = message.chat.id
        if chat_id < 0 and getattr(message, "sender_chat", None) is not None:
            bot.reply_to(message, "⚠️ <b>No puedo identificarte individualmente.</b> Desactiva <b>Ser anónimo</b>.", parse_mode="HTML")
            return

        user_id = message.from_user.id
        comando = message.text.split()[0].replace("/", "").lower()
        if "@" in comando:
            comando = comando.split("@")[0]

        endpoint = f"/{comando}"
        nombre_servicio = NOMBRES_SERVICIOS.get(comando, comando.capitalize())
        texto_completo = message.text.strip()
        partes_comando = texto_completo.split(maxsplit=1)

        if len(partes_comando) == 1:
            mensaje_ayuda = (
                f"⚠️ <b>Formato incorrecto.</b>\n\n"
                f"Uso:\n<code>/{comando} monto|titular|3 dígitos|mensaje|destino</code>\n\n"
                "✅ <b>Ejemplo de uso:</b>\n\n"
                f"<pre>"
                f"/{comando} 150|Pedro Castillo\n"
                f"/{comando} 150|Pedro Castillo|999\n"
                f"/{comando} 150|Pedro Castillo|999999999\n"
                f"/{comando} 150|Pedro Castillo|999|Pago realizado\n"
                f"/{comando} 150|Pedro Castillo|999|Pago realizado|Plin"
                f"</pre>"
            )
            bot.reply_to(message, mensaje_ayuda, parse_mode="HTML")
            return

        permitido, info_plan, motivo = evaluar_permiso(chat_id, user_id, comando)
        if not permitido:
            if motivo in ["limite_agotado", "grupo_expirado"]:
                enviar_limite_alcanzado(bot, message, info_plan)
            elif info_plan:
                bot.reply_to(message, info_plan, parse_mode="HTML")
            return

        args_raw = partes_comando[1]
        parametros = [arg.strip() for arg in args_raw.split("|")]
        monto = parametros[0] if len(parametros) > 0 else "0"
        titular = parametros[1] if len(parametros) > 1 else ""

        payload_voucher = {
            "id": str(user_id),
            "monto": monto,
            "nombre": titular
        }
        if len(parametros) > 2 and parametros[2]:
            payload_voucher["digitos"] = parametros[2]
        if len(parametros) > 3 and parametros[3]:
            payload_voucher["mensaje"] = parametros[3]
        if len(parametros) > 4 and parametros[4]:
            payload_voucher["destino"] = parametros[4]

        msg_espera = bot.reply_to(message, f"⏳ <i>Generando comprobante de <b>{nombre_servicio}</b>...</i>", parse_mode="HTML")

        img_bytes, error = solicitar_voucher_api(endpoint, payload_voucher)

        try:
            bot.delete_message(chat_id, msg_espera.message_id)
        except Exception:
            pass

        if img_bytes:
            photo_file = io.BytesIO(img_bytes)
            photo_file.name = "Screenshot_250826.png"
            caption_respuesta = (
                f"✅ <b>Voucher {nombre_servicio} generado</b>\n\n"
                f"💰 <b>Monto:</b> S/ {monto}\n"
                f"👤 <b>Titular:</b> {titular}\n\n"
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
        else:
            bot.reply_to(message, f"❌ <b>Error:</b> {error}", parse_mode="HTML")