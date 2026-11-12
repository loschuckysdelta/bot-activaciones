"""Registro de usuarios para /register."""
import html
import requests

API_REGISTER = "https://activaciones.vercel.app/api/register"


def registrar_register(bot):
    @bot.message_handler(commands=["register"])
    def register_user(message):
        usuario = getattr(message, "from_user", None)
        if usuario is None:
            bot.reply_to(message, "❌ No pude identificar tu usuario de Telegram.")
            return

        first_name = html.escape(usuario.first_name or "Usuario")
        try:
            respuesta = requests.post(
                API_REGISTER,
                json={"telegramId": str(usuario.id), "username": usuario.username or ""},
                timeout=12,
            )
            respuesta.raise_for_status()
            datos = respuesta.json()
            if not isinstance(datos, dict) or not datos.get("success"):
                bot.reply_to(message, "❌ El servidor no confirmó tu registro.")
                return
            bot.send_message(
                message.chat.id,
                f"✅ <b>¡Registro exitoso, {first_name}!</b>\n\n"
                "Tu cuenta ha sido registrada en <b>YapeXpress</b>.",
                parse_mode="HTML",
            )
        except requests.exceptions.Timeout:
            bot.reply_to(message, "⚠️ La API de registro tardó demasiado en responder.")
        except (requests.RequestException, ValueError) as error:
            print("ERROR /register:", error)
            bot.reply_to(message, "❌ Error al consultar el servidor de registro.")
