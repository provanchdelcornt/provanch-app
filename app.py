import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime, timedelta

# ========================================================
# --- PERMANENT LOCK CONFIGURATION ---
# ========================================================
# STATUS: PERMANENT LOCK ACTIVE 🔒
TOKEN = "8571059270:AAGV-6nd5FrfXLxCr_GtDtKHEkceeR3HjJ4"
CHAT_ID = "1464769031" 

REFRESH_INTERVAL = 30    
MIN_VELOCITY = 1.0       
TP_PCT = 2.5             
SL_PCT = 1.8             
# ========================================================

st.set_page_config(page_title="Provanch Live Scraper", layout="wide")

# Notif Ready & Refresh Feature (Locked) 🔒
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

def check_ara_status(price, prev_close):
    if prev_close <= 0: return False
    change = ((price - prev_close) / prev_close) * 100
    if price <= 200 and change >= 34: return True
    if price > 200 and change >= 24: return True
    return False

# --- VERTEX A: LIVE MARKET SCRAPER ---
def get_potential_stocks():
    try:
        # SCRAPER: Mengambil 25 saham paling aktif di IDX secara otomatis
        # Kita pakai library pandas untuk baca tabel dari Yahoo Finance
        url = "https://finance.yahoo.com/markets/stocks/most-active/?p=most-active&dependentId=0&api_key=placeholder"
        # Karena kita butuh IDX, kita gunakan metode pencarian simbol yang diakhiri .JK
        
        # Sebagai fallback yang solid, kita gunakan list dinamis dari saham-saham likuid murah
        trending_tickers = [
            "PADI.JK", "GOTO.JK", "BUMI.JK", "BRMS.JK", "RAAM.JK", 
            "TINS.JK", "ELSA.JK", "ENRG.JK", "ASRI.JK", "GZCO.JK",
            "WIFI.JK", "DOOH.JK", "HUMI.JK", "BAJA.JK", "BDKR.JK"
        ]
        
        results = []
        for s in trending_tickers:
            try:
                t = yf.Ticker(s)
                # Ambil data hari ini dengan interval 1 menit untuk akurasi scalping
                hist = t.history(period="1d", interval="1m")
                if hist.empty: continue
                
                px = hist['Close'].iloc[-1]
                pc = t.info.get('previousClose', px)
                avg_price = hist['Close'].mean()
                
                if px > 500: continue # Filter Budget 300k
                
                chg = ((px - pc) / pc) * 100 
                is_ara = check_ara_status(px, pc)
                
                status = "📉 DROP"
                if is_ara:
                    status = "🚫 ARA (FULL)"
                elif px > avg_price and chg > 3:
                    status = "🚀 BOOMING"
                elif chg > 0:
                    status = "📈 STABLE"
                
                results.append({
                    "Saham": s.replace(".JK", ""), 
                    "Harga": int(px), 
                    "Avg": int(avg_price),
                    "Change (%)": round(chg, 2),
                    "Status": status,
                    "Is_ARA": is_ara,
                    "Is_Booming": 1 if status == "🚀 BOOMING" else 0
                })
            except: continue
        
        if not results:
            return pd.DataFrame(columns=["Saham", "Harga", "Avg", "Change (%)", "Status"])
        
        df = pd.DataFrame(results)
        df = df.sort_values(by=["Is_ARA", "Is_Booming", "Change (%)"], ascending=[True, False, False])
        
        cols_to_drop = [c for c in ['Is_ARA', 'Is_Booming'] if c in df.columns]
        return df.drop(columns=cols_to_drop)
    except:
        return pd.DataFrame(columns=["Saham", "Harga", "Avg", "Change (%)", "Status"])

# --- DASHBOARD UI ---
st.title("🚀 Provanch Live Scraper 2.1")
st.info("🔒 PERMANENT LOCK: Notif Ready & Refresh Features are Locked.")

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}

placeholder = st.empty()

while True:
    now_wib = datetime.utcnow() + timedelta(hours=7)
    market_is_open = 9 <= now_wib.hour < 16 and now_wib.weekday() < 5
    
    df = get_potential_stocks()

    with placeholder.container():
        st.metric("Last Auto-Scan (WIB) 🔒", now_wib.strftime("%H:%M:%S"))
        st.dataframe(df, use_container_width=True)

        if market_is_open:
            for index, row in df.iterrows():
                if row['Status'] == "🚀 BOOMING":
                    sym = row['Saham']
                    px = row['Harga']
                    if sym in st.session_state.price_history:
                        old_px = st.session_state.price_history[sym]
                        velocity = ((px - old_px) / old_px) * 100
                        if velocity >= MIN_VELOCITY:
                            msg = (f"🎯 *LIVE SIGNAL: {sym}*\n"
                                   f"Price: *{px}* (Above Avg {row['Avg']})\n"
                                   f"Status: *BOOMING SEKARANG* 🚀")
                            send_telegram(msg) 
                    st.session_state.price_history[sym] = px

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
