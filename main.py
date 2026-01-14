import telebot
from telebot import types
import os, threading, random
from flask import Flask
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI (Hafıza İçin) ---
SUPABASE_URL = "https://xjtneisfuvxzjrntarze.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhqdG5laXNmdXZ4empybnRhcnplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgzODc1NTUsImV4cCI6MjA4Mzk2MzU1NX0.2HfFMOCywdJ4uUXeu_Vjf-Xf6v72WRxtUcIZPO63z4U"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- RENDER WEB SERVER (Uyanık Kalması İçin) ---
app = Flask('')
@app.route('/')
def home(): return "Bot Aktif!"
def run_flask(): 
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- BOT AYARLARI ---
TOKEN = '7990158345:AAGfUNFVw7dCiKOkTjb3UlobGxsADBNCW2w'
bot = telebot.TeleBot(TOKEN)

# --- TXT DOSYASINDAN HESAP ÇEKME ---
def get_acc(file_name):
    try:
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines: return random.choice(lines).strip()
        return None
    except: return None

# --- START KOMUTU ---
@bot.message_handler(commands=['start'])
def start(m):
    user_id = m.from_user.id
    args = m.text.split()
    invited_by = int(args[1]) if len(args) > 1 and args[1].isdigit() else None

    # Kayıt ve Referans İşlemi
    u = supabase.table("users").select("*").eq("user_id", user_id).execute()
    if not u.data:
        supabase.table("users").insert({"user_id": user_id, "credits": 5, "invited_by": invited_by}).execute()
        if invited_by and invited_by != user_id:
            inv_data = supabase.table("users").select("credits").eq("user_id", invited_by).execute()
            if inv_data.data:
                new_c = inv_data.data[0]['credits'] + 1
                supabase.table("users").update({"credits": new_c}).eq("user_id", invited_by).execute()
                bot.send_message(invited_by, "🎉 Arkadaşın katıldı! +1 Hak kazandın.")

    res = supabase.table("users").select("credits").eq("user_id", user_id).execute()
    credits = res.data[0]['credits']
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    
    bot.send_message(m.chat.id, f"✅ **BOT AKTİF!**\n\n💎 **Hakkın:** {credits}\n🔗 **Referans Linkin:** `{ref_link}`\n\n**Komutlar:**\n/netflix, /spotify, /exxen, /hbomax, /predunyam", parse_mode="Markdown")

# --- HESAP VERME MANTIĞI ---
def process_req(m, file, service):
    user_id = m.from_user.id
    u = supabase.table("users").select("credits").eq("user_id", user_id).execute()
    if u.data and u.data[0]['credits'] > 0:
        acc = get_acc(file)
        if acc:
            new_c = u.data[0]['credits'] - 1
            supabase.table("users").update({"credits": new_c}).eq("user_id", user_id).execute()
            bot.send_message(m.chat.id, f"🚀 **{service} Hesabın:**\n`{acc}`\n\nKalan Hak: **{new_c}**", parse_mode="Markdown")
        else: bot.send_message(m.chat.id, "⚠️ Stok bitti!")
    else: bot.send_message(m.chat.id, "⚠️ Hak yok! Arkadaş davet et.")

@bot.message_handler(commands=['netflix'])
def net(m): process_req(m, "Netflix.txt", "Netflix")
@bot.message_handler(commands=['spotify'])
def spo(m): process_req(m, "Spotify.txt", "Spotify")
@bot.message_handler(commands=['exxen'])
def exx(m): process_req(m, "Exxen.txt", "Exxen")
@bot.message_handler(commands=['hbomax'])
def hbo(m): process_req(m, "Hbomax.txt", "HBO Max")
@bot.message_handler(commands=['predunyam'])
def pre(m): process_req(m, "Predunyam.txt", "Premium Dünyam")

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
