import os
import telebot
import requests

TOKEN = os.environ.get('BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

bot = telebot.TeleBot(TOKEN)

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

if __name__ == "__main__":
    print("البوت انطلق بنجاح...")
    bot.infinity_polling()
