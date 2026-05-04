import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime, timedelta

# ========================================================
# --- PERMANENT LOCK CONFIGURATION (DO NOT CHANGE) ---
# ========================================================
# Fitur 'Notif Ready' dan 'Refresh' Terkunci Secara Permanen
TOKEN = "8571059270:AAGV-6nd5FrfXLxCr_GtDtKHEkceeR3HjJ4"
CHAT_ID = "1464769031" # @Bentartapinyaman

# --- PARAMETERS SCALPING ---
REFRESH_INTERVAL = 30    # Locked
MIN_VELOCITY = 1.0       
TP_PCT = 2.5             
SL_PCT = 1.8             
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

# --- VERTEX A: DYNAMIC DATA FETCHER (VOLUME & SIGNAL) ---
def get_dynamic_top_data():
    watchlist = [
        "PADI.JK", "GOTO.JK", "BUMI.JK", "ASII.JK", "BBRI.JK", 
        "TLKM.JK", "BBCA.JK", "BMRI.JK", "BRMS.JK", "ADRO.JK",
        "PTBA.JK", "ITMG.JK", "AKRA.JK", "PGAS.JK", "MEDC.JK",
        "ANTM.JK", "TINS.JK", "BRIS.JK", "AMMN.JK", "BBNI.JK"
    ]
    
    results = []
    for s in watchlist:
        try:
            t = yf.Ticker(s)
            info = t.fast_info
            px = info.last_price
            pc = info.regular_market_previous_close
            
            if not px: continue
            
            # Ambil Estimasi Volume (Lot)
            # Menggunakan volume transaksi harian dibagi 100 untuk estimasi Lot
            vol_raw = getattr(info, 'last_volume', 0)
            lot_vol = int(vol_raw / 100) if vol_raw > 0 else 0
            
            chg = ((px - pc) / pc) * 100 if pc else 0
            
            # Logika Signal Entry/SL/TP (Bulat tanpa koma)
            entry = px
            sl = px * (1 - (SL_PCT / 100))
            tp = px * (1 + (TP_PCT / 100))
            
            results.append({
                "Saham": s, 
                "Harga": int(px), 
                "Bid Vol (Lot)": lot_vol,
                "Offer Vol (Lot)": int(lot_vol * 0.8), # Estimasi proporsional
                "Entry": int(entry),
                "SL": int(sl),
                "TP": int(tp),
                "Change (%)": round(chg, 2)
            })
        except:
            continue
    
    # Auto-sort berdasarkan Change (%) tertinggi agar mirip Stockbit
    return pd.DataFrame(results).sort_values(by="Change (%)", ascending=False)

# --- DASHBOARD UI ---
st.title("🚀 Provanch Scalper Pro")
st.subheader("Real-time Monitor (WIB Sync)")

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}

placeholder = st.empty()

# --- MAIN LOOP (WIB TIME & FORCE REFRESH) ---
while True:
    # Sinkronisasi Waktu Server ke WIB (UTC+7)
    now_utc = datetime.utcnow()
    now_wib = now_utc + timedelta(hours=7)
    
    current_hour = now_wib.hour
    day_of_week = now_wib.weekday() 
    
    # Deteksi Market Open (Senin-Jumat, 09:00 - 16:00 WIB)
    market_is_open = 9 <= current_hour < 16 and day_of_week < 5
    
    df = get_dynamic_top_data()

    with placeholder.container():
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Last Refresh (WIB)", now_wib.strftime("%H:%M:%S"))
        with c2: st.metric("Market Status", "OPEN" if market_is_open else "STANDBY")
        with c3:
            if not df.empty:
                top = df.iloc[0]
                st.metric("Top Gainer", top['Saham'], f"{top['Change (%)']}%")

        # Tabel Utama (Final Format)
        st.dataframe(df, use_container_width=True)

        # --- VERTEX D: VELOCITY & TELEGRAM SIGNAL ---
        if market_is_open:
            for index, row in df.iterrows():
                sym = row['Saham']
                px = row['Harga']
                if sym in st.session_state.price_history:
                    old_px = st.session_state.price_history[sym]
                    if old_px > 0:
                        velocity = ((px - old_px) / old_px) * 100
                        if velocity >= MIN_VELOCITY:
                            msg = (f"🎯 *SIGNAL: {sym}*\n"
                                   f"Price: *{px}* (Speed: +{velocity:.2f}%)\n"
                                   f"TP: *{row['TP']}* | SL: *{row['SL']}*\n"
                                   f"Status: *AKSI BELI KUAT*")
                            send_telegram(msg)
                st.session_state.price_history[sym] = px

    # --- REFRESH SYSTEM (LOCKED) ---
    time.sleep(REFRESH_INTERVAL)
    st.rerun()
