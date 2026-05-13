import os
import json
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
    filters
)

# =========================
# 🔐 CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ضع ID الخاص بك هنا أو في Secrets
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
except:
    ADMIN_ID = 123456789 # استبدله بـ ID مالتك إذا ما ضفته بالـ Secrets

MODEL = os.getenv("MODEL", "openai/gpt-4o-mini")

logging.basicConfig(level=logging.INFO)

# =========================
# 🌐 KEEP ALIVE
# =========================
app = Flask(__name__)
@app.route("/")
def home(): return "🔥 ULTIMATE PRO BOT IS LIVE"

def run_web(): app.run(host="0.0.0.0", port=8080)
def keep_alive(): Thread(target=run_web, daemon=True).start()

# =========================
# 💾 DATABASE (نظام الحفظ الذكي)
# =========================
DB_FILE = "users.json"

def load_db():
    """هذه الدالة تضمن أن الملف دائماً يبدأ بـ {} وبدون أخطاء"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: json.dump({}, f)
        return {}
    with open(DB_FILE, "r") as f:
        try:
            data = json.load(f)
            if not isinstance(data, dict): # إذا لقى قائمة [] قديمة يصفرها فوراً
                return {}
            return data
        except:
            return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4) # indent حتى يكون شكل الملف مرتب وسهل القراءة

def get_user(db, uid):
    uid = str(uid) # تحويل الـ ID لنص دائماً لمنع خطأ TypeError
    if uid not in db:
        db[uid] = {
            "name": "",
            "level": 1,
            "weakness": {"رياضيات": 0, "فيزياء": 0, "كيمياء": 0, "انكليزي": 0},
            "chat": []
        }
    return db[uid]

# =========================
# 🧠 كاشف نقاط الضعف
# =========================
def detect_weakness(user, text):
    subjects = {
        "رياضيات": ["x", "y", "حل", "معادلة", "تكامل", "جذر", "تربيع"],
        "فيزياء": ["قوة", "سرعة", "طاقة", "نيوتن", "ضغط", "كهرباء"],
        "كيمياء": ["ذرة", "عنصر", "تفاعل", "مركب", "جدول دوري"],
        "انكليزي": ["verb", "grammar", "tense", "ترجمة", "english"]
    }
    text = text.lower()
    for subject, keys in subjects.items():
        for k in keys:
            if k in text:
                user["weakness"][subject] = user["weakness"].get(subject, 0) + 1

# =========================
# 🤖 AI ENGINE
# =========================
def ask_ai(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"model": MODEL, "messages": messages}, timeout=60)
        return r.json()["choices"][0]["message"]["content"]
    except: return "🤕 عذراً، واجهت مشكلة بالاتصال بالذكاء الاصطناعي."

# =========================
# 🚀 الأوامر (Handlers)
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    get_user(db, update.effective_user.id)
    save_db(db)

    keyboard = [
        ["📚 دراسة", "📷 صورة"],
        ["🎯 خطتي", "📊 إحصائياتي"],
        ["🏆 نقاطي"]
    ]
    await update.message.reply_text(
        "🔥 أهلاً بطل!\nأنا مدرسك الذكي 👨‍🏫\nأرسل أي سؤال أو صورة وخل نبدأ!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = get_user(db, update.effective_user.id)
    weakness = max(user["weakness"], key=user["weakness"].get) if any(user["weakness"].values()) else "رياضيات"
    await update.message.reply_text(f"🎯 **خطة اليوم لـ {user['name']}:**\n\n📚 ركز على: {weakness}\n⏱️ مراجعة 30 دقيقة\n🧠 حل 3 تمارين")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    user = get_user(db, update.effective_user.id)
    w_info = ", ".join([f"{k}:{v}" for k,v in user["weakness"].items() if v > 0])
    await update.message.reply_text(f"📊 **إحصائياتك:**\n👤 الاسم: {user['name']}\n📈 المستوى: {user['level']}\n⚠️ تفاعلك: {w_info if w_info else 'لا توجد بيانات'}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = load_db()
    uid = str(update.effective_user.id)
    user = get_user(db, uid)

    if not user["name"]: user["name"] = update.effective_user.first_name or "بطل"

    text = update.message.text
    detect_weakness(user, text)

    user["chat"].append({"role": "user", "content": text})
    user["chat"] = user["chat"][-10:] # حفظ آخر 10 رسائل فقط للذاكرة

    system = f"أنت مدرس عراقي ذكي ومرح. الطالب: {user['name']}. مستواه: {user['level']}."
    reply = ask_ai([{"role": "system", "content": system}] + user["chat"])

    user["chat"].append({"role": "assistant", "content": reply})
    if len(user["chat"]) % 6 == 0: user["level"] += 1 # زيادة المستوى مع كل 3 حوارات

    save_db(db)
    await update.message.reply_text(reply)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_url = file.file_path

        prompt = update.message.caption or "حل السؤال بالصورة"
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_url}}]}]}
        ).json()
        await update.message.reply_text("📷 **الحل:**\n\n" + res["choices"][0]["message"]["content"])
    except: await update.message.reply_text("🤕 خطأ في الصورة.")

# 👑 ADMIN
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    db = load_db()
    await update.message.reply_text(f"👑 الإدارة\n👥 الطلاب: {len(db)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    db = load_db()
    text = " ".join(context.args)
    count = 0
    for uid in db:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 **تنبيه:**\n\n{text}")
            count += 1
        except: continue
    await update.message.reply_text(f"✅ تم الإرسال لـ {count}")

# =========================
# 🔧 RUN
# =========================
def main():
    keep_alive()
    bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("plan", plan))
    bot.add_handler(CommandHandler("stats", stats))
    bot.add_handler(CommandHandler("admin", admin))
    bot.add_handler(CommandHandler("b", broadcast))

    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    bot.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🚀 BOT IS LIVE AND SAVING DATA")
    bot.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
