import requests

API_USER = "https://activaciones.vercel.app/api/user"

session = requests.Session()


def registrar_me(bot):

    @bot.message_handler(commands=["me"])
    def me(message):

        usuario = message.from_user
        nombre = usuario.first_name or "Sin nombre"

        username = (
            f"@{usuario.username}"
            if usuario.username
            else "@Sin_username"
        )

        try:
            # =========================
            # CONSULTAR USUARIO
            # =========================

            response = session.get(
                API_USER,
                params={"id": str(usuario.id)},
                timeout=5
            )

            if response.status_code == 404:
                bot.send_message(
                    message.chat.id,
                    "❌ <b>No estás registrado.</b>\n\n"
                    "Usa /register para registrarte.",
                    parse_mode="HTML"
                )
                return

            response.raise_for_status()

            datos = response.json()
            user = datos.get("user", {})

            creditos = user.get("credits", 0)
            dias = user.get("days", 0)

            # =========================
            # PERFIL
            # =========================

            texto = (
                "[#YapeXpress] <b>PERFIL DE USUARIO</b>\n"
                "────────────────────\n"
                "➤ <b>INFORMACIÓN DE USUARIO</b>\n\n"
                f"[ 👨‍💼 ] ID ➤ <code>{usuario.id}</code>\n"
                f"[ 📝 ] NOMBRE ➤ {nombre}\n"
                f"[ ⚡ ] USERNAME ➤ {username}\n\n"
                f"[ 💰 ] CRÉDITOS ➤ <b>{creditos}</b>\n"
                f"[ 📅 ] DÍAS ➤ <b>{dias}</b>\n\n"
                "[ 👾 ] ESTADO ➤ <b>ACTIVO</b>\n"
                "────────────────────"
            )

            # =========================
            # ENVIAR SOLO TEXTO
            # =========================

            bot.send_message(
                message.chat.id,
                texto,
                parse_mode="HTML"
            )

        except requests.exceptions.Timeout:
            bot.send_message(
                message.chat.id,
                "⚠️ El servidor está tardando demasiado."
            )

        except requests.exceptions.RequestException as error:
            print("ERROR API /me:", repr(error))

            bot.send_message(
                message.chat.id,
                "❌ No se pudo conectar con el servidor."
            )

        except Exception as error:
            print("ERROR /me:", repr(error))

            bot.send_message(
                message.chat.id,
                "❌ Error al consultar tu perfil."
            )