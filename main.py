import os
from flask import Flask, request
import telebot

# Ambil token dan webhook URL dari environment (Railway)
TOKEN = os.environ.get("TOKEN")  # Sudah kamu simpan di Environment Railway
WEBHOOK_URL = "https://conspindo-recruit-bot-production.up.railway.app"  # Alamat Railway kamu

# Inisialisasi Flask dan Bot
app = Flask(__name__)
bot = telebot.TeleBot(TOKEN)

# ==========================
# PESAN AWAL & INFORMASI BOT
# ==========================

@bot.message_handler(commands=['start', 'info'])
def send_welcome(message):
    text = (
        "👋 *Selamat datang di Program Rekrutmen ConsPIndo (Sesi 2)*\n\n"
        "Silakan isi Formulir Pendaftaran langsung di chat ini.\n"
        "_Jawablah pertanyaan dengan jujur dan lengkap._\n\n"
        "Ketik */daftar* untuk memulai proses pendaftaran."
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ==========================
# PROSES FORMULIR PENDAFTARAN
# ==========================

user_data = {}

@bot.message_handler(commands=['daftar'])
def start_registration(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    bot.send_message(chat_id, "🧾 Silakan masukkan *Nama Lengkap Anda*:", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_name)

def process_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['nama'] = message.text
    bot.send_message(chat_id, "📧 Masukkan *Alamat Email Aktif* Anda:", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_email)

def process_email(message):
    chat_id = message.chat.id
    user_data[chat_id]['email'] = message.text
    bot.send_message(chat_id, "📱 Masukkan *Nomor WhatsApp aktif* Anda:", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_whatsapp)

def process_whatsapp(message):
    chat_id = message.chat.id
    user_data[chat_id]['whatsapp'] = message.text
    bot.send_message(chat_id, "🏙️ Masukkan *Domisili / Kota Tinggal* Anda:", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_city)

def process_city(message):
    chat_id = message.chat.id
    user_data[chat_id]['domisili'] = message.text
    bot.send_message(chat_id, "🎓 Masukkan *Latar belakang pendidikan terakhir Anda*:", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_education)

def process_education(message):
    chat_id = message.chat.id
    user_data[chat_id]['pendidikan'] = message.text
    bot.send_message(chat_id, "💼 Masukkan *Bidang keahlian atau minat utama Anda*:", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_field)

def process_field(message):
    chat_id = message.chat.id
    user_data[chat_id]['keahlian'] = message.text
    bot.send_message(chat_id, "🕐 Sudah berapa lama Anda memiliki pengalaman kerja di bidang tersebut?", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_experience)

def process_experience(message):
    chat_id = message.chat.id
    user_data[chat_id]['pengalaman'] = message.text
    bot.send_message(chat_id, "📎 Silakan kirim *Foto KTP / ID Card* Anda (dalam ukuran wajar):")
    bot.register_next_step_handler(message, process_ktp)

def process_ktp(message):
    chat_id = message.chat.id
    if not message.photo:
        bot.send_message(chat_id, "⚠️ Kirimkan sebagai *foto*, bukan teks. Coba lagi.")
        bot.register_next_step_handler(message, process_ktp)
        return
    file_id = message.photo[-1].file_id
    user_data[chat_id]['ktp'] = file_id
    bot.send_message(chat_id, "📸 Sekarang kirim *Pas Foto Anda (proporsional dan jelas)*:")
    bot.register_next_step_handler(message, process_pasfoto)

def process_pasfoto(message):
    chat_id = message.chat.id
    if not message.photo:
        bot.send_message(chat_id, "⚠️ Kirimkan sebagai *foto*, bukan teks. Coba lagi.")
        bot.register_next_step_handler(message, process_pasfoto)
        return
    file_id = message.photo[-1].file_id
    user_data[chat_id]['pasfoto'] = file_id

    data = user_data[chat_id]
    summary = (
        f"✅ *Data Pendaftaran Anda*\n\n"
        f"👤 Nama: {data['nama']}\n"
        f"📧 Email: {data['email']}\n"
        f"📱 WhatsApp: {data['whatsapp']}\n"
        f"🏙️ Domisili: {data['domisili']}\n"
        f"🎓 Pendidikan: {data['pendidikan']}\n"
        f"💼 Keahlian: {data['keahlian']}\n"
        f"🕐 Pengalaman: {data['pengalaman']}\n\n"
        "_Tim Rekrutmen ConsPIndo akan melakukan verifikasi data Anda._"
    )

    bot.send_message(chat_id, summary, parse_mode='Markdown')

    # Kirim juga ke admin (bisa ubah ID admin)
    GROUP_CHAT_ID = -1002955347210  # ID grup Data_Recruitment
bot.send_message(GROUP_CHAT_ID, f"📋 *Data Pendaftar Baru:*\n\n{summary}", parse_mode='Markdown')
# ==========================
# WEBHOOK HANDLER UNTUK RAILWAY
# ==========================

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.before_first_request
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

@app.route('/', methods=['GET'])
def index():
    return "🤖 ConsPIndo Recruit Bot sedang aktif."

# Jalankan Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
