import io
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def registrar_buy(bot):

    @bot.message_handler(commands=["buy", "comprar", "precios"])
    def buy(message):
        imagen_url = "https://i.postimg.cc/NjKPzxvX/image.png"

        texto = (
            "💳 <b>TARIFARIO DE CRÉDITOS</b>\n"
            "•···························•····························•\n\n"
            "🎯 <b>Consumo de créditos</b>\n"
            "└ Yape Fake ➤ 25 créditos\n"
            "└ Banca Fake ➤ 7 créditos\n\n"
            "📈 <b>Ganancia reseller:</b> hasta 60%. Precios libres.\n\n"
            "•···························•····························•\n\n"
            "🛒 <b>Compra tus créditos aquí 👇</b>"
        )

        markup = InlineKeyboardMarkup()
        btn_soporte = InlineKeyboardButton(
            text="🛒 COMPRAR CRÉDITOS", 
            url="https://t.me/tuchuckynet_x?text=Hola%2C%20quiero%20comprar%20cr%C3%A9ditos%20de%20YapeXpress"
        )
        markup.add(btn_soporte)

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(imagen_url, headers=headers, timeout=10)
            
            foto_bytes = io.BytesIO(response.content)
            foto_bytes.name = "banner.png"

            bot.send_photo(
                message.chat.id,
                photo=foto_bytes,
                caption=texto,
                parse_mode="HTML",
                reply_markup=markup
            )
        except Exception:
            bot.send_message(
                message.chat.id,
                texto,
                parse_mode="HTML",
                reply_markup=markup
            )