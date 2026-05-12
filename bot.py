import os
import telebot
import requests
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
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TOKEN)

# --- 3. أوامر البوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "هلا بيك! أنا بوت الذكاء الاصطناعي. اسألني أي شي وبالخدمة.")

@bot.message_handler(func=lambda message: True)
def reply(message):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "user",
                        "content": message.text
                    }
                ]
            }
        )
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        bot.reply_to(message, text)
    except Exception as e:
        bot.reply_to(message, str(e))

# --- 4. تشغيل كل شيء ---
if __name__ == "__main__":
    keep_alive()
    print("البوت انطلق بنجاح وباستخدام OpenRouter...")
    bot.infinity_polling()
