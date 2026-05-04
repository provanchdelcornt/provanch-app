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

st.set_page_config(page_title="Provanch Auto-Scanner 2.0", layout="wide")

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

# --- VERTEX A: SMART AUTO-SCANNER ---
def get_potential_stocks():
    # Daftar pantauan lebih luas untuk scanning
    watchlist = [
        "PADI.JK", "GOTO.JK", "BUMI.JK", "BRMS.JK", "DOOH.JK",
        "WIFI.JK", "STRK.JK", "HUMI.JK", "BAJA.JK", "CARE.JK",
        "FWCT.JK", "NZIA.JK", "NICL.JK", "RAAM.JK", "BDKR.JK",
        "PSAB.JK", "TINS.JK", "ELSA.JK", "ENRG.JK", "BIPI.JK",
        "ASRI.JK", "KLAS.JK", "SAGE.JK", "SMGA.JK", "WIDI.JK"
    ]
    
    results = []
    for s in watchlist:
        try:
            t = yf.Ticker(s)
            hist = t.history(period="2d")
            if len(hist) < 2: continue
            
            px = hist['Close'].iloc[-1]
            pc = hist['Close'].iloc[-2]
            avg_price = hist[['Open', 'High', 'Low', 'Close']].iloc[-1].mean()
            
            if px > 500: continue # Filter Budget 300k
            
            chg = ((px - pc) / pc) * 100 
            is_ara = check_ara_status(px, pc)
            
            # LOGIKA POTENSIAL: Harga > Avg & Belum ARA
            status = "📉 DROP"
            if is_ara:
                status = "🚫 ARA (FULL)"
            elif px > avg_price and chg > 2:
                status = "🚀 BOOMING"
            elif chg > 0:
                status = "📈 STABLE"
            
            results.append({
                "Saham": s, 
                "Harga": int(px), 
                "Avg": int(avg_price),
                "Change (%)": round(chg, 2),
                "Status": status,
                "Is_ARA": is_ara,
                "Is_Booming": 1 if status == "🚀 BOOMING" else 0
            })
        except: continue
    
    df = pd.DataFrame(results)
    # Sorting: Booming dulu, baru Change tertinggi, ARA paling bawah
    if not df.empty:
        df = df.sort_values(by=["Is_ARA", "Is_Booming", "Change (%)"], ascending=[True, False, False])
    return df.drop(columns=['Is_ARA', 'Is_Booming'])

# --- DASHBOARD UI ---
st.title("🚀 Provanch Auto-Scanner 2.0")
st.info("🔒 PERMANENT LOCK: Notif Ready & Refresh Features are Locked.")

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}

placeholder = st.empty()

while True:
    now_wib = datetime.utcnow() + timedelta(hours=7)
    market_is_open = 9 <= now_wib.hour < 16 and now_wib.weekday() < 5
    
    df = get_potential_stocks()

    with placeholder.container():
        st.metric("Last Refresh (WIB) 🔒", now_wib.strftime("%H:%M:%S"))
        
        # Display Table
        st.dataframe(df, use_container_width=True)

        # Smart Telegram Logic
        if market_is_open:
            for index, row in df.iterrows():
                if row['Status'] == "🚀 BOOMING":
                    sym = row['Saham']
                    px = row['Harga']
                    if sym in st.session_state.price_history:
                        old_px = st.session_state.price_history[sym]
                        velocity = ((px - old_px) / old_px) * 100
                        if velocity >= MIN_VELOCITY:
                            msg = (f"🔥 *AUTO-SCANNER ALERT: {sym}*\n"
                                   f"Price: *{px}* (Above Avg {row['Avg']})\n"
                                   f"Change: *{row['Change (%)']}%*\n"
                                   f"Status: *CONFIRMED BOOMING* 🚀")
                            send_telegram(msg) # Notif Ready 🔒
                    st.session_state.price_history[sym] = px

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
