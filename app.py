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
# ========================================================

st.set_page_config(page_title="Provanch Scraper + Graph", layout="wide")

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

# --- VERTEX A: SCANNER WITH HISTORY ---
def get_data_and_history():
    trending_tickers = [
        "PADI.JK", "GOTO.JK", "BUMI.JK", "BRMS.JK", "RAAM.JK", 
        "TINS.JK", "ELSA.JK", "ENRG.JK", "ASRI.JK", "GZCO.JK",
        "WIFI.JK", "DOOH.JK", "HUMI.JK", "BAJA.JK", "BDKR.JK",
        "NATO.JK", "GPSO.JK", "BOAT.JK", "LABA.JK", "STRK.JK"
    ]
    
    results = []
    histories = {}
    
    try:
        data = yf.download(trending_tickers, period="1d", interval="5m", group_by='ticker', threads=True, progress=False)
        
        for s in trending_tickers:
            try:
                if s not in data or data[s].empty: continue
                valid_data = data[s].dropna()
                if valid_data.empty: continue
                
                last_row = valid_data.iloc[-1]
                px = last_row['Close']
                pc = data[s]['Open'].iloc[0] 
                avg_price = valid_data['Close'].mean()
                
                if px > 500 or px <= 0: continue 
                
                chg = ((px - pc) / pc) * 100 
                is_ara = check_ara_status(px, pc)
                
                status = "📈 STABLE"
                if is_ara: status = "🚫 ARA (FULL)"
                elif px > avg_price and chg > 2.5: status = "🚀 BOOMING"
                elif chg < 0: status = "📉 DROP"
                
                results.append({
                    "Saham": s.replace(".JK", ""), 
                    "Harga": int(px), 
                    "Avg": int(avg_price),
                    "Change (%)": round(chg, 2),
                    "Status": status,
                    "Is_ARA": is_ara,
                    "Is_Booming": 1 if status == "🚀 BOOMING" else 0
                })
                # Simpan histori untuk grafik
                histories[s.replace(".JK", "")] = valid_data[['Close']]
            except: continue
    except:
        return pd.DataFrame(), {}
    
    if not results: return pd.DataFrame(), {}
    
    df = pd.DataFrame(results)
    df = df.sort_values(by=["Is_ARA", "Is_Booming", "Change (%)"], ascending=[True, False, False])
    return df, histories

# --- DASHBOARD UI ---
st.title("🚀 Provanch Scraper + Graph Analysis")
st.info("🔒 PERMANENT LOCK: Notif Ready & Refresh Features are Locked.")

placeholder = st.empty()

while True:
    now_wib = datetime.utcnow() + timedelta(hours=7)
    df, all_hist = get_data_and_history()

    with placeholder.container():
        col_table, col_graph = st.columns([2, 1])
        
        with col_table:
            st.subheader(f"Market List ({now_wib.strftime('%H:%M:%S')})")
            st.dataframe(df.drop(columns=[c for c in ['Is_ARA', 'Is_Booming'] if c in df.columns]), use_container_width=True)

        with col_graph:
            if not df.empty:
                top_1_name = df.iloc[0]['Saham']
                top_1_chg = df.iloc[0]['Change (%)']
                st.subheader(f"📊 Top 1: {top_1_name}")
                st.metric("Current Change", f"{top_1_chg}%")
                
                # Menampilkan Grafik Histori Harga Top 1
                if top_1_name in all_hist:
                    chart_data = all_hist[top_1_name]
                    st.line_chart(chart_data)
                    st.caption("Histori harga 5 menitan sejak pasar dibuka.")
            else:
                st.write("Menunggu data...")

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
