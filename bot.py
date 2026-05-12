import os
import logging
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# 🔐 CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# موديل ثابت ومستقر
MODEL = "openai/gpt-4o-mini"

# =========================
# ⚙️ LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# 🌐 KEEP ALIVE (Replit)
# =========================
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "🔥 Legend Bot is LIVE"

def run_web():
    app_flask.run(host="0.0.0.0", port=8080)

    def keep_alive():
        t = Thread(target=run_web)
        t.daemon = True
        t.start()

# =========================
# 🤖 AI ENGINE (OpenRouter)
# =========================
def ask_ai(prompt: str) -> str:
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://replit.com",
            "X-Title": "LegendBot"
        }

        system_prompt = """
أنت مساعد ذكي عراقي 👨‍🏫🔥

القواعد:
- إذا السؤال دراسي: اشرح خطوة خطوة وبأسلوب واضح.
- إذا رياضيات: حل مرتب مع خطوات.
- إذا ترجمة: ترجم بدقة.
- إذا كتابة: اكتب بشكل احترافي.
- إذا سؤال عام: جاوب باختصار ووضوح.
- إذا طلب ترفيه: رد بخفة.
- دائماً أضف "الخلاصة 📋" عند الشرح أو الحل.
"""

        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }

        res = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=40
        )

        # إذا OpenRouter رجع خطأ، خلّه يطلع حتى نعرف السبب
        if res.status_code != 200:
            return f"⚠️ OpenRouter Error:\n{res.text}"

        result = res.json()
        return result["choices"][0]["message"]["content"]

    except Exception as e:
        logging.error(e)
        return f"🤕 Error:\n{str(e)}"

# =========================
# 🚀 /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📚 دراسة", "🌍 ترجمة"],
        ["✍️ كتابة", "🧠 سؤال عام"],
        ["😂 ترفيه", "📷 صورة"]
    ]

    await update.message.reply_text(
        "🔥 أهلاً بطل!\n"
        "أنا Legend Bot 👨‍🏫🌍\n"
        "أرسل سؤال، نص، أو صورة وأنا أساعدك.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )

# =========================
# 👨‍🏫 /tutor
# =========================
async def tutor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👨‍🏫 وضع المدرّس مفعّل.\n"
        "أرسل أي سؤال وأنا أشرحه بالتفصيل."
    )

# =========================
# 🧠 TEXT HANDLER
# =========================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip().lower()

        if "ترجم" in text:
            prompt = "ترجم هذا النص بدقة:\n" + text

        elif "شرح" in text or "اشرح" in text:
            prompt = "اشرح هذا الدرس خطوة خطوة:\n" + text

        elif "اكتب" in text:
            prompt = "اكتب هذا بشكل احترافي:\n" + text

        elif "نكتة" in text:
            prompt = "اعطني نكتة قصيرة مضحكة"

        elif "اختبار" in text:
            prompt = "أنشئ اختبار مع أجوبة:\n" + text

        else:
            prompt = text

        reply = ask_ai(prompt)

        await update.message.reply_text(
            "🤖 النتيجة:\n\n" + reply
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(
            "صار خطأ أثناء معالجة الرسالة 🤕"
        )

# =========================
# 📷 IMAGE HANDLER
# =========================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        image_url = file.file_path

        prompt = f"""
هذه صورة من المستخدم.

إذا كانت سؤال دراسي:
1) استخرج السؤال
2) حلّه خطوة خطوة
3) اشرح مثل مدرس
4) أضف الخلاصة 📋

إذا ليست سؤال:
صف الصورة بشكل واضح.

رابط الصورة:
{image_url}
"""

        reply = ask_ai(prompt)

        await update.message.reply_text(
            "📷 تحليل الصورة:\n\n" + reply
        )

    except Exception as e:
        logging.error(e)
        await update.message.reply_text(
            "ما قدرت أفهم الصورة 🤕 حاول بصورة أوضح."
        )

# =========================
# 🔧 MAIN
# =========================
def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN missing in Secrets")
        return

    if not OPENROUTER_API_KEY:
        print("❌ OPENROUTER_API_KEY missing in Secrets")
        return

    keep_alive()

    app = ApplicationBuilder().token(
        TELEGRAM_TOKEN
    ).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tutor", tutor))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        )
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            handle_photo
        )
    )

    print("🔥 LEGEND BOT IS RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()