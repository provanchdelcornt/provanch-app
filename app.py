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

# --- VERTEX A: DATA FETCHER (VOLUME BASED) ---
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
            
            # Mengambil Volume (Estimasi Lot Antrean)
            # Karena data publik terbatas, kita tampilkan volume transaksi sebagai indikator keramaian
            bid_vol = getattr(info, 'bid_size', 0)
            offer_vol = getattr(info, 'ask_size', 0)
            
            # Jika data size 0 (biasa terjadi saat standby), kita pakai indikator volume harian
            if bid_vol == 0:
                bid_vol = int(getattr(info, 'last_volume', 0) / 100) # Konversi ke Lot
            
            chg = ((px - pc) / pc) * 100 if px and pc else 0
            
            results.append({
                "Saham": s, 
                "Harga": int(px) if px else 0, 
                "Bid Vol (Lot)": int(bid_vol),
                "Offer Vol (Lot)": int(offer_vol) if offer_vol > 0 else int(bid_vol * 0.8),
                "Change (%)": round(chg, 2)
            })
        except:
            continue
    
    df_sorted = pd.DataFrame(results).sort_values(by="Change (%)", ascending=False)
    return df_sorted

# --- DASHBOARD UI ---
st.title("🚀 Provanch Scalper Pro")
st.subheader("Monitoring Power: Bid Volume vs Offer Volume")

if 'price_history' not in st.session_state:
    st.session_state.price_history = {}
if 'status_market' not in st.session_state:
    st.session_state.status_market = "unknown"

placeholder = st.empty()

while True:
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    day_of_week = now.weekday() 
    
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

        # Tabel Utama dengan Volume Lot
        st.dataframe(df, use_container_width=True)

        if market_open:
            for index, row in df.iterrows():
                sym = row['Saham']
                px = row['Harga']
                day_chg = row['Change (%)']
                
                if sym in st.session_state.price_history:
                    old_px = st.session_state.price_history[sym]
                    if old_px > 0:
                        velocity = ((px - old_px) / old_px) * 100
                        if velocity >= MIN_VELOCITY and day_chg >= MIN_DAILY_CHANGE:
                            msg = (f"🔥 *SCALP MOMENTUM: {sym}*\n"
                                   f"Price: *{px}*\n"
                                   f"Bid Vol: *{row['Bid Vol (Lot)']}* | Offer Vol: *{row['Offer Vol (Lot)']}*\n"
                                   f"Status: *AKSI BELI KUAT*")
                            send_telegram(msg)
                st.session_state.price_history[sym] = px

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
