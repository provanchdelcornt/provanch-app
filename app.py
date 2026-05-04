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

# --- PARAMETERS ---
REFRESH_INTERVAL = 30    
MIN_VELOCITY = 1.0       
MIN_DAILY_CHANGE = 1.0   
# ========================================================

st.set_page_config(page_title="Provanch Scalper Pro", layout="wide")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass

# --- VERTEX A: DATA FETCHER (WITH BID/OFFER) ---
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
            
            # Ambil data harga dasar
            last_price = info.last_price
            prev_close = info.regular_market_previous_close
            
            # Simulasi/Ambil Bid & Offer (Jika tersedia di yfinance fast_info)
            # Catatan: yfinance terkadang membatasi bid/ask secara real-time, 
            # kita pakai last_price sebagai patokan jika bid/ask delay.
            bid = getattr(info, 'bid', last_price)
            offer = getattr(info, 'ask', last_price + (last_price * 0.005)) # Estimasi jika ask kosong
            
            chg = ((last_price - prev_close) / prev_close) * 100 if last_price and prev_close else 0
            
            results.append({
                "Saham": s, 
                "Last Price": round(last_price, 2) if last_price else 0, 
                "Bid": round(bid, 2) if bid else 0,
                "Offer": round(offer, 2) if offer else 0,
                "Change (%)": round(chg, 2)
            })
        except:
            continue
    
    df_sorted = pd.DataFrame(results).sort_values(by="Change (%)", ascending=False)
    return df_sorted

# --- DASHBOARD UI ---
st.title("🚀 Provanch Scalper Pro")
st.subheader("Monitoring Real-time (Price, Bid, Offer)")

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}
if 'status_market' not in st.session_state:
    st.session_state.status_market = "unknown"

placeholder = st.empty()

while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    day_of_week = now.weekday() 
    
    # --- VERTEX E: JADWAL BURSA ---
    if current_time == "09:00" and st.session_state.status_market != "open" and day_of_week < 5:
        send_telegram("waktunya cari cuan mas hehe..")
        st.session_state.status_market = "open"
    elif current_time == "16:00" and st.session_state.status_market != "closed":
        send_telegram("market sudah tutup mas >_<")
        st.session_state.status_market = "closed"

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

        # --- TABEL UTAMA DENGAN BID & OFFER ---
        st.dataframe(df, use_container_width=True)

        # --- VERTEX D: VELOCITY DETECTION ---
        if market_open:
            for index, row in df.iterrows():
                sym = row['Saham']
                px = row['Last Price']
                day_chg = row['Change (%)']
                
                if sym in st.session_state.price_history:
                    old_px = st.session_state.price_history[sym]
                    if old_px > 0:
                        velocity = ((px - old_px) / old_px) * 100
                        if velocity >= MIN_VELOCITY and day_chg >= MIN_DAILY_CHANGE:
                            msg = (f"🔥 *SCALP MOMENTUM: {sym}*\n"
                                   f"Price: *{px}*\n"
                                   f"Bid: *{row['Bid']}* | Offer: *{row['Offer']}*\n"
                                   f"Speed: *+{velocity:.2f}%*\n"
                                   f"Status: *PERTANDA BAGUS*")
                            send_telegram(msg)
                st.session_state.price_history[sym] = px

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
