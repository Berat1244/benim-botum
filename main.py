import telebot
from telebot import types
import os
import sqlite3
from datetime import datetime
import threading
from flask import Flask

# --- RENDER/KOYEB WEB SERVER AYARI ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Aktif!"

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- VERİTABANI BAĞLANTISI ---
# Render'da kilitlenme hatası almamak için check_same_thread=False ekledik
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 5, invited_by INTEGER)''')
conn.commit()

# --- BOT AYARLARI ---
# Token'ı tırnak içine doğru yazdığından emin ol
TOKEN = '7990158345:AAGfUNFVw7dCiKOkTjb3UlobGxsADBNCW2w'
bot = telebot.TeleBot(TOKEN)

# --- KOMUTLAR ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    # Referans kontrolü
    args = message.text.split()
    invited_by = None
    if len(args) > 1:
        invited_by = int(args[1])

    # Kullanıcıyı kaydet
    cursor.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user is None:
        # Yeni kullanıcı
        cursor.execute("INSERT INTO users (user_id, credits, invited_by) VALUES (?, ?, ?)", (user_id, 5, invited_by))
        conn.commit()
        if invited_by:
            cursor.execute("UPDATE users SET credits = credits + 1 WHERE user_id = ?", (invited_by,))
            conn.commit()
            bot.send_message(invited_by, "🎉 Bir arkadaşın davetinle katıldı! +1 Hak kazandın.")
    
    # Güncel bilgileri çek
    cursor.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
    credits = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE invited_by = ?", (user_id,))
    invite_count = cursor.fetchone()[0]

    ref_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
    
    welcome_text = (
        f"✅ **BOTUNA HOŞ GELDİN!** 🎉\n\n"
        f"💎 **Mevcut Hakkın:** {credits}\n"
        f"👥 **Toplam Davetin:** {invite_count}\n\n"
        f"🔗 **Referans Linkin:**\n`{ref_link}`\n\n"
        f"Arkadaşlarını davet ederek her kişi için +1 hak kazanabilirsin!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

# --- BOTU BAŞLAT ---
if __name__ == "__main__":
    # Flask sunucusunu ayrı bir kolda başlat (Render için şart)
    t = threading.Thread(target=run_flask)
    t.start()
    
    print("Bot başlatılıyor...")
    # Çakışmaları önlemek için eski update'leri temizle
    bot.remove_webhook()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
