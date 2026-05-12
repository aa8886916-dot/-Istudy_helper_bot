import os
import time
import base64
import requests
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# --- Flask Keep-Alive ---
app = Flask('')

@app.route('/')
def home(): return "I am alive"

def run(): app.run(host='0.0.0.0', port=8080)

def keep_alive(): Thread(target=run).start()

# --- Secrets ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

bot = telebot.TeleBot(BOT_TOKEN)

# --- Model ---
MODEL = "google/gemini-flash-1.5"

# --- System Prompts ---
SYSTEM_PROMPT = """أنت أستاذ أكاديمي عراقي كبير ومشجع اسمك "أستاذ زين".
قواعدك:
- ناد الطالب دائماً بـ "بطل" أو "كفو" بشكل طبيعي
- اشرح كل مسألة خطوة بخطوة بشكل واضح
- استخدم Markdown للتنسيق (عناوين، نقاط، جدول)
- استخدم LaTeX للمعادلات الرياضية (مثل: $E=mc^2$)
- إذا كان الموضوع معقداً، اصنع خريطة ذهنية بالإيموجي والتسلسل الهرمي
- كن دائماً إيجابياً ومشجعاً"""

TUTOR_PROMPT = """أنت معلم سقراطي عراقي. قاعدتك الذهبية: لا تعطِ الإجابة أبداً بشكل مباشر.
بدلاً من ذلك:
- اسأل أسئلة توجيهية تقود الطالب للإجابة بنفسه
- أعطِ تلميحات تدريجية
- شجّع على كل خطوة صحيحة بـ "كفو! وصلت لخطوة مهمة"
- إذا أجاب الطالب بشكل صحيح تماماً، قل "بطل! إجابة صحيحة 100% 🏆" وأخبره أنه كسب نقطة IQ"""

# --- Per-user state ---
memory = {}        # {uid: [messages]}
tutor_mode = {}    # {uid: bool}
iq_points = {}     # {uid: int}
last_request = {}  # {uid: float} anti-spam
user_stats = {}    # {uid: {name, count}}


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def get_action_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("توضيح أكثر 💡", callback_data="clarify"),
        types.InlineKeyboardButton("اختبرني 📝", callback_data="quiz")
    )
    kb.row(
        types.InlineKeyboardButton("المختصر المفيد 📋", callback_data="summary")
    )
    return kb


def call_api(messages, system=None):
    if system is None:
        system = SYSTEM_PROMPT
    payload_messages = [{"role": "system", "content": system}] + messages
    for attempt in range(3):
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={"model": MODEL, "messages": payload_messages},
                timeout=45
            )
            data = resp.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            code = data.get("error", {}).get("code")
            if code == 429:
                time.sleep(3)
                continue
            return f"خطأ من الخادم: {data.get('error', {}).get('message', str(data))}"
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                return f"فشل الاتصال بالخادم: {str(e)}"
    return "تعذّر الاتصال، حاول مرة ثانية."


def check_spam(uid):
    now = time.time()
    if uid in last_request and now - last_request[uid] < 3:
        return True
    last_request[uid] = now
    return False


def track_user(message):
    uid = message.from_user.id
    name = message.from_user.first_name or "مجهول"
    if uid not in user_stats:
        user_stats[uid] = {"name": name, "count": 0}
    user_stats[uid]["count"] += 1


def safe_delete(chat_id, msg_id):
    try:
        bot.delete_message(chat_id, msg_id)
    except Exception:
        pass


# ─────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────

