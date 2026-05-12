import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home(): return "I am alive"

def run(): app.run(host='0.0.0.0', port=8080)

def keep_alive(): Thread(target=run).start()

TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "هلا بيك! البوت اشتغل هسة، دزلي أي سؤال.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"صارت مشكلة تقنية: {str(e)}")

if __name__ == "__main__":
    keep_alive()
    print("جاري تشغيل البوت...")
    bot.infinity_polling()
