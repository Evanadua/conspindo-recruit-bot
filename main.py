from dotenv import load_dotenv
import os
import telebot
from telebot import types
from flask import Flask, request

# ===============================
# 🔧 LOAD .ENV & KONFIGURASI DASAR
# ===============================
load_dotenv()

TOKEN = os.environ.get("TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://conspindo-recruit-bot-production.up.railway.app")
PORT = int(os.environ.get("PORT", 5000))

if not TOKEN:
    raise RuntimeError("⚠️ Environment variable TOKEN belum di-set!")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ===============================
# 🧩 KONFIGURASI GRUP & ADMIN
# ===============================
GROUP_ADMIN_ID = -1002955347210   # Grup hasil form (Data_Recruitment)
ADMIN_PERSONAL_ID = 2007605734    # Admin pribadi
GROUP_PUBLIC_IDS = [              # Grup publik penerima /info
    -1002955347210,               # Group 1
    -1002061458573,               # Group 2
    -1009876543210                # Group 3
]
ALLOWED_ADMINS = [
    2007605734, 1062490743, 1159933604, 7552115568, 5632143594, 5818417700
]

# ===============================
# 🗂 DATA PENGGUNA
# ===============================
user_data = {}
questions = [
    "1️⃣ Nama Lengkap:",
    "2️⃣ Nomor WhatsApp Aktif:",
    "3️⃣ Email:",
    "4️⃣ Domisili (Kota/Kabupaten/Provinsi):",
    "5️⃣ Jabatan yang diminati:",
    "6️⃣ Bidang Keahlian / Potensi:",
    "7️⃣ Pengalaman Organisasi / Profesi:",
    "8️⃣ Alasan ingin bergabung dengan ConsPIndo:"
]

# ===============================
# ⚙️ MODE OTOMATIS: Railway / Local
# ===============================
RUN_MODE = "WEBHOOK" if os.environ.get("RAILWAY_ENVIRONMENT") else "LOCAL"
print(f"🚀 Bot berjalan dalam mode: {RUN_MODE}")

# ===============================
# 🏁 COMMAND /START
# ===============================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "Silakan buka chat pribadi dengan Asisten kami untuk mengisi formulir.")
        return
    bot.send_message(message.chat.id,
        "👋 Halo! Ini *Asisten Rekrutmen ConsPIndo*.\n\nKetik *Mulai* untuk memulai pengisian formulir.",
        parse_mode="Markdown"
    )

# ===============================
# 🧾 PROSES FORM REKRUTMEN
# ===============================
@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.text and m.text.strip().lower() == 'mulai')
def mulai_form(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'answers': [], 'ktp_file_id': None, 'pas_file_id': None}
    bot.send_message(chat_id, questions[0])
    bot.register_next_step_handler(message, handle_answer, 0)

def handle_answer(message, index):
    chat_id = message.chat.id
    text = message.text or ""
    user_data.setdefault(chat_id, {'answers': [], 'ktp_file_id': None, 'pas_file_id': None})
    user_data[chat_id]['answers'].append(text)

    next_index = index + 1
    if next_index < len(questions):
        bot.send_message(chat_id, questions[next_index])
        bot.register_next_step_handler(message, handle_answer, next_index)
    else:
        bot.send_message(chat_id, "9️⃣ Kirim *Foto KTP* Anda (format JPG/PNG).", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_ktp)

def handle_ktp(message):
    chat_id = message.chat.id
    if not message.photo:
        bot.send_message(chat_id, "Kirim dalam bentuk *foto* (bukan file). Coba lagi.", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_ktp)
        return
    user_data[chat_id]['ktp_file_id'] = message.photo[-1].file_id
    bot.send_message(chat_id, "🔟 Sekarang kirim *Pas Foto Formal* Anda (format JPG/PNG).", parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_pasfoto)

def handle_pasfoto(message):
    chat_id = message.chat.id
    if not message.photo:
        bot.send_message(chat_id, "Kirim dalam bentuk *foto* (bukan file). Coba lagi.", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_pasfoto)
        return
    user_data[chat_id]['pas_file_id'] = message.photo[-1].file_id
    send_summary(chat_id)

