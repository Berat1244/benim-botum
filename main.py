import telebot
import os, threading, random
from flask import Flask
from supabase import create_client, Client

# --- SUPABASE ---
SUPABASE_URL = "https://xjtneisfuvxzjrntarze.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhqdG5laXNmdXZ4empybnRhcnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzODc1NTUsImV4cCI6MjA4Mzk2MzU1NX0.2HfFMOCywdJ4uUXeu_Vjf-Xf6v72WRxtUcIZPO63z4U"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "BOT CALISIYOR!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))

# --- BOT ---
TOKEN = '8122282591:AAFLcVGOtv48TaFRrIPcU8Dg0n3DCwSICnY'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ BOT CALISIYOR! Haklarını kontrol ediyorum...")
    user_id = m.from_user.id
    # Kayıt kontrol
    u = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not u.data:
        supabase.table("users").insert({"user_id": user_id, "credits": 5}).execute()
    bot.send_message(m.chat.id, "Hesap almak için: /netflix, /spotify, /exxen")

@bot.message_handler(commands=['netflix', 'spotify', 'exxen', 'hbomax', 'predunyam'])
def give_acc(m):
    bot.reply_to(m, "Stoklar kontrol ediliyor, lütfen bekle...")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    print("--- BOT MOTORU CALISTI ---")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
