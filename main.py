import os, re, sqlite3, datetime
from flask import Flask, request
import threading
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('protection.db')
    conn.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, platform TEXT, user TEXT, content TEXT, time TEXT)')
    conn.commit()
    conn.close()
init_db()

BAD_WORDS = ["سب","كذب","نصب","غشاش","زبالة","نصابة","حرامية","قذر","كلب"]

def log_delete(platform, user, content):
    conn = sqlite3.connect('protection.db')
    conn.execute("INSERT INTO logs VALUES (NULL,?,?,?,?)", (platform, user, content, str(datetime.datetime.now())))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return "نظام الحماية الموحد شغال - رابط واحد لكل المنصات"

@app.route('/admin')
def admin():
    conn = sqlite3.connect('protection.db')
    logs = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    html = "<h1>لوحة التحكم الموحدة</h1><table border=1><tr><th>المنصة</th><th>المستخدم</th><th>التعليق</th><th>الوقت</th></tr>"
    for l in logs:
        html+=f"<tr><td>{l[1]}</td><td>{l[2]}</td><td>{l[3]}</td><td>{l[4]}</td></tr>"
    return html+"</table>"

async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    text = update.message.text or update.message.caption or ""
    if re.search(r'(t\.me/|http|@\w+|www\.)', text) or update.message.forward_from_chat:
        if str(update.effective_user.id)!= str(ADMIN_ID):
            try:
                await update.message.delete()
                log_delete("Telegram", str(update.effective_user.id), text)
                return
            except: pass
    for w in BAD_WORDS:
        if w in text.lower():
            try:
                await update.message.delete()
                log_delete("Telegram", str(update.effective_user.id), text)
                return
            except: pass

def run_bot():
    if not BOT_TOKEN:
        return
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(MessageHandler(filters.ALL, protect))
    app_bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
