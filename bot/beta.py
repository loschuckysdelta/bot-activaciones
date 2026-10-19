import json
import os
import time
from datetime import datetime

import requests
from telebot import types

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_GRUPOS = os.path.join(BASE_DIR, "grupos_autorizados.json")
URL_IMAGEN_PROMO = "https://i.postimg.cc/4d7GwtKG/image.png"
LINK_DESCARGA = "https://ypfkplus.com/"  # Destino del botón DESCARGAR GRATIS
ADMIN_IDS = [8635600472]  # Reemplaza o amplía con los ID de administradores.
LINK_ADMIN = "https://t.me/tuchuckynet_x"
URL_ACTIVACIONES = "https://activaciones.vercel.app/api"
X_TOKEN = os.environ.get("ACTIVACIONES_X_TOKEN", "")

SERVICIOS = {
    "yape": "Yape", "plin": "Plin", "bim": "Bim", "sip": "Sip",
    "agora": "Agora", "lemon": "Lemon", "panda": "Panda",
    "prexpe": "Prexpe", "bcp": "BCP", "ibk": "Interbank",
    "bbva": "BBVA", "scotiabank": "Scotiabank",
    "ripley": "Ripley", "falabella": "Falabella", "caja": "Caja",
}

COOLDOWN_GRUPOS = {}
COOLDOWN_PRIVADO = {}
USOS_PRIVADOS = {}
RESET_CONFIRMACIONES = {}


