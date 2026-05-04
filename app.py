import feedparser
import requests
import time
import re
from datetime import datetime

# ========================================================
# --- CONFIGURATION (VERSI LENGKAP RIFKY) ---
# ========================================================
TOKEN = "8571059270:AAGV-6nd5FrfXLxCr_GtDtKHEkceeR3HjJ4"
CHAT_ID = "1464769031"

FEEDS = {
    "CNBC Market": "https://www.cnbcindonesia.com/market/rss",
    "Kontan Saham": "https://www.kontan.co.id/rss/saham",
    "Bisnis News": "https://www.bisnis.com/rss/indeks"
}

processed_news = set()

def clean_html(text):
    return re.sub(re.compile('<.*?>'), '', text)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def generate_plan_template():
    """Membuat template plan kosong untuk diisi manual saat scalping"""
    return (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 **DAY TRADE STRATEGY**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 **ENTRY AREA :** _Cek Bid/Offer (Haka/Antri)_ \n"
        "🔴 **CUT LOSS   :** _-2% s/d -3% dari Entry_ \n"
        "🔵 **TAKE PROFIT:** _+2% (Bungkus) / +5% (Hold)_ \n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

def run_news_bot():
    print(f"[{datetime.now()}] Provanch Intelligence 24/7 Started...")
    
    # Notif pembuka yang lebih keren
    welcome_msg = (
        "🔥 **PROVANCH NEWS INTELLIGENCE ACTIVE** 🔥\n\n"
        "Sistem siap memantau Market 24 Jam.\n"
        "Plan Day Trade akan disertakan pada setiap berita."
    )
    send_telegram(welcome_msg)

    while True:
        for source_name, url in FEEDS.items():
            try:
                feed = feedparser.parse(url)
                if not feed.entries:
                    continue
                
                entry = feed.entries[0]
                if entry.link not in processed_news:
                    title = entry.title
                    summary = clean_html(entry.get('summary', 'Lihat detail di sumber.'))
                    short_summary = (summary[:130] + '...') if len(summary) > 130 else summary
                    
                    # Gabungkan Berita + Trading Plan
                    full_msg = (
                        f"🆕 *BERITA TERBARU: {source_name.upper()}*\n\n"
                        f"🗞 *Judul:* {title}\n"
                        f"📝 *Brief:* {short_summary}\n\n"
                        f"{generate_plan_template()}\n\n"
                        f"🔗 [Baca Selengkapnya Di Sini]({entry.link})"
                    )
                    
                    send_telegram(full_msg)
                    processed_news.add(entry.link)
                    
                    if len(processed_news) > 100:
                        processed_news.clear()
                        
            except Exception as e:
                print(f"Error: {e}")
        
        # Interval cek berita tiap 2 menit
        time.sleep(120)

if __name__ == "__main__":
    run_news_bot()
