import telebot
from telebot import types
import os
import sqlite3
import re
from datetime import datetime, timedelta

# --- AYARLAR ---
TOKEN = '7990158345:AAHr9KWLdZZXaSeSmAbMpQO2bUcK7zY1UyQ'
bot = telebot.TeleBot(TOKEN)

# Kanallar
ZORUNLU_KANALLAR = ["@Kampanyavebilgi", "@Dosyakanal1", "@kampanyachat"]

# --- VERİTABANI ---
def db_setup():
    conn = sqlite3.connect("veritabani.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (uid INTEGER PRIMARY KEY, hak INTEGER, davet INTEGER, ad TEXT, ref_by INTEGER, last_daily TEXT)''')
    conn.commit()
    conn.close()

def get_user(uid):
    conn = sqlite3.connect("veritabani.db")
    c = conn.cursor()
    c.execute("SELECT hak, davet, ref_by, last_daily FROM users WHERE uid = ?", (uid,))
    res = c.fetchone()
    conn.close()
    return res

def add_user(uid, ad, ref_id=None):
    if not get_user(uid):
        conn = sqlite3.connect("veritabani.db")
        c = conn.cursor()
        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (uid, 5, 0, ad, ref_id, simdi))
        conn.commit()
        conn.close()

def update_val(uid, hak_artisi=0, davet_artisi=0, ref_temizle=False, yeni_hak=None):
    conn = sqlite3.connect("veritabani.db")
    c = conn.cursor()
    if yeni_hak is not None:
        simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE users SET hak = ?, last_daily = ? WHERE uid = ?", (yeni_hak, simdi, uid))
    else:
        c.execute("UPDATE users SET hak = hak + ?, davet = davet + ? WHERE uid = ?", (hak_artisi, davet_artisi, uid))
    if ref_temizle:
        c.execute("UPDATE users SET ref_by = NULL WHERE uid = ?", (uid,))
    conn.commit()
    conn.close()

def check_daily_reset(uid):
    user = get_user(uid)
    if not user: return
    last_time = datetime.strptime(user[3], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > last_time + timedelta(hours=24):
        update_val(uid, yeni_hak=5)

def get_account_safe(platform):
    file_path = f"{platform}.txt"
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+:[^\s]+", content)
        if not match: return None
        account = match.group(0)
        new_content = content.replace(account, "", 1)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return account
    except: return None

def check_sub(user_id):
    for kanal in ZORUNLU_KANALLAR:
        try:
            status = bot.get_chat_member(kanal, user_id).status
            if status not in ['member', 'administrator', 'creator']: return False
        except: return False
    return True

# --- KOMUTLAR ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    ad = message.from_user.first_name or "Kullanıcı"
    params = message.text.split()
    if not get_user(uid):
        ref_id = int(params[1]) if len(params) > 1 and params[1].isdigit() else None
        add_user(uid, ad, ref_id if ref_id != uid else None)
    else:
        check_daily_reset(uid)

    if not check_sub(uid):
        markup = types.InlineKeyboardMarkup()
        for i, k in enumerate(ZORUNLU_KANALLAR, 1):
            markup.add(types.InlineKeyboardButton(f"Kanal {i}'e Katıl", url=f"https://t.me/{k[1:]}"))
        markup.add(types.InlineKeyboardButton("✅ Katıldım", callback_data="check_sub"))
        bot.send_message(message.chat.id, "❌ Önce kanallara katılmalısın!", reply_markup=markup)
    else:
        ana_menu(message)

def ana_menu(message):
    uid = message.from_user.id
    check_daily_reset(uid)
    u = get_user(uid)
    msg = (
        "✅ BOTUNA HOŞ GELDİN! 🎉\n\n"
        "Hesap alabilmek için gerekli şartları yerine getirdin!\n"
        "1. Kanallara abone oldun. (Yaptın!)\n"
        "2. İlk hesap hakkın BEDAVA!! Hemen /market'ten seç.\n"
        "3. Her kişi başına hak kazan.\n\n"
        f"💎 Mevcut Hakkın: **{u[0]}**\n"
        f"👥 Toplam Davetin: **{u[1]}**"
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("/market", "/referansim", "/fakeno")
    bot.send_message(message.chat.id, msg, reply_markup=markup)

@bot.message_handler(commands=['market'])
def market_sec(message):
    if not check_sub(message.from_user.id): return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Exxen", callback_data="g_exxen"), types.InlineKeyboardButton("Netflix", callback_data="g_netflix"))
    markup.add(types.InlineKeyboardButton("Disney+", callback_data="g_disney"), types.InlineKeyboardButton("HBO Max", callback_data="g_hbomax"))
    markup.add(types.InlineKeyboardButton("PreDünyam", callback_data="g_predunyam"))
    bot.send_message(message.chat.id, "👇 Kategori seç:", reply_markup=markup)

@bot.message_handler(commands=['referansim'])
def referans(message):
    uid = message.from_user.id
    u = get_user(uid)
    link = f"https://t.me/{bot.get_me().username}?start={uid}"
    bot.send_message(message.chat.id, f"🔗 **Davet Linkin:** `{link}`\n\n✅ Onaylı davet başına +1 hak gelir.")

@bot.message_handler(commands=['fakeno'])
def fakeno(message):
    bot.send_message(message.chat.id, "📢 **Duyuru:** Fake numara yöntemi yakında eklenecektir!")

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    uid = call.from_user.id
    if call.data == "check_sub":
        if check_sub(uid):
            user_data = get_user(uid)
            if user_data and user_data[2]:
                ref_owner = user_data[2]
                update_val(ref_owner, hak_artisi=1, davet_artisi=1)
                update_val(uid, ref_temizle=True)
                bot.send_message(ref_owner, "✅ Arkadaşın kanallara katıldı! +1 Hak eklendi.")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            ana_menu(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Eksik kanal var!", show_alert=True)
    elif call.data.startswith("g_"):
        check_daily_reset(uid)
        user = get_user(uid)
        if user[0] <= 0:
            bot.answer_callback_query(call.id, "❌ Hakkın bitti!", show_alert=True)
            return
        plat = call.data.split("_")[1]
        acc = get_account_safe(plat)
        if acc:
            update_val(uid, hak_artisi=-1)
            bot.send_message(call.message.chat.id, f"✅ **{plat.upper()} Hesabın:**\n\n`{acc}`")
        else:
            bot.answer_callback_query(call.id, "😔 Stok bitti!", show_alert=True)

if __name__ == "__main__":
    db_setup()
    bot.infinity_polling()
