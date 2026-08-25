def registrar_cmds(bot):

    @bot.message_handler(commands=["cmds", "commands", "help"])
    def cmds(message):
        texto = (
            "📋 <b>COMANDOS DISPONIBLES</b>\n\n"
            "•···························•····························•\n\n"
            "🪪 <b>GENERAL</b>\n"
            "/me\n"
            "Ver mi información.\n\n"
            "/buy\n"
            "Tarifario de créditos.\n\n"
            "•···························•····························•\n\n"
            "🚀 <b>ACTIVACIONES YAPE</b>\n"
            "/activate correo@gmail.com\n"
            "Activa una cuenta de un cliente registrado.\n\n"
            "/token\n"
            "Genera token de autocompletado.\n\n"
            "/info correo@gmail.com\n"
            "Ver información del cliente.\n\n"
            "/historial\n"
            "Ver el historial de tus activaciones.\n\n"
            "•···························•····························•\n\n"
            "🧾 <b>PLAN VOUCHERS</b>\n"
            "/ejemplos\n"
            "Ver galería de ejemplos\n\n"
            "/yape monto|nombre|3digitos\n"
            "/plin monto|nombre|3digitos\n"
            "/bim monto|nombre|3digitos\n"
            "/sip monto|nombre|3digitos\n"
            "/agora monto|nombre|3digitos\n"
            "/lemon monto|nombre|3digitos\n"
            "/panda monto|nombre\n"
            "/prexpe monto|nombre\n"
            "/bcp monto|nombre|3digitos\n"
            "/ibk monto|nombre|3digitos\n"
            "/bbva monto|nombre|3digitos\n"
            "/scotiabank monto|nombre|3digitos\n"
            "/falabella monto|nombre|3digitos\n"
            "/ripley monto|nombre|3digitos\n"
            "/caja monto|nombre|3digitos\n"
            "Genera vouchers de pago.\n\n"
            "•···························•····························•"
        )

        bot.send_message(
            message.chat.id,
            texto,
            parse_mode="HTML"
        )