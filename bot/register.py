import requests

API_REGISTER = "https://activaciones.vercel.app/api/register"


def registrar_register(bot):

    @bot.message_handler(commands=["register"])
    def register_user(message):

        user_id = str(message.from_user.id)
        first_name = message.from_user.first_name or "Usuario"
        username = message.from_user.username or ""

        try:
            respuesta = requests.post(
                API_REGISTER,
                json={
                    "telegramId": user_id,
                    "username": username
                },
                timeout=10
            )

            datos = respuesta.json()

            if not respuesta.ok or not datos.get("success"):
                bot.reply_to(
                    message,
                    "❌ No se pudo completar el registro."
                )
                return

            bot.send_message(
                message.chat.id,
                f"✅ <b>¡Registro exitoso, {first_name}!</b>\n\n"
                "Tu cuenta ha sido registrada en <b>YapeXpress</b>.",
                parse_mode="HTML"
            )

        except Exception as error:
            print("ERROR /register:", error)

            bot.reply_to(
                message,
                "❌ Error al registrar tu cuenta."
            )