def cargar_grupos():
    if not os.path.isfile(ARCHIVO_GRUPOS):
        return {}
    try:
        with open(ARCHIVO_GRUPOS, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        resultado = {}
        for grupo, info in datos.items():
            info["usuarios"] = info.get("usuarios", {}) if isinstance(info.get("usuarios"), dict) else {}
            resultado[int(grupo)] = info
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


def consultar_dias_api(user_id):
    """Devuelve (activo, días). Sin token o ante error usa plan gratuito."""
    if not X_TOKEN:
        return False, 0
    try:
        respuesta = requests.get(
            f"{URL_ACTIVACIONES}/user",
            params={"id": user_id},
            headers={"X-TOKEN": X_TOKEN},
            timeout=5,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
        dias = int(datos.get("user", {}).get("days", 0) or 0)
        return bool(datos.get("success") and dias > 0), max(0, dias)
    except (requests.RequestException, ValueError, TypeError) as exc:
        print(f"No se pudieron consultar los días: {exc}")
        return False, 0


def evaluar_permiso(chat_id, user_id):
    hoy = datetime.now().strftime("%Y-%m-%d")
    ahora = time.time()

    if chat_id < 0:
        grupo = GRUPOS_AUTORIZADOS.get(chat_id)
        if not grupo:
            return False, "❌ <b>Grupo no autorizado.</b>", "grupo_no_autorizado"

        limite = int(grupo.get("limite_diario", 3))
        antispam = int(grupo.get("anti_spam", 5))
        usuarios = grupo.setdefault("usuarios", {})
        clave = str(user_id)
        registro = usuarios.get(clave, {"fecha": hoy, "usos": 0})
        if registro.get("fecha") != hoy:
            registro = {"fecha": hoy, "usos": 0}

        # Primero se verifica el límite, para que el usuario vea el video
        # aunque haya enviado el comando antes de terminar el AntiSpam.
        if registro["usos"] >= limite:
            return False, (
                "⚠️ <b>¡Tus consultas se agotaron!</b>\n\n"
                f"👤 Tu ID: <code>{user_id}</code>\n"
                f"📊 Usaste <b>{registro['usos']}/{limite}</b> consultas.\n\n"
                "📸 Consulta la oferta especial a continuación.\n\n"
                "📱 <b>¿Deseas comprar la APP?</b>\n"
                "✅ Contacta al administrador.\n\n"
                "👥 Las demás personas del grupo conservan sus consultas."
            ), "limite_agotado"

        cooldown = COOLDOWN_GRUPOS.setdefault(chat_id, {})
        restante = antispam - (ahora - cooldown.get(user_id, 0))
        if restante > 0:
            return False, f"⏱ AntiSpam personal: espera <b>{int(restante) + 1}s</b>.", "antispam"

        registro["usos"] += 1
        usuarios[clave] = registro
        guardar_grupos()
        cooldown[user_id] = ahora
        return True, (
            f"👥 Grupo autorizado\n📊 Consultas: "
            f"<b>{registro['usos']}/{limite}</b>"
        ), "ok"

    activo, dias = consultar_dias_api(user_id)
    if activo:
        restante = 5 - (ahora - COOLDOWN_PRIVADO.get(user_id, 0))
        if restante > 0:
            return False, f"⏱ Espera <b>{int(restante) + 1}s</b>.", "antispam"
        COOLDOWN_PRIVADO[user_id] = ahora
        return True, f"🌟 Plan activo: {dias} días. Consultas ilimitadas.", "ok"

    registro = USOS_PRIVADOS.get(user_id, {"fecha": hoy, "usos": 0})
    if registro["fecha"] != hoy:
        registro = {"fecha": hoy, "usos": 0}
    if registro["usos"] >= 3:
        return False, (
            "⚠️ <b>¡Tus consultas se agotaron!</b>\n\n"
            f"👤 Tu ID: <code>{user_id}</code>\n"
            "📊 Usaste <b>3/3</b> consultas gratuitas.\n\n"
            "📸 Consulta la oferta especial a continuación.\n\n"
            "📱 <b>¿Deseas comprar la APP?</b>\n"
            "✅ Contacta al administrador o vuelve mañana."
        ), "limite_agotado"

    restante = 5 - (ahora - COOLDOWN_PRIVADO.get(user_id, 0))
    if restante > 0:
        return False, f"⏱ Espera <b>{int(restante) + 1}s</b>.", "antispam"

    registro["usos"] += 1
    USOS_PRIVADOS[user_id] = registro
    COOLDOWN_PRIVADO[user_id] = ahora
    return True, f"🎁 Plan gratuito: <b>{registro['usos']}/3</b> consultas.", "ok"


def enviar_limite_alcanzado(bot, message, texto):
    """Envía el aviso de límite con imagen promocional y botones."""
    botones = types.InlineKeyboardMarkup()
    botones.add(types.InlineKeyboardButton(
        "📲 CONTACTAR AL ADMINISTRADOR", url=LINK_ADMIN
    ))
    if LINK_DESCARGA:
        botones.add(types.InlineKeyboardButton(
            "⬇️ DESCARGAR GRATIS", url=LINK_DESCARGA
        ))

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
        bot.send_photo(
            message.chat.id,
            photo=URL_IMAGEN_PROMO,
            caption=mensaje,
            **kwargs,
        )
    except Exception as exc:
        print(f"No se pudo enviar la imagen promocional: {exc}")
        bot.send_message(message.chat.id, mensaje, **kwargs)


def registrar_beta(bot):
    @bot.message_handler(commands=["miid"])
    def miid(message):
        if getattr(message, "sender_chat", None) is not None:
            bot.reply_to(message, "⚠️ Envía el comando con tu perfil, no como administrador anónimo.")
            return
        bot.reply_to(message, f"👤 Tu ID: <code>{message.from_user.id}</code>\n👥 Chat: <code>{message.chat.id}</code>", parse_mode="HTML")

    @bot.message_handler(commands=["addgrupo"])
    def addgrupo(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        try:
            _, identificador, limite, espera = message.text.split()
            identificador, limite = int(identificador), int(limite)
            espera = convertir_antispam(espera)
            if identificador >= 0 or limite <= 0:
                raise ValueError("Grupo o límite inválido")
            anteriores = GRUPOS_AUTORIZADOS.get(identificador, {}).get("usuarios", {})
            GRUPOS_AUTORIZADOS[identificador] = {
                "limite_diario": limite, "anti_spam": espera, "usuarios": anteriores
            }
            guardar_grupos()
            bot.reply_to(message, f"✅ Grupo <code>{identificador}</code> autorizado.\n📊 {limite} consultas por persona.\n⏱ {espera}s de AntiSpam.", parse_mode="HTML")
        except (ValueError, TypeError):
            bot.reply_to(message, "Uso: <code>/addgrupo ID_GRUPO LIMITE 30s</code>", parse_mode="HTML")

    @bot.message_handler(commands=["delgrupo"])
    def delgrupo(message):
        if message.from_user.id not in ADMIN_IDS:
            return
        try:
            identificador = int(message.text.split()[1])
            if identificador not in GRUPOS_AUTORIZADOS:
                bot.reply_to(message, "⚠️ Grupo no autorizado.")
                return
            del GRUPOS_AUTORIZADOS[identificador]
            COOLDOWN_GRUPOS.pop(identificador, None)
            guardar_grupos()
            bot.reply_to(message, "✅ Grupo eliminado de los autorizados.")
        except (ValueError, IndexError):
            bot.reply_to(message, "Uso: /delgrupo ID_GRUPO")

    @bot.message_handler(commands=["resetdb"])
    def resetdb(message):
        user_id = message.from_user.id
        if user_id not in ADMIN_IDS:
            bot.reply_to(message, "❌ No tienes permiso.")
            return
        partes = message.text.split()
        if len(partes) == 1:
            RESET_CONFIRMACIONES[user_id] = time.time()
            bot.reply_to(message, "⚠️ Reiniciará grupos y contadores. Confirma en 60 segundos con /resetdb confirmar")
            return
        if len(partes) != 2 or partes[1].lower() != "confirmar":
            bot.reply_to(message, "Uso: /resetdb confirmar")
            return
        inicio = RESET_CONFIRMACIONES.get(user_id)
        if inicio is None or time.time() - inicio > 60:
            RESET_CONFIRMACIONES.pop(user_id, None)
            bot.reply_to(message, "⌛ Confirmación inexistente o vencida. Usa /resetdb primero.")
            return
        GRUPOS_AUTORIZADOS.clear()
        COOLDOWN_GRUPOS.clear()
        COOLDOWN_PRIVADO.clear()
        USOS_PRIVADOS.clear()
        RESET_CONFIRMACIONES.pop(user_id, None)
        guardar_grupos()
        bot.reply_to(message, "✅ Grupos y contadores reiniciados.")

    @bot.message_handler(commands=list(SERVICIOS))
    def consultas(message):
        if message.chat.id < 0 and getattr(message, "sender_chat", None) is not None:
            bot.reply_to(message, "⚠️ No se puede identificar al administrador anónimo. Envía con tu perfil personal.")
            return
        partes = message.text.split(maxsplit=1)
        if len(partes) < 2:
            bot.reply_to(message, "ℹ️ Para esta demostración usa /yape prueba (o el comando de servicio correspondiente).")
            return
        permitido, texto, motivo = evaluar_permiso(message.chat.id, message.from_user.id)
        if not permitido:
            if motivo == "limite_agotado":
                enviar_limite_alcanzado(bot, message, texto)
            else:
                bot.reply_to(message, texto, parse_mode="HTML")
            return
        # Solo ejemplo de límites y mensajería: NO produce comprobantes de pago.
        bot.reply_to(message, "✅ <b>Consulta de demostración registrada.</b>\n" + texto + "\n\nℹ️ No se ha efectuado ni certificado ningún pago.", parse_mode="HTML")

