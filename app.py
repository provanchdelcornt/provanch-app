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

# --- PARAMETERS SCALPING ---
REFRESH_INTERVAL = 30    # Locked
MIN_VELOCITY = 1.0       # Notif jika naik > 1% dalam 30 detik
TP_PCT = 2.5             # Target Profit 2.5%
SL_PCT = 1.8             # Stop Loss 1.8%
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
            
            # Ambil Estimasi Volume Antrean
            bid_vol = int(getattr(info, 'bid_size', getattr(info, 'last_volume', 0) / 100))
            offer_vol = int(getattr(info, 'ask_size', bid_vol * 0.8))
            
            chg = ((px - pc) / pc) * 100 if pc else 0
            
            # Logika Signal Entry/SL/TP
            entry = px
            sl = px * (1 - (SL_PCT / 100))
            tp = px * (1 + (TP_PCT / 100))
            
            results.append({
                "Saham": s, 
                "Harga": int(px), 
                "Bid Vol": int(bid_vol),
                "Offer Vol": int(offer_vol),
                "Entry": int(entry),
                "SL": int(sl),
                "TP": int(tp),
                "Change (%)": round(chg, 2)
            })
        except:
            continue
    
    # Auto-sort berdasarkan performa terbaik
    return pd.DataFrame(results).sort_values(by="Change (%)", ascending=False)

# --- DASHBOARD UI ---
st.title("🚀 Provanch Scalper Pro")
st.subheader("Real-time Scalping Monitor")

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}

placeholder = st.empty()

# --- MAIN LOOP (FORCE UPDATE) ---
while True:
    now = datetime.now()
    # Market dianggap buka jam 09:00 - 16:00 WIB, Senin-Jumat
    market_is_open = 9 <= now.hour < 16 and now.weekday() < 5
    
    df = get_dynamic_top_data()

    with placeholder.container():
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Last Refresh", now.strftime("%H:%M:%S"))
        with c2: st.metric("Market Status", "OPEN" if market_is_open else "STANDBY")
        with c3:
            if not df.empty:
                top = df.iloc[0]
                st.metric("Top Gainer", top['Saham'], f"{top['Change (%)']}%")

        # Tabel Utama (Clean & Tanpa Koma)
        st.dataframe(df, use_container_width=True)

        # --- VERTEX D: VELOCITY & SIGNAL NOTIF ---
        if market_is_open:
            for index, row in df.iterrows():
                sym = row['Saham']
                px = row['Harga']
                if sym in st.session_state.price_history:
                    old_px = st.session_state.price_history[sym]
                    velocity = ((px - old_px) / old_px) * 100
                    
                    if velocity >= MIN_VELOCITY:
                        msg = (f"🎯 *SIGNAL: {sym}*\n"
                               f"Price: *{px}* (Speed: +{velocity:.2f}%)\n"
                               f"Bid/Offer: {row['Bid Vol']}/{row['Offer Vol']}\n"
                               f"Target TP: *{row['TP']}* | SL: *{row['SL']}*")
                        send_telegram(msg)
                st.session_state.price_history[sym] = px

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
