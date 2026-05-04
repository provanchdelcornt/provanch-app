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

st.set_page_config(page_title="Provanch Budget Scalper", layout="wide")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

# --- LOGIKA DETEKSI ARA ---
def check_ara_status(price, prev_close):
    if prev_close <= 0: return False
    change = ((price - prev_close) / prev_close) * 100
    # Batas ARA di Indonesia: >200 (35%), 200-500 (25%)
    if price <= 200 and change >= 34: return True
    if price > 200 and change >= 24: return True
    return False

# --- VERTEX A: DATA FETCHER (SMART FILTER) ---
def get_budget_stocks():
    watchlist = [
        "PADI.JK", "GOTO.JK", "BUMI.JK", "BRMS.JK", "DOOH.JK",
        "WIFI.JK", "STRK.JK", "HUMI.JK", "BAJA.JK", "CARE.JK",
        "FWCT.JK", "NZIA.JK", "NICL.JK", "RAAM.JK", "BDKR.JK",
        "PSAB.JK", "TINS.JK", "ELSA.JK", "ENRG.JK", "BIPI.JK"
    ]
    
    results = []
    for s in watchlist:
        try:
            t = yf.Ticker(s)
            hist = t.history(period="5d")
            if len(hist) < 2: continue
            
            px = hist['Close'].iloc[-1]
            pc = hist['Close'].iloc[-2]
            
            if px > 500: continue # Tetap filter harga murah
            
            chg = ((px - pc) / pc) * 100 
            is_ara = check_ara_status(px, pc)
            
            # --- PENENTUAN STATUS ---
            status = "🔥 POTENSI"
            if is_ara:
                status = "🚫 ARA (JANGAN MASUK)"
            elif chg < 0:
                status = "📉 DROP"
            
            results.append({
                "Saham": s, 
                "Harga": int(px), 
                "Change (%)": round(chg, 2),
                "Status": status,
                "Entry": int(px),
                "SL": int(px * (1 - (SL_PCT / 100))),
                "TP": int(px * (1 + (TP_PCT / 100))),
                "Is_ARA": is_ara # Hidden helper
            })
        except: continue
    
    df = pd.DataFrame(results)
    # SORTING PINTAR: Yang ARA ditaruh paling bawah, yang Potensi naik ditaruh atas
    df = df.sort_values(by=["Is_ARA", "Change (%)"], ascending=[True, False])
    return df.drop(columns=['Is_ARA'])

# --- DASHBOARD UI ---
st.title("🚀 Provanch Budget Scalper")
st.subheader("Smart Monitoring: Otomatis Filter Saham ARA")

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}

placeholder = st.empty()

while True:
    now_wib = datetime.utcnow() + timedelta(hours=7)
    market_is_open = 9 <= now_wib.hour < 16 and now_wib.weekday() < 5
    
    df = get_budget_stocks()

    with placeholder.container():
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Last Refresh (WIB)", now_wib.strftime("%H:%M:%S"))
        with c2: st.metric("Market Status", "OPEN" if market_is_open else "STANDBY")
        with c3:
            if not df.empty:
                top = df.iloc[0] # Sekarang top 1 bukan ARA
                st.metric("Best Entry", top['Saham'], f"{top['Change (%)']}%")

        st.dataframe(df, use_container_width=True)

        # Telegram hanya kirim notif jika BUKAN ARA
        if market_is_open:
            for index, row in df.iterrows():
                if "ARA" in row['Status']: continue # Lewati notif ARA
                
                sym = row['Saham']
                px = row['Harga']
                if sym in st.session_state.price_history:
                    old_px = st.session_state.price_history[sym]
                    velocity = ((px - old_px) / old_px) * 100
                    if velocity >= MIN_VELOCITY:
                        msg = (f"🎯 *SMART SIGNAL: {sym}*\nPrice: *{px}* (+{velocity:.2f}%)\n"
                               f"Status: *BELUM ARA - AMAN ENTRY*\n"
                               f"TP: *{row['TP']}* | SL: *{row['SL']}*")
                        send_telegram(msg)
                st.session_state.price_history[sym] = px

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
