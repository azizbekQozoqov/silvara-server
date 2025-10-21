from telebot import TeleBot, types
from dotenv import load_dotenv
import os
import json
import logging

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)
logger = logging.getLogger('silvara')

# Admin/group chat to forward orders to
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")  # e.g., -1001234567890 for groups, or admin user id
if TARGET_CHAT_ID:
    try:
        TARGET_CHAT_ID = int(TARGET_CHAT_ID)
    except ValueError:
        # keep as string; TeleBot accepts str ids too
        pass

# Optional: URL of deployed web app (set via BotFather Web App / domain settings)
WEBAPP_URL = os.getenv("WEBAPP_URL")  # e.g., https://silvara.uz/raviosta/bot/

@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "Welcome to Raviosta Kitchen!\n"
        "Open the menu to browse dishes and place your order."
    )
    if WEBAPP_URL:
        # Reply keyboard button that opens the WebApp
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton("Open Menu", web_app=types.WebAppInfo(WEBAPP_URL)))
        bot.send_message(message.chat.id, text, reply_markup=kb)
    else:
        bot.send_message(message.chat.id, text)


def _format_order_text(order: dict) -> str:
    customer = order.get('customer') or {}
    loc = order.get('location') or {}
    items = order.get('items') or []
    total = order.get('total') or 0
    parts = []
    parts.append("🧾 New Raviosta Order")
    if order.get('timestamp'):
        parts.append(f"⏱ {order['timestamp']}")
    parts.append("")
    parts.append("👤 Customer:")
    parts.append(f"• Name: {customer.get('name','-')}")
    parts.append(f"• Phone: {customer.get('phone','-')}")
    if customer.get('comment'):
        parts.append(f"• Comment: {customer['comment']}")
    parts.append("")
    parts.append("🍽 Items:")
    for it in items:
        parts.append(f"• {it.get('name','?')} ×{it.get('quantity',1)} — {it.get('price',0):,} so'm")
    parts.append("")
    parts.append(f"💰 Total: {total:,} so'm")
    if loc.get('lat') and loc.get('lng'):
        lat = loc['lat']; lng = loc['lng']
        parts.append("")
        parts.append(f"📍 Location: {lat:.5f}, {lng:.5f}")
        parts.append(f"🔗 https://maps.google.com/?q={lat},{lng}")
    return "\n".join(parts)


@bot.message_handler(content_types=['web_app_data'])
def handle_webapp_data(message: types.Message):
    """
    Receives data from Telegram WebApp via WebApp.sendData(JSON_STRING)
    and forwards a formatted order to the target chat.
    """
    try:
        data_raw = message.web_app_data.data if message.web_app_data else None
        if not data_raw:
            bot.reply_to(message, "No order data received.")
            return
        order = json.loads(data_raw)
    except Exception as e:
        logger.exception("Failed to parse web_app_data")
        bot.reply_to(message, "Failed to read your order data. Please try again.")
        return

    try:
        text = _format_order_text(order)
        dest = TARGET_CHAT_ID or message.chat.id
        # Forward order summary
        bot.send_message(dest, text)
        # Send pin if location present
        loc = order.get('location') or {}
        if loc.get('lat') and loc.get('lng'):
            bot.send_location(dest, latitude=loc['lat'], longitude=loc['lng'])
        # Acknowledge to the user
        bot.reply_to(message, "✅ Your order was sent. We will contact you soon.")
    except Exception:
        logger.exception("Failed to forward order to target chat")
        bot.reply_to(message, "Could not forward your order. Please try again later.")

