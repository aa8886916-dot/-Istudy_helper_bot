import os
import telebot
import requests
import base64

TOKEN = os.environ.get('BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TOKEN)

# ذاكرة المحادثات
memory = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "هلا 👋\nاني بوت دراسة بالذكاء الاصطناعي 📚\nارسل سؤال أو صورة وأنا أساعدك 🔥"
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(
        message,
        "📌 الأوامر:\n/start\n/help\n\nارسل نص أو صورة للسؤال 🤖"
    )

@bot.message_handler(func=lambda message: True, content_types=['text'])
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

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image_base64 = base64.b64encode(downloaded_file).decode('utf-8')

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemma-3-27b-it:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "حلل هذه الصورة واشرح محتواها"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            }
        )

        print(response.json())
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        bot.reply_to(message, text)

    except Exception as e:
        bot.reply_to(message, str(e))

print("Bot is running...")
bot.infinity_polling()
