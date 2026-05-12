import os
import telebot
import requests

TOKEN = os.environ.get('BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TOKEN)

# ذاكرة المحادثات
memory = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "هلا 👋\nاني بوت دراسة بالذكاء الاصطناعي.\nارسل أي سؤال أو واجب وأنا أساعدك 📚"
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(
        message,
        "/start - تشغيل البوت\n/help - المساعدة\n\nارسل أي سؤال وأنا أجاوبك 🤖"
    )

@bot.message_handler(func=lambda message: True)
def reply(message):
    try:
        user_id = message.chat.id

        if user_id not in memory:
            memory[user_id] = []

        memory[user_id].append({
            "role": "user",
            "content": message.text
        })

        memory[user_id] = memory[user_id][-10:]

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": memory[user_id]
            }
        )

        data = response.json()
        text = data["choices"][0]["message"]["content"]

        memory[user_id].append({
            "role": "assistant",
            "content": text
        })

        bot.reply_to(message, text)

    except Exception as e:
        bot.reply_to(message, str(e))

print("Bot is running...")
bot.infinity_polling()
