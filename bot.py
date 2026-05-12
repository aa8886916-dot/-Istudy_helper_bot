import telebot
from google import genai

BOT_TOKEN = "8712235380:AAGdw9g8Vr7k_LEJ5Qk2hlPiixhPuloCar4"
API_KEY = "AIzaSyBTPYq1OCp0oNfR6LWbhF7MuC45h9AvX5E"

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
