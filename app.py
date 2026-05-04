import streamlit as st
import feedparser
import requests
import time
import re
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = "8571059270:AAGV-6nd5FrfXLxCr_GtDtKHEkceeR3HjJ4"
CHAT_ID = "1464769031"

FEEDS = {
    "CNBC Market": "https://www.cnbcindonesia.com/market/rss",
    "Kontan Saham": "https://www.kontan.co.id/rss/saham",
    "Bisnis News": "https://www.bisnis.com/rss/indeks"
}

# Tampilan di Website Streamlit
st.set_page_config(page_title="Provanch Intelligence", page_icon="📈")
st.title("🚀 Provanch News Intelligence")
st.write("Sistem sedang memantau market dan mengirim notif ke Telegram Rifky.")

def clean_html(text):
    return re.sub(re.compile('<.*?>'), '', text)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# Gunakan tombol buat memicu pengecekan di web
if st.button('Cek Berita Sekarang'):
    st.info("Sedang mengecek sumber berita...")
    for source_name, url in FEEDS.items():
        feed = feedparser.parse(url)
        if feed.entries:
            entry = feed.entries[0]
            title = entry.title
            st.success(f"Berita Terbaru dari {source_name} ditemukan!")
            st.write(f"**{title}**")
            
            # Kirim ke Telegram juga
            msg = f"🆕 *CEK MANUAL: {source_name}*\n\n📍 {title}\n\n🔗 [Link]({entry.link})"
            send_telegram(msg)
else:
    st.write("Klik tombol di atas untuk tes manual atau biarkan bot jalan otomatis.")

# Bagian Auto-Loop (Hanya jika dijalankan di server)
# Catatan: Di Streamlit Cloud, while True bisa bikin aplikasi stuck/hitam. 
# Lebih baik jalankan bot utama kamu di PythonAnywhere yang tadi sudah berhasil.