@bot.message_handler(commands=['start'])
def cmd_start(message):
    name = message.from_user.first_name or "بطل"
    bot.reply_to(message,
        f"هلا {name} 👋\n\n"
        "أنا *أستاذ زين* — مساعدك الدراسي الذكي 📚\n\n"
        "ارسلي:\n"
        "• 💬 أي سؤال نصي\n"
        "• 🖼 صورة من كتابك أو سبورتك\n"
        "• 📄 ملف PDF للتلخيص\n"
        "• 🎙 رسالة صوتية\n\n"
        "📌 *الأوامر:*\n"
        "/tutor — وضع التدريس السقراطي 🎓\n"
        "/plan — مخطط دراسي بوميدورو 📅\n"
        "/stats — نقاط IQ وإحصائياتك 🏆\n"
        "/help — دليل الاستخدام",
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['help'])
def cmd_help(message):
    bot.reply_to(message,
        "📖 *دليل أستاذ زين:*\n\n"
        "• ارسل سؤالك وأجاوبك خطوة بخطوة\n"
        "• ارسل صورة (كتاب/سبورة) وأحللها\n"
        "• ارسل PDF وألخصه\n"
        "• ارسل رسالة صوتية وأفهمها\n\n"
        "🎓 /tutor — وضع توجيه بالأسئلة بدل الإجابة المباشرة\n"
        "📅 /plan — مخطط دراسي مفصل\n"
        "🏆 /stats — نقاط IQ والإحصائيات\n\n"
        "بعد كل جواب تظهر أزرار:\n"
        "💡 توضيح أكثر | 📝 اختبرني | 📋 المختصر",
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['tutor'])
def cmd_tutor(message):
    uid = message.from_user.id
    tutor_mode[uid] = not tutor_mode.get(uid, False)
    if tutor_mode[uid]:
        bot.reply_to(message,
            "🎓 *وضع التدريس السقراطي مفعّل!*\n\n"
            "راح أوجهك بأسئلة وتلميحات بدل ما أعطيك الجواب مباشرة.\n"
            "كل إجابة صحيحة = نقطة IQ 🧠",
            parse_mode='Markdown'
        )
    else:
        bot.reply_to(message, "✅ رجعنا للوضع العادي. دزلي أي سؤال بطل!")


@bot.message_handler(commands=['plan'])
def cmd_plan(message):
    msg = bot.reply_to(message,
        "📅 زيني:\n"
        "1️⃣ اسم المادة أو المواد\n"
        "2️⃣ تاريخ الامتحان\n\n"
        "مثال: *رياضيات وفيزياء، الامتحان بعد 5 أيام*",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, generate_plan)


def generate_plan(message):
    uid = message.chat.id
    bot.send_chat_action(uid, 'typing')
    wait = bot.reply_to(message, "⏳ جاري إعداد مخططك الدراسي...")
    result = call_api([{
        "role": "user",
        "content": (
            f"اصنع مخططاً دراسياً بأسلوب بوميدورو (25 دقيقة دراسة + 5 دقائق راحة) لـ:\n{message.text}\n\n"
            "رتّبه باليوم والساعة، وأضف نصائح مراجعة في نهاية كل يوم."
        )
    }])
    safe_delete(uid, wait.message_id)
    bot.reply_to(message, result, parse_mode='Markdown')


@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    uid = message.from_user.id
    points = iq_points.get(uid, 0)
    count = user_stats.get(uid, {}).get("count", 0)
    if points >= 20:
        rank = "🏅 أستاذ!"
    elif points >= 10:
        rank = "⭐ متميز"
    elif points >= 5:
        rank = "📈 متقدم"
    else:
        rank = "🌱 مبتدئ"
    bot.reply_to(message,
        f"🏆 *إحصائياتك:*\n\n"
        f"🧠 نقاط IQ: *{points}*\n"
        f"🎖 الرتبة: {rank}\n"
        f"💬 عدد الأسئلة: {count}\n\n"
        f"{'واصل تذاكر وراح تطلع بطل! 💪' if points < 10 else 'كفو، استمر على هذا المستوى! 🔥'}",
        parse_mode='Markdown'
    )


