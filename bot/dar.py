import requests

# ==========================================
# API PARA AGREGAR CRÉDITOS
# ==========================================

API_CREDITOS = "https://activaciones.vercel.app/api/add_credits"


# ==========================================
# ADMINISTRADORES
# Pon aquí tu ID de Telegram
# ==========================================

ADMIN_IDS = [
   8635600472
]


def registrar_dar(bot):

    @bot.message_handler(commands=["dar"])
    def dar_creditos(message):

        # ==========================================
        # VERIFICAR ADMIN
        # ==========================================

        if message.from_user.id not in ADMIN_IDS:
            bot.reply_to(
                message,
                "❌ <b>No tienes permiso para usar /dar.</b>",
                parse_mode="HTML"
            )
            return

        # ==========================================
        # FORMATO:
        # /dar TELEGRAM_ID CANTIDAD
        # ==========================================

        partes = message.text.strip().split()

        if len(partes) != 3:
            bot.reply_to(
                message,
                "⚠️ <b>USO CORRECTO</b>\n\n"
                "📝 <code>/dar ID CANTIDAD</code>\n\n"
                "Ejemplo:\n"
                "<code>/dar 8635600472 50</code>",
                parse_mode="HTML"
            )
            return

        # Telegram ID como STRING
        telegram_id = partes[1].strip()

        # ==========================================
        # VALIDAR ID
        # ==========================================

        if not telegram_id.isdigit():
            bot.reply_to(
                message,
                "❌ <b>El Telegram ID debe contener solo números.</b>",
                parse_mode="HTML"
            )
            return

        # ==========================================
        # VALIDAR CANTIDAD
        # ==========================================

        try:
            cantidad = int(partes[2])

        except ValueError:
            bot.reply_to(
                message,
                "❌ <b>La cantidad debe ser un número entero.</b>",
                parse_mode="HTML"
            )
            return

        if cantidad <= 0:
            bot.reply_to(
                message,
                "❌ <b>La cantidad debe ser mayor que 0.</b>",
                parse_mode="HTML"
            )
            return

        # ==========================================
        # PAYLOAD EXACTO DE LA API
        # ==========================================

        payload = {
            "telegramId": str(telegram_id),
            "amount": cantidad
        }

        try:

            response = requests.post(
                API_CREDITOS,
                json=payload,
                timeout=15
            )

            # ==========================================
            # LEER RESPUESTA
            # ==========================================

            try:
                data = response.json()
            except ValueError:
                data = {}

            # ==========================================
            # SI LA API DEVUELVE ERROR
            # ==========================================

            if not response.ok:

                error_api = (
                    data.get("message")
                    or data.get("error")
                    or response.text
                    or "Error desconocido"
                )

                bot.reply_to(
                    message,
                    "❌ <b>ERROR AL DAR CRÉDITOS</b>\n\n"
                    f"📡 Código: <code>{response.status_code}</code>\n"
                    f"📝 <code>{error_api}</code>",
                    parse_mode="HTML"
                )
                return

            # ==========================================
            # BUSCAR SALDO DEVUELTO POR LA API
            # ==========================================

            saldo = None

            posibles_campos = [
                "credits",
                "creditos",
                "saldo",
                "newBalance",
                "nuevoSaldo",
                "balance"
            ]

            for campo in posibles_campos:
                if campo in data:
                    saldo = data[campo]
                    break

            # También revisar si viene dentro de "user"
            if saldo is None:

                usuario = data.get("user") or data.get("usuario")

                if isinstance(usuario, dict):

                    for campo in posibles_campos:
                        if campo in usuario:
                            saldo = usuario[campo]
                            break

            # ==========================================
            # MENSAJE DE ÉXITO
            # ==========================================

            texto = (
                "✅ <b>CRÉDITOS ENTREGADOS</b>\n\n"
                f"👤 Telegram ID ➣ <code>{telegram_id}</code>\n"
                f"💰 Créditos agregados ➣ <b>{cantidad}</b>"
            )

            if saldo is not None:
                texto += f"\n💳 Saldo actual ➣ <b>{saldo}</b>"

            bot.reply_to(
                message,
                texto,
                parse_mode="HTML"
            )

        # ==========================================
        # TIMEOUT
        # ==========================================

        except requests.exceptions.Timeout:

            bot.reply_to(
                message,
                "❌ <b>La API tardó demasiado en responder.</b>",
                parse_mode="HTML"
            )

        # ==========================================
        # ERROR DE CONEXIÓN
        # ==========================================

        except requests.exceptions.RequestException as error:

            bot.reply_to(
                message,
                "❌ <b>Error conectando con la API.</b>\n\n"
                f"<code>{error}</code>",
                parse_mode="HTML"
            )

        # ==========================================
        # OTRO ERROR
        # ==========================================

        except Exception as error:

            bot.reply_to(
                message,
                "❌ <b>Error inesperado.</b>\n\n"
                f"<code>{error}</code>",
                parse_mode="HTML"
            )