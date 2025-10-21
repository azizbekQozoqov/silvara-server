from telebot import TeleBot, types
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    webapp = types.WebAppInfo("url='https://silvara.uz/miniapps/raviosta/'")
    markup.add(types.KeyboardButton("Open MiniApp", web_app=webapp))
    bot.send_message(message.chat.id, "Welcome!", reply_markup=markup)
