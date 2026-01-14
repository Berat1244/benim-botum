import telebot
from telebot import types
import os
import threading
import random
from flask import Flask
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
SUPABASE_URL = "https://xjtneisfuvxzjrntarze.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhqdG5laXNmdXZ4empybnRhcnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzODc1NTUsImV4cCI6MjA4Mzk2MzU1NX0.2HfFMOCywdJ4uUXeu_Vjf-Xf6v72WRxtUcIZPO63z4U"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- RENDER WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Tum Sistemler Aktif!"
def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- BOT AYARLARI ---
TOKEN = '7990158345:AAGfUNFVw7dCiKOkTjb3UlobGxsADBNCW2w'
bot = telebot.TeleBot(TOKEN)

# --- DOSYADAN HESAP ÇEKME FONKSİYONU ---
def get_account_from_file(file_name):
    try:
        # Dosya ismini kontrol et (GitHub'daki dosya isimlerinle aynı olmalı)
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    return random.choice(lines).strip()
        return None
    except:
        return None

# --- KOMUTLAR ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    invited_by = None
    if len(args) > 1:
        try: invited_by = int(args[1])
        except: invited_by = None

    # Hafıza Sistemi (Kullanıcı Kayıt)
    user_data = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not user_data.data:
        supabase.table("users").insert({"user_id": user_id, "credits": 5, "invited_by": invited_by}).execute()
        if invited_by and invited_by != user_id:
            inviter = supabase.table("users").select("credits").eq("user_id", invited_by).execute()
            if inviter.data:
                new_credits = inviter.data[0]['credits'] + 1
                supabase.table("users").update({"credits": new_credits}).eq("user_id", invited_by).execute()
                bot.send_message(invited_by, "🎉 Arkadaşın katıldı! +1 Hak kazandın.")

    current_user = supabase.table("users").select("*").eq("user_id", user_id).execute()
    credits = current_user.data[0]['credits']
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    text = (
        f"✅ **BOT TÜM SİSTEMLER AKTİF!**\n\n"
        f"💎 **Mevcut Hakkın:** {credits}\n"
        f"🔗 **Referans Linkin:** `{ref_link}`\n\n"
        f"🎬 **Kullanılabilir Komutlar:**\n"
        f"/netflix | /spotify | /hbomax\n"
        f"/exxen | /predunyam"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# --- GENEL HESAP VERME MANTIĞI ---
def process_request(message, file_name, service_name):
    user_id = message.from_user.id
    user_info = supabase.table("users").select("credits").eq("user_id", user_id).execute()
    
    if user_info.data and user_info.data[0]['credits'] > 0:
        account = get_account_from_file(file_name)
        if account:
            new_credits = user_info.data[0]['credits'] - 1
            supabase.table("users").update({"credits": new_credits}).eq("user_id", user_id).execute()
            bot.send_message(message.chat.id, f"🚀 **İşte {service_name} Hesabın:**\n\n`{account}`\n\nKalan Hakkın: **{new_credits}**", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"⚠️ Üzgünüm, {service_name} stokları şu an boş.")
    else:
        bot.send_message(message.chat.id, "⚠️ Hakkın bitmiş! Ref linkinle arkadaş davet et.")

# --- TÜM KOMUTLAR ---
@bot.message_handler(commands=['netflix'])
def netflix(message): process_request(message, "Netflix.txt", "Netflix")

@bot.message_handler(commands=['spotify'])
def spotify(message): process_request(message, "Spotify.txt", "Spotify")

@bot.message_handler(commands=['hbomax'])
def hbomax(message): process_request(message, "Hbomax.txt", "HBO Max")

@bot.message_handler(commands=['exxen'])
def exxen(message): process_request(message, "Exxen.txt", "Exxen")

@bot.message_handler(commands=['predunyam'])
def predunyam(message): process_request(message, "Predunyam.txt", "Premium Dünyam")

# --- BOTU BAŞLAT ---
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
