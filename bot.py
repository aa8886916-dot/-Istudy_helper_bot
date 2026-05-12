import os
import telebot
import google.generativeai as genai
from flask import Flask
from threading import Thread

# --- 1. إعداد السيرفر الصغير (Keep Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. جلب المفاتيح من الـ Secrets ---
TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

# --- 3. إعداد ذكاء Gemini (الموديل المحدث) ---
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(TOKEN)

# --- 4. أوامر البوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "هلا بيك! أنا بوت الذكاء الاصطناعي المحدث. اسألني أي شي وبالخدمة.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, str(e))

# --- 5. تشغيل كل شيء ---
if __name__ == "__main__":
    keep_alive()
    print("البوت انطلق بنجاح وباستخدام موديل Gemini 1.5 Flash...")
    bot.infinity_polling()
