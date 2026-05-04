import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime, timedelta

# ========================================================
# --- PERMANENT LOCK CONFIGURATION ---
# ========================================================
TOKEN = "8571059270:AAGV-6nd5FrfXLxCr_GtDtKHEkceeR3HjJ4"
CHAT_ID = "1464769031" 

REFRESH_INTERVAL = 30    
MIN_VELOCITY = 1.0       
TP_PCT = 2.5             
SL_PCT = 1.8             
# ========================================================

st.set_page_config(page_title="Provanch Scalper Pro", layout="wide")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

# --- VERTEX A: DATA FETCHER (FORCED DATA) ---
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
            # Ambil history 5 hari terakhir untuk memastikan data CLOSE ada
            hist = t.history(period="5d")
            
            if len(hist) < 2: continue
            
            px = hist['Close'].iloc[-1] # Harga Terakhir
            pc = hist['Close'].iloc[-2] # Harga Penutupan Sebelumnya
            
            vol_raw = hist['Volume'].iloc[-1]
            lot_vol = int(vol_raw / 100)
            chg = ((px - pc) / pc) * 100 
            
            results.append({
                "Saham": s, 
                "Harga": int(px), 
                "Bid Vol (Lot)": lot_vol,
                "Offer Vol (Lot)": int(lot_vol * 0.8),
                "Entry": int(px),
                "SL": int(px * (1 - (SL_PCT / 100))),
                "TP": int(px * (1 + (TP_PCT / 100))),
                "Change (%)": round(chg, 2)
            })
        except: continue
    
    # Sortir agar yang paling cuan di atas
    return pd.DataFrame(results).sort_values(by="Change (%)", ascending=False)

# --- DASHBOARD UI ---
st.title("🚀 Provanch Scalper Pro")

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}

placeholder = st.empty()

while True:
    now_wib = datetime.utcnow() + timedelta(hours=7)
    market_is_open = 9 <= now_wib.hour < 16 and now_wib.weekday() < 5
    
    df = get_dynamic_top_data()

    with placeholder.container():
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Last Refresh (WIB)", now_wib.strftime("%H:%M:%S"))
        with c2: st.metric("Market Status", "OPEN" if market_is_open else "STANDBY")
        with c3:
            if not df.empty:
                top = df.iloc[0]
                st.metric("Top Gainer", top['Saham'], f"{top['Change (%)']}%")

        st.dataframe(df, use_container_width=True)

        if market_is_open:
            for index, row in df.iterrows():
                sym = row['Saham']
                px = row['Harga']
                if sym in st.session_state.price_history:
                    old_px = st.session_state.price_history[sym]
                    if old_px > 0:
                        velocity = ((px - old_px) / old_px) * 100
                        if velocity >= MIN_VELOCITY:
                            msg = (f"🎯 *SIGNAL: {sym}*\nPrice: *{px}* (+{velocity:.2f}%)\n"
                                   f"TP: *{row['TP']}* | SL: *{row['SL']}*")
                            send_telegram(msg)
                st.session_state.price_history[sym] = px

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
