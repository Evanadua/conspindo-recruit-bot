import telebot
from telebot import types

# === TOKEN BOT ANDA ===
TOKEN = "7771265241:AAG_dvqYh2WbbLnq49cs5xVxWAyHZIfuNkw"
bot = telebot.TeleBot(TOKEN)

# === GROUP PENAMPUNG HASIL ===
GROUP_CHAT_ID = -1002955347210  # @Data_Recruitment

# === DATA PERTANYAAN ===
questions = [
    "1️⃣ Nama Lengkap:",
    "2️⃣ Usia:",
    "3️⃣ Email:",
    "4️⃣ No. WhatsApp:",
    "5️⃣ Domisili (Kota/Provinsi):",
    "6️⃣ Bidang keahlian / pekerjaan saat ini:",
    "7️⃣ Alasan ingin bergabung dengan ConsPIndo:",
    "8️⃣ Harapan Anda ke depan setelah bergabung:"
]

# === PENYIMPANAN SEMENTARA ===
user_data = {}
user_step = {}

# ==========================================================
#  /INFO - Untuk di GRUP PUBLIK
# ==========================================================
@bot.message_handler(commands=['info'])
def kirim_info_rekrutmen(message):
    if message.chat.type in ['group', 'supergroup']:
        text = (
            "👋 *Selamat Datang di Program Rekrutmen ConsPIndo – Sesi 2*\n\n"
            "✨ Terima kasih telah bergabung bersama kami!\n\n"
            "Asisten kami siap membantu Anda mengisi *Formulir Pendaftaran* "
            "untuk posisi di *Pusat* maupun *Provinsi/Kota/Kabupaten.*\n\n"
            "📋 *Data yang diperlukan:*\n"
            "1️⃣ Nama Lengkap\n"
            "2️⃣ Usia\n"
            "3️⃣ Email\n"
            "4️⃣ No. WhatsApp\n"
            "5️⃣ Domisili (Kota/Provinsi)\n"
            "6️⃣ Bidang Keahlian / Pekerjaan\n"
            "7️⃣ Alasan Bergabung\n"
            "8️⃣ Harapan ke Depan\n"
            "9️⃣ Foto ID / KTP\n"
            "🔟 Pas Foto Formal\n\n"
            "🕓 *Semua data bersifat rahasia dan hanya untuk administrasi resmi ConsPIndo.*"
        )

        markup = types.InlineKeyboardMarkup()
        tombol = types.InlineKeyboardButton(
            "🔘 Mulai Isi Formulir Pendaftaran",
            url="https://t.me/ConsPIndoRecruitBot?start=apply"
        )
        markup.add(tombol)

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="Markdown",
            reply_markup=markup,
            disable_web_page_preview=True
        )
    else:
        bot.send_message(message.chat.id, "Perintah /info hanya digunakan di *grup publik*.", parse_mode="Markdown")


# ==========================================================
#  /START - Untuk di PRIVATE CHAT (chat pribadi)
# ==========================================================
@bot.message_handler(commands=['start'])
def start_private(message):
    if message.chat.type == 'private':
        welcome = (
            "👋 *Halo!* Saya *Asisten ConsPIndo*.\n\n"
            "Terima kasih telah bergabung dalam *Program Rekrutmen ConsPIndo – Sesi 2.*\n"
            "Saya akan membantu Anda mengisi formulir pendaftaran.\n\n"
            "Tekan tombol di bawah ini untuk memulai pengisian data."
        )
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📝 Mulai Isi Formulir"))
        bot.send_message(message.chat.id, welcome, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.reply_to(message, "Silakan gunakan perintah ini di *chat pribadi bot*.", parse_mode="Markdown")


# ==========================================================
#  MULAI PENGISIAN FORMULIR
# ==========================================================
@bot.message_handler(func=lambda msg: msg.text == "📝 Mulai Isi Formulir" and msg.chat.type == 'private')
def mulai_formulir(message):
    user_data[message.chat.id] = {}
    user_step[message.chat.id] = 0
    bot.send_message(message.chat.id, questions[0])


# ==========================================================
#  PROSES PERTANYAAN BERUNTUN
# ==========================================================
@bot.message_handler(func=lambda msg: msg.chat.id in user_step and user_step[msg.chat.id] < len(questions))
def tanya_berikutnya(message):
    step = user_step[message.chat.id]
    user_data[message.chat.id][questions[step]] = message.text

    if step + 1 < len(questions):
        user_step[message.chat.id] += 1
        bot.send_message(message.chat.id, questions[step + 1])
    else:
        user_step[message.chat.id] += 1
        bot.send_message(
            message.chat.id,
            "9️⃣ Silakan kirim *Foto ID / KTP* Anda (gambar harus jelas dan proporsional).",
            parse_mode="Markdown"
        )


# ==========================================================
#  TERIMA FOTO KTP & PAS FOTO
# ==========================================================
@bot.message_handler(content_types=['photo'])
def terima_foto(message):
    if message.chat.id not in user_step:
        return

    step = user_step[message.chat.id]

    # === FOTO ID ===
    if step == len(questions):
        user_data[message.chat.id]['Foto KTP'] = message.photo[-1].file_id
        user_step[message.chat.id] += 1
        bot.send_message(
            message.chat.id,
            "🔟 Sekarang kirim *Pas Foto Formal* Anda (ukuran standar, jelas, dan proporsional).",
            parse_mode="Markdown"
        )

    # === PAS FOTO ===
    elif step == len(questions) + 1:
        user_data[message.chat.id]['Pas Foto'] = message.photo[-1].file_id

        summary = "\n".join([
            f"{q} {a}" for q, a in user_data[message.chat.id].items() if q in questions
        ])

        # === KIRIM KE GRUP PENAMPUNG ===
        bot.send_message(GROUP_CHAT_ID, f"📋 *Data Rekrutmen Baru:*\n\n{summary}", parse_mode="Markdown")

        # Kirim kedua foto
        if 'Foto KTP' in user_data[message.chat.id]:
            bot.send_photo(GROUP_CHAT_ID, user_data[message.chat.id]['Foto KTP'], caption="🆔 Foto ID / KTP")
        if 'Pas Foto' in user_data[message.chat.id]:
            bot.send_photo(GROUP_CHAT_ID, user_data[message.chat.id]['Pas Foto'], caption="📸 Pas Foto Formal")

        # Konfirmasi ke user
        bot.send_message(
            message.chat.id,
            "✅ Terima kasih! Semua data dan foto Anda telah berhasil dikirim.\n\n"
            "Tim Rekrutmen ConsPIndo akan melakukan verifikasi secepatnya.",
            parse_mode="Markdown"
        )

        # Hapus data sementara
        del user_data[message.chat.id]
        del user_step[message.chat.id]


print("🤖 Asisten ConsPIndo sedang berjalan...")
bot.polling(non_stop=True)