def send_summary(chat_id):
    data = user_data.get(chat_id)
    if not data:
        bot.send_message(chat_id, "⚠️ Sesi tidak ditemukan. Ketik *Mulai* untuk ulang.", parse_mode="Markdown")
        return

    answers = data['answers']
    while len(answers) < len(questions):
        answers.append("—")

    summary = "📋 *Data Rekrutmen Baru:*\n\n" + "\n".join(
        f"{questions[i]} {answers[i]}" for i in range(len(questions))
    )
    sender = f"\n\n🕓 Dikirim oleh: @{(bot.get_chat(chat_id).username or 'TanpaUsername')}"

    bot.send_message(GROUP_ADMIN_ID, summary + sender, parse_mode="Markdown")
    bot.send_message(ADMIN_PERSONAL_ID, summary + sender, parse_mode="Markdown")

    if data['ktp_file_id']:
        bot.send_photo(GROUP_ADMIN_ID, data['ktp_file_id'], caption=f"🪪 KTP — {answers[0]}")
        bot.send_photo(ADMIN_PERSONAL_ID, data['ktp_file_id'], caption=f"🪪 KTP — {answers[0]}")
    if data['pas_file_id']:
        bot.send_photo(GROUP_ADMIN_ID, data['pas_file_id'], caption=f"📸 Pas Foto — {answers[0]}")
        bot.send_photo(ADMIN_PERSONAL_ID, data['pas_file_id'], caption=f"📸 Pas Foto — {answers[0]}")

    bot.send_message(chat_id, "✅ Terima kasih! Data Anda sudah dikirim ke tim rekrutmen.", parse_mode="Markdown")
    user_data.pop(chat_id, None)

# ===============================
# 📢 /INFO UNTUK ADMIN
# ===============================
@bot.message_handler(commands=['info', 'broadcast'])
def cmd_broadcast(message):
    if message.from_user.id not in ALLOWED_ADMINS:
        bot.reply_to(message, "❌ Anda tidak diizinkan menggunakan perintah ini.")
        return

    info_text = (
        "👋 *Selamat Datang di Rekrutmen ConsPIndo – Sesi 2*\n\n"
        "Asisten kami akan membantu Anda mengisi *Formulir Pendaftaran* di chat pribadi.\n\n"
        "📋 *Data yang perlu disiapkan:*\n"
        "1️⃣ Nama Lengkap\n2️⃣ Nomor WhatsApp Aktif\n3️⃣ Email\n4️⃣ Domisili\n"
        "5️⃣ Jabatan yang diminati\n6️⃣ Bidang Keahlian\n7️⃣ Pengalaman Organisasi\n"
        "8️⃣ Alasan Bergabung\n9️⃣ Foto KTP\n🔟 Pas Foto Formal\n\n"
        "Klik tombol di bawah untuk mulai mengisi form di private chat."
    )
    username = bot.get_me().username
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📝 Mulai Isi Formulir", url=f"https://t.me/{username}?start=apply"))

    sent_to = 0
    for gid in GROUP_PUBLIC_IDS:
        try:
            bot.send_message(gid, info_text, parse_mode="Markdown", reply_markup=markup)
            sent_to += 1
        except Exception as e:
            print(f"Gagal kirim ke {gid}: {e}")

    bot.reply_to(message, f"✅ Pesan info dikirim ke {sent_to} grup publik.")

# ===============================
# 🌐 WEBHOOK & POLLING HANDLER
# ===============================
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook_receiver():
    update = telebot.types.Update.de_json(request.get_data(as_text=True))
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "🤖 ConsPIndo Recruit Bot aktif."

# ===============================
# 🚀 MODE OTOMATIS: WEBHOOK / POLLING
# ===============================
import time

if __name__ == "__main__":
    if RUN_MODE == "WEBHOOK":
        print("🌐 Mode Railway terdeteksi — menjalankan Webhook...")
        bot.remove_webhook()
        bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
        app.run(host="0.0.0.0", port=PORT)

    else:
        print("💻 Mode lokal — menjalankan Polling dengan auto-reconnect...")
        bot.remove_webhook()

        while True:
            try:
                bot.infinity_polling(timeout=60, long_polling_timeout=60, skip_pending=True)
            except Exception as e:
                print(f"⚠️ Terjadi error koneksi: {e}")
                print("🔁 Mencoba menghubungkan ulang dalam 5 detik...")
                time.sleep(5)
