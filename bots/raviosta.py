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

# Simple i18n for user-facing bot messages
I18N = {
    'english': {
        'start': (
            "Welcome to Raviosta!\n"
            "Open the menu to browse dishes and place your order."
        ),
        'open_menu': "Open Menu",
        'no_order': "No order data received.",
        'parse_fail': "Failed to read your order data. Please try again.",
        'sent_ok': "✅ Your order was sent. We will contact you soon.",
        'forward_fail': "Could not forward your order. Please try again later.",
    },
    'uzbek': {
        'start': (
            "Raviosta ga xush kelibsiz!\n"
            "Menyuni ochib taomlarni ko'ring va buyurtma bering."
        ),
        'open_menu': "Menyuni ochish",
        'no_order': "Buyurtma ma'lumoti olinmadi.",
        'parse_fail': "Buyurtma ma'lumotini o‘qib bo‘lmadi. Qayta urinib ko‘ring.",
        'sent_ok': "✅ Buyurtmangiz yuborildi. Tez orada siz bilan bog‘lanamiz.",
        'forward_fail': "Buyurtmangizni yuborib bo‘lmadi. Iltimos, keyinroq qayta urinib ko‘ring.",
    },
    'russian': {
        'start': (
            "Добро пожаловать в Raviosta\n"
            "Откройте меню, чтобы выбрать блюда и оформить заказ."
        ),
        'open_menu': "Открыть меню",
        'no_order': "Данные заказа не получены.",
        'parse_fail': "Не удалось прочитать данные заказа. Попробуйте ещё раз.",
        'sent_ok': "✅ Ваш заказ отправлен. Мы скоро с вами свяжемся.",
        'forward_fail': "Не удалось переслать ваш заказ. Пожалуйста, попробуйте позже.",
    },
}

# Display names for languages (kept recognizable across locales)
LANG_DISPLAY = {
    'english': 'English',
    'uzbek': "O‘zbek",
    'russian': 'Русский',
}

# In-memory per-user language preferences (user_id -> lang key)
USER_LANG: dict[int, str] = {}

def _get_lang(message: types.Message) -> str:
    # Prefer explicit user preference if set
    try:
        uid = getattr(getattr(message, 'from_user', None), 'id', None)
        if uid and uid in USER_LANG:
            return USER_LANG[uid]
    except Exception:
        pass
    code = (getattr(getattr(message, 'from_user', None), 'language_code', '') or '').lower()
    if code.startswith('uz'):
        return 'uzbek'
    if code.startswith('ru'):
        return 'russian'
    return 'russian'

def _t(lang: str, key: str) -> str:
    return I18N.get(lang, I18N['english']).get(key, I18N['english'].get(key, key))

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
    lang = _get_lang(message)
    text = _t(lang, 'start')
    if WEBAPP_URL:
        # Reply keyboard button that opens the WebApp
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(types.KeyboardButton(_t(lang, 'open_menu'), web_app=types.WebAppInfo(WEBAPP_URL)))
        bot.send_message(message.chat.id, text, reply_markup=kb)
    else:
        bot.send_message(message.chat.id, text)


# --- Language selection (/lang) ---
def _normalize_lang_arg(arg: str | None) -> str | None:
    if not arg:
        return None
    a = arg.strip().lower()
    if a in ('en', 'eng', 'english'):
        return 'english'
    if a in ('uz', 'uzb', 'uzbek', "o'z", 'oz', 'ozb'):
        return 'uzbek'
    if a in ('ru', 'rus', 'russian', 'рус', 'русский'):
        return 'russian'
    return None


@bot.message_handler(commands=['lang'])
def cmd_lang(message: types.Message):
    lang = _get_lang(message)
    # Allow parameter: /lang en|ru|uz
    parts = (message.text or '').split()
    if len(parts) > 1:
        want = _normalize_lang_arg(parts[1])
        if want:
            USER_LANG[getattr(message.from_user, 'id', 0)] = want
            bot.reply_to(message, _t(lang, 'start').split('\n')[0] + f"\n" + _lang_set_msg(lang, want))
            return
        # Fallthrough to keyboard if invalid param

    # Show inline keyboard to select language
    prompt = _choose_lang_prompt(lang)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(LANG_DISPLAY['uzbek'], callback_data='set_lang:uzbek'),
        types.InlineKeyboardButton(LANG_DISPLAY['russian'], callback_data='set_lang:russian'),
        types.InlineKeyboardButton(LANG_DISPLAY['english'], callback_data='set_lang:english'),
    )
    bot.send_message(message.chat.id, prompt, reply_markup=kb)


def _choose_lang_prompt(lang: str) -> str:
    if lang == 'uzbek':
        return "Tilni tanlang:"
    if lang == 'russian':
        return "Выберите язык:"
    return "Choose your language:"


def _lang_set_msg(user_lang: str, new_lang: str) -> str:
    # user_lang: language to render the message in
    name = LANG_DISPLAY.get(new_lang, new_lang)
    if user_lang == 'uzbek':
        return f"Til {name} qilib o‘rnatildi."
    if user_lang == 'russian':
        return f"Язык изменён на {name}."
    return f"Language set to {name}."


@bot.callback_query_handler(func=lambda c: isinstance(c.data, str) and c.data.startswith('set_lang:'))
def cb_set_lang(call: types.CallbackQuery):
    try:
        _, val = (call.data or '').split(':', 1)
    except Exception:
        return
    if val not in ('english', 'uzbek', 'russian'):
        return
    uid = getattr(getattr(call, 'from_user', None), 'id', None)
    if uid:
        USER_LANG[uid] = val
    # Render confirmation using the newly selected language for consistency
    msg = _lang_set_msg(val, val)
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass
    # Edit message if possible, otherwise send a new one
    try:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg)
    except Exception:
        bot.send_message(call.message.chat.id, msg)


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
    lang = _get_lang(message)
    try:
        data_raw = message.web_app_data.data if message.web_app_data else None
        if not data_raw:
            bot.reply_to(message, _t(lang, 'no_order'))
            return
        order = json.loads(data_raw)
    except Exception as e:
        logger.exception("Failed to parse web_app_data")
        bot.reply_to(message, _t(lang, 'parse_fail'))
        return

    text = _format_order_text(order)
    loc = order.get('location') or {}

    # Try to send to TARGET_CHAT_ID first; if that fails, fall back to replying in the current chat
    dest_primary = TARGET_CHAT_ID or message.chat.id
    sent_ok = False

    try:
        bot.send_message(dest_primary, text)
        if loc.get('lat') and loc.get('lng'):
            bot.send_location(dest_primary, latitude=loc['lat'], longitude=loc['lng'])
        sent_ok = True
    except Exception as e:
        logger.exception("Primary forward failed (dest=%s). Falling back to user chat.", dest_primary)
        # Fallback only if primary wasn't the same as the current chat
        if dest_primary != message.chat.id:
            try:
                bot.send_message(message.chat.id, text)
                if loc.get('lat') and loc.get('lng'):
                    bot.send_location(message.chat.id, latitude=loc['lat'], longitude=loc['lng'])
                sent_ok = True
            except Exception:
                logger.exception("Fallback send to user chat also failed")

    if sent_ok:
        bot.reply_to(message, _t(lang, 'sent_ok'))
    else:
        bot.reply_to(message, _t(lang, 'forward_fail'))

