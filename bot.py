import os
import telebot
import google.generativeai as genai

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@bot.message_handler(func=lambda message: True)
def reply(message):
    res = model.generate_content(message.text)
    bot.reply_to(message, res.text)

bot.infinity_polling()
