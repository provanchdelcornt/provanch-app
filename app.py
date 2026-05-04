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
# ========================================================

st.set_page_config(page_title="Provanch 3.1 - Hybrid Scanner", layout="wide")

# Sidebar untuk Ganti Mode
st.sidebar.header("⚙️ Mode Selection")
trading_mode = st.sidebar.selectbox("Pilih Strategi:", ["Scalping (Day Trading)", "BSJP (Beli Sore Jual Pagi)"])

# Settingan Parameter berdasarkan Mode
if trading_mode == "BSJP (Beli Sore Jual Pagi)":
    TP_PCT, SL_PCT = 2.0, 1.5
    st.sidebar.info("Mode BSJP: Fokus pada akumulasi akhir sesi.")
else:
    TP_PCT, SL_PCT = 2.5, 1.8
    st.sidebar.info("Mode Scalping: Fokus pada volatilitas harga.")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

def get_market_data(mode):
    tickers = ["PADI.JK", "GOTO.JK", "BUMI.JK", "BRMS.JK", "RAAM.JK", "TINS.JK", "ELSA.JK", "ENRG.JK", "ASRI.JK", "GZCO.JK", "WIFI.JK", "BSJP.JK"]
    results, histories = [], {}
    
    try:
        data = yf.download(tickers, period="1d", interval="5m", group_by='ticker', threads=True, progress=False)
        for s in tickers:
            if s not in data or data[s].empty: continue
            valid_data = data[s].dropna()
            if valid_data.empty: continue
            
            px = valid_data['Close'].iloc[-1]
            pc = data[s]['Open'].iloc[0]
            avg_price = valid_data['Close'].mean()
            chg = ((px - pc) / pc) * 100 
            
            # Logika Khusus BSJP (Power Score)
            power_15m = 0
            if len(valid_data) >= 3:
                power_15m = ((px - valid_data['Close'].iloc[-3]) / valid_data['Close'].iloc[-3]) * 100

            status = "📈 STABLE"
            score = chg
            
            if mode == "BSJP (Beli Sore Jual Pagi)":
                if px > avg_price and power_15m > 0.4: status = "🔥 BSJP READY"
                score = power_15m + chg
            else:
                if px > avg_price and chg > 2.5: status = "🚀 BOOMING"
                score = chg

            results.append({
                "Saham": s.replace(".JK", ""), "Harga": int(px), 
                "Power(15m)": round(power_15m, 2), "Change(%)": round(chg, 2), 
                "Status": status, "Score": score
            })
            histories[s.replace(".JK", "")] = valid_data[['Close']]
            
    except: return pd.DataFrame(), {}
    
    df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
    return df, histories

# --- UI DASHBOARD ---
st.title(f"🚀 Provanch - {trading_mode}")
st.info("🔒 Status: Notif Ready & Refresh Features Locked.")

placeholder = st.empty()

while True:
    now_wib = datetime.utcnow() + timedelta(hours=7)
    df, all_hist = get_market_data(trading_mode)

    with placeholder.container():
        col_list, col_analysis = st.columns([2, 1])
        with col_list:
            st.subheader(f"Scanner List ({now_wib.strftime('%H:%M:%S')})")
            st.dataframe(df.drop(columns=['Score']), use_container_width=True)
            if not df.empty:
                st.line_chart(all_hist[df.iloc[0]['Saham']])

        with col_analysis:
            if not df.empty:
                s_name, s_px = df.iloc[0]['Saham'], df.iloc[0]['Harga']
                st.subheader("🛒 Order Planner (300k)")
                tp_val = int(s_px * (1 + (TP_PCT/100)))
                cl_val = int(s_px * (1 - (SL_PCT/100)))
                st.success(f"🎯 Target Jual: {tp_val}")
                st.error(f"🛑 Batas CL: {cl_val}")
                st.info(f"📦 Beli: {int(300000 / (s_px * 100))} Lot")

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