# ─────────────────────────────────────────
# ADMIN COMMANDS
# ─────────────────────────────────────────

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace('/broadcast', '', 1).strip()
    if not text:
        bot.reply_to(message, "اكتب الرسالة بعد الأمر.\nمثال: /broadcast أهلاً بالجميع!")
        return
    sent = 0
    for uid in list(user_stats.keys()):
        try:
            bot.send_message(uid, f"📢 *إعلان من الإدارة:*\n\n{text}", parse_mode='Markdown')
            sent += 1
        except Exception:
            pass
    bot.reply_to(message, f"✅ تم الإرسال لـ {sent} مستخدم.")


@bot.message_handler(commands=['adminstats'])
def cmd_adminstats(message):
    if message.from_user.id != ADMIN_ID:
        return
    total_users = len(user_stats)
    total_msgs = sum(v["count"] for v in user_stats.values())
    top = sorted(iq_points.items(), key=lambda x: x[1], reverse=True)[:5]
    top_text = "\n".join(
        f"{i+1}. {user_stats.get(uid, {}).get('name', uid)}: {pts} نقطة"
        for i, (uid, pts) in enumerate(top)
    ) or "لا يوجد بيانات"
    bot.reply_to(message,
        f"📊 *إحصائيات النظام:*\n\n"
        f"👥 المستخدمون: {total_users}\n"
        f"💬 إجمالي الرسائل: {total_msgs}\n\n"
        f"🏆 *أعلى 5 بـ IQ:*\n{top_text}",
        parse_mode='Markdown'
    )


# ─────────────────────────────────────────
# TEXT MESSAGES
# ─────────────────────────────────────────

@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_text(message):
    uid = message.chat.id
    if check_spam(uid):
        bot.reply_to(message, "⏳ انتظر ثانية بين كل سؤال.")
        return
    track_user(message)
    bot.send_chat_action(uid, 'typing')
    wait = bot.reply_to(message, "🔄 جاري التفكير...")

    if uid not in memory:
        memory[uid] = []
    memory[uid].append({"role": "user", "content": message.text})
    memory[uid] = memory[uid][-10:]

    system = TUTOR_PROMPT if tutor_mode.get(uid) else SYSTEM_PROMPT
    result = call_api(memory[uid], system=system)
    memory[uid].append({"role": "assistant", "content": result})

    if tutor_mode.get(uid) and any(w in result for w in ["صحيح 100%", "بطل!", "إجابة صحيحة"]):
        iq_points[uid] = iq_points.get(uid, 0) + 1

    safe_delete(uid, wait.message_id)
    bot.reply_to(message, result, parse_mode='Markdown', reply_markup=get_action_keyboard())


# ─────────────────────────────────────────
# PHOTO
# ─────────────────────────────────────────

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.chat.id
    if check_spam(uid):
        bot.reply_to(message, "⏳ انتظر ثانية بين كل طلب.")
        return
    track_user(message)
    bot.send_chat_action(uid, 'upload_photo')
    wait = bot.reply_to(message, "🔍 جاري تحليل الصورة... انتظر ⏳")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image_b64 = base64.b64encode(downloaded_file).decode('utf-8')
        caption = message.caption or (
            "أنت مساعد دراسي محترف. حلل هذه الصورة: "
            "إذا كانت سؤالاً فحلّه بالتفصيل خطوة بخطوة، "
            "وإذا كانت شرحاً أو نصاً فلخّصه وأبرز أهم النقاط."
        )
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "text", "text": caption},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]}
                ]
            },
            timeout=45
        )
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        safe_delete(uid, wait.message_id)
        bot.reply_to(message, text, parse_mode='Markdown', reply_markup=get_action_keyboard())
    except Exception as e:
        safe_delete(uid, wait.message_id)
        bot.reply_to(message, f"ما گدرت أقرأ الصورة، جرب صورة أوضح.\nالخطأ: {str(e)}")


# ─────────────────────────────────────────
# PDF
# ─────────────────────────────────────────

