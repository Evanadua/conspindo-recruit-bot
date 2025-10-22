import os
from flask import Flask, request
import telebot
from telebot import types

# ----- KONFIGURASI (gunakan ENV di Railway) -----
TOKEN = os.environ.get("TOKEN")  # PENTING: gunakan variabel ENV bernama TOKEN
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://conspindo-recruit-bot-production.up.railway.app")
GROUP_CHAT_ID = -1002955347210  # ID grup Data_Recruitment (tetap)

if not TOKEN:
    raise RuntimeError("Environment variable TOKEN belum di-set. Isi TOKEN di Railway Variables.")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ----- Storage sementara untuk sesi user -----
# Struktur: user_data[chat_id] = { 'answers': [ans1..ans8], 'ktp_file_id':..., 'pas_file_id':... }
user_data = {}

# Daftar 8 pertanyaan (tetap)
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

# ---------------------
# /info  -> untuk dikirim di GROUP PUBLIK
# tombol akan mengarahkan ke username bot yang sebenarnya (menghindari username not found)
# ---------------------
@bot.message_handler(commands=['info'])
def cmd_info(message):
    # ambil username bot yang sesuai token (runtime)
    me = bot.get_me()
    username = me.username or ""
    tme_link = f"https://t.me/{username}?start=apply" if username else ""

    info_text = (
        "👋 *Selamat Datang di Rekrutmen ConsPIndo – Sesi 2*\n\n"
        "Asisten kami akan membantu Anda mengisi *Formulir Pendaftaran* secara private (chat pribadi).\n\n"
        "📋 *Data yang perlu disiapkan:*\n"
        "1️⃣ Nama Lengkap\n"
        "2️⃣ Nomor WhatsApp Aktif\n"
        "3️⃣ Email\n"
        "4️⃣ Domisili (Kota/Kabupaten/Provinsi)\n"
        "5️⃣ Jabatan yang diminati\n"
        "6️⃣ Bidang Keahlian / Potensi\n"
        "7️⃣ Pengalaman Organisasi / Profesi\n"
        "8️⃣ Alasan ingin bergabung dengan ConsPIndo\n"
        "9️⃣ Foto ID / KTP (jelas)\n"
        "🔟 Pas Foto Formal (proporsional)\n\n"
        "Klik tombol di bawah untuk membuka chat privat dengan Asisten kami dan mulai mengisi."
    )

    markup = types.InlineKeyboardMarkup()
    if tme_link:
        btn = types.InlineKeyboardButton("📝 Mulai Isi Formulir (Private Chat)", url=tme_link)
        markup.add(btn)
    else:
        markup.add(types.InlineKeyboardButton("📝 Mulai Isi Formulir", callback_data="start_private"))

    bot.send_message(message.chat.id, info_text, parse_mode="Markdown", reply_markup=markup)

# ---------------------
# /start handler -> jika di private
# ---------------------
@bot.message_handler(commands=['start'])
def cmd_start(message):
    # jika dari group, informasikan user untuk buka chat private
    if message.chat.type != 'private':
        bot.reply_to(message, "Untuk mendaftar, silakan klik tombol pengumuman dan lanjutkan di *chat pribadi* dengan Asisten kami.", parse_mode="Markdown")
        return

    # Kalau private, mulai proses
    bot.send_message(message.chat.id, "👋 Halo! Ini *Asisten ConsPIndo*.\nKetik *Mulai* untuk memulai pengisian formulir (1 per 1).", parse_mode="Markdown")

# Tombol/teks Mulai
@bot.message_handler(func=lambda m: m.chat.type == 'private' and m.text and m.text.strip().lower() == 'mulai')
def start_private_flow(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'answers': [], 'ktp_file_id': None, 'pas_file_id': None}
    # tanya pertanyaan pertama
    bot.send_message(chat_id, questions[0])
    bot.register_next_step_handler(message, handle_answer, 0)

