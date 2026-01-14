import telebot
from telebot import types
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
def home(): return "Bot Canlı!"
def run_flask(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))

# --- BOT ---
TOKEN = 'YENI_ALACAGIN_TOKENI_BURAYA_YAPISTIR'
bot = telebot.TeleBot(TOKEN)

def get_acc(file_name):
    try:
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines: return random.choice(lines).strip()
        return None
    except: return None

@bot.message_handler(commands=['start'])
def start(m):
    user_id = m.from_user.id
    # Kayıt işlemi
    user_data = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not user_data.data:
        supabase.table("users").insert({"user_id": user_id, "credits": 5}).execute()
    
    credits = supabase.table("users").select("credits").eq("user_id", user_id).execute().data[0]['credits']
    bot_info = bot.get_me()
    ref = f"https://t.me/{bot_info.username}?start={user_id}"
    
    bot.send_message(m.chat.id, f"✅ **BOT HAZIR!**\n\n💎 Hak: {credits}\n🔗 Ref: `{ref}`\n\nKomutlar: /netflix, /spotify, /exxen, /hbomax, /predunyam", parse_mode="Markdown")

def give_acc(m, file, service):
    user_id = m.from_user.id
    u = supabase.table("users").select("credits").eq("user_id", user_id).execute()
    if u.data and u.data[0]['credits'] > 0:
        acc = get_acc(file)
        if acc:
            new = u.data[0]['credits'] - 1
            supabase.table("users").update({"credits": new}).eq("user_id", user_id).execute()
            bot.send_message(m.chat.id, f"🚀 **{service} Hesabın:**\n`{acc}`\n\nKalan Hak: {new}", parse_mode="Markdown")
        else: bot.send_message(m.chat.id, "⚠️ Stok bitti!")
    else: bot.send_message(m.chat.id, "⚠️ Hak yok! Ref kas.")

@bot.message_handler(commands=['netflix'])
def n(m): give_acc(m, "Netflix.txt", "Netflix")
@bot.message_handler(commands=['spotify'])
def s(m): give_acc(m, "Spotify.txt", "Spotify")
@bot.message_handler(commands=['exxen'])
def e(m): give_acc(m, "Exxen.txt", "Exxen")
@bot.message_handler(commands=['hbomax'])
def h(m): give_acc(m, "Hbomax.txt", "HBO Max")
@bot.message_handler(commands=['predunyam'])
def p(m): give_acc(m, "Predunyam.txt", "Premium Dünyam")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
