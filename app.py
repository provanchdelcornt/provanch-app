import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime

# ========================================================
# --- PERMANENT LOCK CONFIGURATION (DO NOT CHANGE) ---
# ========================================================
# Fitur 'Notif Ready' dan 'Refresh' Terkunci Secara Permanen
TOKEN = "8571059270:AAGV-6nd5FrfXLxCr_GtDtKHEkceeR3HjJ4"
CHAT_ID = "1464769031" # @Bentartapinyaman

# --- PARAMETERS ---
REFRESH_INTERVAL = 30    # Sesuai fitur 'Refresh' permanen
MIN_VELOCITY = 1.0       # Notif jika naik > 1% dalam 30 detik
MIN_DAILY_CHANGE = 1.0   # Hanya pantau saham yang sudah hijau
# ========================================================

st.set_page_config(page_title="Provanch Scalper Pro", layout="wide")

# --- VERTEX C: NOTIF READY (TELEGRAM) ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass

# --- VERTEX A: DATA FETCHER (TOP VALUE BEI) ---
def get_top_20_data():
    hot_stocks = [
        "PADI.JK", "GOTO.JK", "BUMI.JK", "ASII.JK", "BBRI.JK", 
        "TLKM.JK", "BBCA.JK", "BMRI.JK", "BRMS.JK", "ADRO.JK",
        "PTBA.JK", "ITMG.JK", "AKRA.JK", "PGAS.JK", "MEDC.JK",
        "ANTM.JK", "TINS.JK", "BRIS.JK", "AMMN.JK", "BBNI.JK"
    ]
    
    results = []
    for s in hot_stocks:
        try:
            t = yf.Ticker(s)
            info = t.fast_info
            px = info.last_price
            pc = info.regular_market_previous_close
            # Hitung kenaikan harian
            chg = ((px - pc) / pc) * 100 if px and pc else 0
            results.append({
                "Saham": s, 
                "Harga": round(px, 2) if px else 0, 
                "Change (%)": round(chg, 2)
            })
        except:
            continue
    return pd.DataFrame(results)

# --- DASHBOARD UI ---
st.title("🚀 Provanch Scalper Pro")
st.subheader("Monitoring Top 20 Saham Paling Rame")

# Inisialisasi State (Agar data tidak hilang saat refresh)
if 'price_history' not in st.session_state:
    st.session_state.price_history = {}
if 'status_market' not in st.session_state:
    st.session_state.status_market = "unknown"

placeholder = st.empty()

# --- MAIN LOOP ---
while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    day_of_week = now.weekday() # 0=Senin, 4=Jumat
    
    # --- VERTEX E: JADWAL BURSA (NOTIF) ---
    if current_time == "09:00" and st.session_state.status_market != "open" and day_of_week < 5:
        send_telegram("waktunya cari cuan mas hehe..")
        st.session_state.status_market = "open"
    elif current_time == "16:00" and st.session_state.status_market != "closed":
        send_telegram("market sudah tutup mas >_<")
        st.session_state.status_market = "closed"

    # Fetch Data Terbaru
    df = get_top_20_data()

    with placeholder.container():
        # Kolom Indikator
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Last Refresh", now.strftime("%H:%M:%S"))
        with c2:
            market_open = 9 <= now.hour < 16 and day_of_week < 5
            st.metric("Market Status", "OPEN" if market_open else "STANDBY")
        with c3:
            if not df.empty:
                top = df.sort_values(by="Change (%)", ascending=False).iloc[0]
                st.metric("Top Gainer", top['Saham'], f"{top['Change (%)']}%")

        # --- TABEL UTAMA (FIXED: Tanpa Gradient Agar Tidak Error) ---
        st.dataframe(df, use_container_width=True)

        # --- VERTEX D: VELOCITY DETECTION ---
        if market_open:
            for index, row in df.iterrows():
                sym = row['Saham']
                px = row['Harga']
                day_chg = row['Change (%)']
                
                if sym in st.session_state.price_history:
                    old_px = st.session_state.price_history[sym]
                    # Deteksi lonjakan harga dalam 30 detik
                    if old_px > 0:
                        velocity = ((px - old_px) / old_px) * 100
                        
                        # Trigger Notif Ready
                        if velocity >= MIN_VELOCITY and day_chg >= MIN_DAILY_CHANGE:
                            msg = (f"🔥 *SCALP MOMENTUM: {sym}*\n"
                                   f"Price: *{px}*\n"
                                   f"Speed: *+{velocity:.2f}%* (30s)\n"
                                   f"Status: *PERTANDA BAGUS*")
                            send_telegram(msg)
                
                st.session_state.price_history[sym] = px

    # --- REFRESH SYSTEM ---
    time.sleep(REFRESH_INTERVAL)
    st.rerun()
