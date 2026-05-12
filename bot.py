import os
import telebot
from google import genai

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_KEY = os.environ.get("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

bot = telebot.TeleBot(BOT_TOKEN)
client = genai.Client(api_key=API_KEY)

@bot.message_handler(func=lambda message: True)
def reply(message):
    res = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=message.text
    )
    bot.reply_to(message, res.text)

bot.infinity_polling()
