import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime

# ========================================================
# --- PERMANENT LOCK CONFIGURATION (DO NOT CHANGE) ---
# ========================================================
TOKEN = "8571059270:AAGV-6nd5FrfXLxCr_GtDtKHEkceeR3HjJ4"
CHAT_ID = "1464769031" 

# --- PARAMETERS SCALPING ---
REFRESH_INTERVAL = 30    
MIN_VELOCITY = 1.0       
TP_PCT = 2.5   # Take Profit 2.5%
SL_PCT = 1.8   # Stop Loss 1.8%
# ========================================================

st.set_page_config(page_title="Provanch Scalper Pro", layout="wide")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass

# --- VERTEX A: DATA FETCHER WITH SIGNALS ---
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
            
            chg = ((px - pc) / pc) * 100
            
            # --- LOGIKA SARAN HARGA (SIGNAL) ---
            entry = px
            stop_loss = px * (1 - (SL_PCT / 100))
            take_profit = px * (1 + (TP_PCT / 100))
            
            results.append({
                "Saham": s, 
                "Harga": int(px), 
                "Entry": int(entry),
                "Stop Loss (SL)": int(stop_loss),
                "Take Profit (TP)": int(take_profit),
                "Change (%)": round(chg, 2)
            })
        except:
            continue
    
    return pd.DataFrame(results).sort_values(by="Change (%)", ascending=False)

# --- DASHBOARD UI ---
st.title("🚀 Provanch Scalper Pro")
st.subheader("Signal Mode: Entry, SL, & TP")

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}
if 'status_market' not in st.session_state:
    st.session_state.status_market = "unknown"

placeholder = st.empty()

while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    day_of_week = now.weekday() 
    
    df = get_dynamic_top_data()

    with placeholder.container():
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Last Refresh", now.strftime("%H:%M:%S"))
        with c2: 
            market_open = 9 <= now.hour < 16 and day_of_week < 5
            st.metric("Market Status", "OPEN" if market_open else "STANDBY")
        with c3:
            if not df.empty:
                top = df.iloc[0]
                st.metric("Top Gainer", top['Saham'], f"{top['Change (%)']}%")

        # --- TABEL DENGAN SARAN HARGA ---
        st.dataframe(df, use_container_width=True)

        # --- TELEGRAM NOTIF WITH SIGNAL ---
        if market_open:
            for index, row in df.iterrows():
                sym = row['Saham']
                px = row['Harga']
                if sym in st.session_state.price_history:
                    old_px = st.session_state.price_history[sym]
                    velocity = ((px - old_px) / old_px) * 100
                    
                    if velocity >= MIN_VELOCITY:
                        msg = (f"🎯 *SIGNAL DETECTED: {sym}*\n"
                               f"Entry: *{row['Entry']}*\n"
                               f"Take Profit: *{row['Take Profit (TP)']}*\n"
                               f"Cut Loss: *{row['Stop Loss (SL)']}*\n"
                               f"Speed: *+{velocity:.2f}%*")
                        send_telegram(msg)
                st.session_state.price_history[sym] = px

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