@bot.message_handler(content_types=['document'])
def handle_document(message):
    uid = message.chat.id
    if check_spam(uid):
        bot.reply_to(message, "⏳ انتظر ثانية بين كل طلب.")
        return
    track_user(message)
    if message.document.mime_type != 'application/pdf':
        bot.reply_to(message, "أرسل ملف PDF فقط.")
        return
    bot.send_chat_action(uid, 'typing')
    wait = bot.reply_to(message, "📄 جاري قراءة الـ PDF... انتظر ⏳")
    try:
        import fitz
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        doc = fitz.open(stream=downloaded_file, filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        doc.close()
        if len(text.strip()) < 50:
            safe_delete(uid, wait.message_id)
            bot.reply_to(message, "الـ PDF ما يحتوي على نص قابل للقراءة (قد يكون صور فقط).")
            return
        if len(text) > 8000:
            text = text[:8000] + "\n...[مقتطع]"
        result = call_api([{
            "role": "user",
            "content": f"لخّص هذا الملف الدراسي وأبرز أهم النقاط والمفاهيم:\n\n{text}"
        }])
        safe_delete(uid, wait.message_id)
        bot.reply_to(message, result, parse_mode='Markdown', reply_markup=get_action_keyboard())
    except ImportError:
        safe_delete(uid, wait.message_id)
        bot.reply_to(message, "⚠️ مكتبة PDF غير متوفرة.")
    except Exception as e:
        safe_delete(uid, wait.message_id)
        bot.reply_to(message, f"ما گدرت أقرأ الـ PDF.\nالخطأ: {str(e)}")


# ─────────────────────────────────────────
# VOICE
# ─────────────────────────────────────────

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    uid = message.chat.id
    track_user(message)
    bot.send_chat_action(uid, 'typing')
    wait = bot.reply_to(message, "🎙️ جاري فهم رسالتك الصوتية... ⏳")
    try:
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        audio_b64 = base64.b64encode(downloaded_file).decode('utf-8')
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": [
                        {"type": "text", "text": "استمع لهذه الرسالة الصوتية وأجب على السؤال فيها بالتفصيل."},
                        {"type": "image_url", "image_url": {"url": f"data:audio/ogg;base64,{audio_b64}"}}
                    ]}
                ]
            },
            timeout=45
        )
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        safe_delete(uid, wait.message_id)
        bot.reply_to(message, text, parse_mode='Markdown', reply_markup=get_action_keyboard())
    except Exception as e:
        safe_delete(uid, wait.message_id)
        bot.reply_to(message, f"ما گدرت أفهم الرسالة الصوتية.\nالخطأ: {str(e)}")


# ─────────────────────────────────────────
# INLINE BUTTON CALLBACKS
# ─────────────────────────────────────────

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.message.chat.id
    bot.answer_callback_query(call.id, "⏳ جاري المعالجة...")
    bot.send_chat_action(uid, 'typing')

    last_msgs = memory.get(uid, [])
    if not last_msgs:
        bot.send_message(uid, "ما في محادثة سابقة، ابدأ بسؤال جديد.")
        return

    prompts = {
        "clarify": "وضّح آخر نقطة شرحتها بمثال عملي أبسط وأكثر تفصيلاً",
        "quiz":    "اصنع سؤال MCQ واحد عن آخر موضوع تحدثنا عنه مع 4 خيارات وبيّن الإجابة الصحيحة",
        "summary": "لخّص آخر موضوع تحدثنا عنه في نقاط مرتبة لا تتجاوز 10 أسطر"
    }
    prompt_text = prompts.get(call.data, "وضّح أكثر")
    msgs = last_msgs + [{"role": "user", "content": prompt_text}]
    result = call_api(msgs)

    memory[uid] = (msgs + [{"role": "assistant", "content": result}])[-10:]
    bot.send_message(uid, result, parse_mode='Markdown', reply_markup=get_action_keyboard())


# ─────────────────────────────────────────
# LAUNCH
# ─────────────────────────────────────────

if __name__ == "__main__":
    keep_alive()
    print("✅ أستاذ زين انطلق بنجاح!")
    bot.infinity_polling()
