class MessageTemplates:
    """Centralized message templates"""

    START = """🤖 *Telegram AI Bot*

Halo! Saya AI assistant powered by Groq.

*Cara Pakai:*
• *Private Chat:* Langsung chat aja!
• *Group Chat:* Mention saya @{bot_username} atau reply chat saya

*Commands:*
/start - Info bot
/help - Bantuan
/clear - Reset percakapan
/stats - Statistik (admin only)

💡 Powered by Llama 3.3 70B"""

    HELP = """📚 *Bantuan*

*Contoh Tanya:*
• "Jelaskan apa itu AI"
• "Hitung 15% dari 500000"
• "Tips nabung yang efektif"
• "Buatkan cerita pendek"

Bot akan ingat percakapan sebelumnya!

*Commands:*
/start - Info
/help - Bantuan
/clear - Reset chat
/stats - Statistics (admin)"""

    PHOTO_NOT_SUPPORTED = """📷 Terima kasih sudah kirim foto!

🚧 Maaf, fitur analisis gambar **belum tersedia** saat ini.

Untuk saat ini, saya hanya bisa membantu dengan:
✅ Chat text
✅ Menjawab pertanyaan
✅ Analisis & diskusi

Silakan tanya dalam bentuk text ya! 😊"""

    STATS = """📊 *Bot Statistics*

👥 Total Chats: {total_chats}
💬 Total Messages: {total_messages}
✅ Active Chats: {active_chats}
🤖 AI Model: {ai_model}
⏱️ Rate Limit: {rate_limit}s/{max_req}req/min"""

    # Error messages
    RATE_LIMIT_GROQ = "⏳ Groq API sedang sibuk. Tunggu sebentar ya..."
    RATE_LIMIT_USER = "⏱️ Terlalu cepat! Tunggu {seconds} detik lagi."
    RATE_LIMIT_MINUTE = "⏱️ Terlalu banyak request! Max {max_requests}/menit."
    NETWORK_ERROR = "🌐 Network error. Coba lagi ya!"
    TIMEOUT_ERROR = "⏰ Request timeout. Pertanyaan terlalu kompleks?"
    API_KEY_ERROR = "🔑 API key error. Check configuration!"
    GENERAL_ERROR = "❌ Maaf, ada error: {error}"
    ADMIN_ONLY = "❌ Command ini hanya untuk admin."
    HISTORY_CLEARED = "✅ Percakapan telah direset!"
