import telebot
from telebot import types
import os
import threading
from flask import Flask
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI (HAFIZA SİSTEMİ) ---
SUPABASE_URL = "https://xjtneisfuvxzjrntarze.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhqdG5laXNmdXZ4empybnRhcnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzODc1NTUsImV4cCI6MjA4Mzk2MzU1NX0.2HfFMOCywdJ4uUXeu_Vjf-Xf6v72WRxtUcIZPO63z4U"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- RENDER WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"
def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- BOT AYARLARI ---
TOKEN = '7990158345:AAGfUNFVw7dCiKOkTjb3UlobGxsADBNCW2w'
bot = telebot.TeleBot(TOKEN)

# --- KOMUTLAR ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()
    invited_by = None
    if len(args) > 1:
        try: invited_by = int(args[1])
        except: invited_by = None

    user_data = supabase.table("users").select("*").eq("user_id", user_id).execute()
    
    if not user_data.data:
        supabase.table("users").insert({"user_id": user_id, "credits": 5, "invited_by": invited_by}).execute()
        if invited_by and invited_by != user_id:
            inviter = supabase.table("users").select("credits").eq("user_id", invited_by).execute()
            if inviter.data:
                new_credits = inviter.data[0]['credits'] + 1
                supabase.table("users").update({"credits": new_credits}).eq("user_id", invited_by).execute()
                bot.send_message(invited_by, "🎉 Bir arkadaşın katıldı! +1 Hak kazandın.")
    
    current_user = supabase.table("users").select("*").eq("user_id", user_id).execute()
    credits = current_user.data[0]['credits']
    invites = supabase.table("users").select("user_id", count="exact").eq("invited_by", user_id).execute()
    invite_count = invites.count if invites.count is not None else 0

    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    
    welcome_text = (
        f"✅ **BOTUNA HOŞ GELDİN!** 🎉\n\n"
        f"💎 **Mevcut Hakkın:** {credits}\n"
        f"👥 **Toplam Davetin:** {invite_count}\n\n"
        f"🔗 **Referans Linkin:**\n`{ref_link}`\n\n"
        f"🔓 Hesap almak için: `/spotify` yazabilirsin!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

# --- SPOTIFY HESAP ATMA KOMUTU ---
@bot.message_handler(commands=['spotify'])
def send_accounts(message):
    user_id = message.from_user.id
    # Kullanıcının hakkını kontrol et
    user_info = supabase.table("users").select("credits").eq("user_id", user_id).execute()
    
    if user_info.data and user_info.data[0]['credits'] > 0:
        # 1 hak düşür
        new_credits = user_info.data[0]['credits'] - 1
        supabase.table("users").update({"credits": new_credits}).eq("user_id", user_id).execute()
        
        # BURAYA HESAPLARI YAZ
        hesaplar = (
            "🚀 **İşte Spotify Hesabın:**\n\n"
            "📧 e-Posta: `hesap1@gmail.com` \n"
            "🔑 Şifre: `sifre123` \n\n"
            f"Kalan Hakkın: **{new_credits}**"
        )
        bot.send_message(message.chat.id, hesaplar, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ Üzgünüm, hiç hakkın kalmamış! Referans linkinle arkadaş davet et.")

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    bot.remove_webhook()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
