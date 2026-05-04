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
TP_PCT = 2.0  # Target BSJP biasanya 2% cukup
SL_PCT = 1.5  # Stop Loss lebih ketat untuk BSJP
# ========================================================

st.set_page_config(page_title="Provanch BSJP Scanner", layout="wide")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

# --- LOGIKA ANALISA BSJP ---
def get_bsjp_signals():
    # Daftar saham potensial BSJP (Likuid & Volatil)
    tickers = [
        "PADI.JK", "GOTO.JK", "BUMI.JK", "BRMS.JK", "RAAM.JK", 
        "TINS.JK", "ELSA.JK", "ENRG.JK", "ASRI.JK", "GZCO.JK",
        "WIFI.JK", "DOOH.JK", "HUMI.JK", "BAJA.JK", "BDKR.JK",
        "NATO.JK", "GPSO.JK", "BOAT.JK", "LABA.JK", "STRK.JK", "BSJP.JK"
    ]
    
    results = []
    histories = {}
    
    try:
        # Ambil data hari ini dengan interval 5 menit
        data = yf.download(tickers, period="1d", interval="5m", group_by='ticker', threads=True, progress=False)
        
        for s in tickers:
            try:
                if s not in data or data[s].empty: continue
                valid_data = data[s].dropna()
                if len(valid_data) < 5: continue
                
                px = valid_data['Close'].iloc[-1]
                pc = data[s]['Open'].iloc[0] # Harga Open pagi tadi
                avg_price = valid_data['Close'].mean()
                
                # Cek pergerakan 15 menit terakhir (Power Check)
                last_15m_px = valid_data['Close'].iloc[-3]
                power_score = ((px - last_15m_px) / last_15m_px) * 100
                
                if px > 500: continue # Filter Modal 300k
                
                chg = ((px - pc) / pc) * 100 
                
                # Syarat BSJP: Harga naik di akhir sesi & di atas rata-rata
                status = "💤 SIDEWAYS"
                if px > avg_price and power_score > 0.5 and chg > 2:
                    status = "🔥 BSJP READY"
                elif chg < 0:
                    status = "📉 WEAK"
                
                results.append({
                    "Saham": s.replace(".JK", ""),
                    "Harga": int(px),
                    "Power (15m)": round(power_score, 2),
                    "Change (%)": round(chg, 2),
                    "Status": status,
                    "Score": power_score + chg # Helper sorting
                })
                histories[s.replace(".JK", "")] = valid_data[['Close']]
            except: continue
    except: return pd.DataFrame(), {}
    
    if not results: return pd.DataFrame(), {}
    
    df = pd.DataFrame(results)
    # Sorting berdasarkan Power & Change tertinggi
    df = df.sort_values(by="Score", ascending=False)
    return df, histories

# --- UI DASHBOARD ---
st.title("🚀 Provanch 3.0 - BSJP Strategy")
st.info("🔒 PERMANENT LOCK: Notif Ready & Refresh Features are Locked.")

placeholder = st.empty()

while True:
    now_wib = datetime.utcnow() + timedelta(hours=7)
    df, all_hist = get_bsjp_signals()

    with placeholder.container():
        col_list, col_analysis = st.columns([2, 1])
        
        with col_list:
            st.subheader(f"BSJP Scanner ({now_wib.strftime('%H:%M:%S')})")
            st.dataframe(df.drop(columns=['Score']), use_container_width=True)
            
            if not df.empty:
                top_bsjp = df.iloc[0]['Saham']
                st.subheader(f"📈 Power Graph: {top_bsjp}")
                st.line_chart(all_hist[top_bsjp])

        with col_analysis:
            if not df.empty:
                s_name = df.iloc[0]['Saham']
                s_px = df.iloc[0]['Harga']
                
                st.subheader("🛒 BSJP Order Planner")
                st.write(f"Saham: **{s_name}** | Modal: **300k**")
                
                tp_val = int(s_px * (1 + (TP_PCT/100)))
                cl_val = int(s_px * (1 - (SL_PCT/100)))
                total_lot = int(300000 / (s_px * 100))
                
                st.success(f"🎯 **Jual Besok Pagi (TP): {tp_val}**")
                st.error(f"🛑 **Batas Proteksi (CL): {cl_val}**")
                st.info(f"📦 **Beli Sore Ini: {total_lot} Lot**")
                
                # Auto-Telegram Signal di Jam Closing
                if 15 <= now_wib.hour <= 16 and df.iloc[0]['Status'] == "🔥 BSJP READY":
                    msg = (f"🔥 *BSJP SIGNAL DETECTED!*\n\n"
                           f"Saham: *{s_name}*\nPrice: *{s_px}*\n"
                           f"Power: *{df.iloc[0]['Power (15m)']}* (Strong Closing!)\n\n"
                           f"Beli sekarang, jual besok pagi!")
                    send_telegram(msg)
            else:
                st.write("Menganalisa pergerakan akhir sesi...")

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