# fungsi penangan jawaban teks; index = indeks pertanyaan saat ini
def handle_answer(message, index):
    chat_id = message.chat.id
    text = message.text or ""
    # simpan jawaban
    user_data.setdefault(chat_id, {'answers': [], 'ktp_file_id': None, 'pas_file_id': None})
    user_data[chat_id]['answers'].append(text)

    next_index = index + 1
    if next_index < len(questions):
        # tanya pertanyaan berikutnya
        bot.send_message(chat_id, questions[next_index])
        bot.register_next_step_handler(message, handle_answer, next_index)
    else:
        # semua 8 jawaban selesai -> minta foto KTP (poin 9)
        bot.send_message(chat_id, "9️⃣ Silakan kirim *Foto ID/KTP* Anda (foto jelas dan proporsional).", parse_mode="Markdown")
        bot.register_next_step_handler(message, handle_ktp_photo)

# terima foto KTP
def handle_ktp_photo(message):
    chat_id = message.chat.id
    if not message.photo:
        bot.send_message(chat_id, "Mohon kirim foto KTP dalam bentuk *foto* (jpg/png). Coba lagi.")
        bot.register_next_step_handler(message, handle_ktp_photo)
        return
    file_id = message.photo[-1].file_id
    user_data[chat_id]['ktp_file_id'] = file_id

    # minta pas foto (poin 10)
    bot.send_message(chat_id, "🔟 Sekarang kirim *Pas Foto Formal* Anda (latar netral, proporsional).", parse_mode="Markdown")
    bot.register_next_step_handler(message, handle_pasfoto_photo)

# terima pas foto
def handle_pasfoto_photo(message):
    chat_id = message.chat.id
    if not message.photo:
        bot.send_message(chat_id, "Mohon kirim pas foto dalam bentuk *foto* (jpg/png). Coba lagi.")
        bot.register_next_step_handler(message, handle_pasfoto_photo)
        return
    file_id = message.photo[-1].file_id
    user_data[chat_id]['pas_file_id'] = file_id

    # susun ringkasan dan kirim ke group + konfirmasi ke user
    send_summary_and_media(chat_id)

def send_summary_and_media(chat_id):
    data = user_data.get(chat_id)
    if not data:
        bot.send_message(chat_id, "Terjadi kesalahan: sesi tidak ditemukan. Silakan mulai ulang dengan mengetik 'Mulai'.")
        return

    answers = data['answers']
    # pastikan length 8 (safety)
    while len(answers) < 8:
        answers.append("—")

    summary_lines = [f"{questions[i]} {answers[i]}" for i in range(8)]
    summary_text = "📋 *Data Rekrutmen Baru:*\n\n" + "\n".join(summary_lines) + f"\n\n🕓 Dikirim oleh: @{(bot.get_chat(chat_id).username or 'TanpaUsername')}"
    
    # kirim ringkasan teks ke group
    bot.send_message(GROUP_CHAT_ID, summary_text, parse_mode="Markdown")

    # kirim foto KTP & Pas Foto ke group jika ada
    if data.get('ktp_file_id'):
        bot.send_photo(GROUP_CHAT_ID, data['ktp_file_id'], caption=f"🪪 KTP — {answers[0]}")
    if data.get('pas_file_id'):
        bot.send_photo(GROUP_CHAT_ID, data['pas_file_id'], caption=f"📸 Pas Foto — {answers[0]}")

    # konfirmasi ke user
    bot.send_message(chat_id, "✅ Terima kasih! Semua data dan foto Anda telah diterima. Tim Rekrutmen akan meninjau segera.", parse_mode="Markdown")

    # hapus sesi user
    user_data.pop(chat_id, None)

# -------------------------
# Webhook route / set webhook
# -------------------------
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook_receiver():
    json_str = request.get_data(as_text=True)
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.before_first_request
def setup_webhook():
    # set webhook ke WEBHOOK_URL/TOKEN
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

@app.route('/', methods=['GET'])
def index():
    return "🤖 ConsPIndo Recruit Bot (webhook) aktif."

# Jalankan Flask (Railway menyediakan PORT)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
