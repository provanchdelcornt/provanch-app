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

st.set_page_config(page_title="Provanch 3.2 - Hybrid Scanner", layout="wide")

# Sidebar - Strategi Selection
st.sidebar.header("⚙️ Strategy Selector")
trading_mode = st.sidebar.selectbox(
    "Pilih Metode:", 
    ["Scalping", "BSJP", "Day Trade", "Gorengan Finder (Method G)"]
)

# Pengaturan Parameter Otomatis Berdasarkan Strategi
if trading_mode == "BSJP":
    TP_PCT, SL_PCT = 2.0, 1.5
    desc = "Fokus akumulasi sore (14:30) untuk Gap Up pagi."
elif trading_mode == "Day Trade":
    TP_PCT, SL_PCT = 4.0, 2.0
    desc = "Fokus momentum harian di atas VWAP."
elif trading_mode == "Gorengan Finder (Method G)":
    TP_PCT, SL_PCT = 7.0, 3.0
    desc = "Deteksi saham 'tidur' yang mulai bangun (Volume Spike)."
else: # Scalping
    TP_PCT, SL_PCT = 2.0, 1.5
    desc = "Fokus volatilitas cepat dan HAKA."

st.sidebar.info(f"**Mode {trading_mode}:** {desc}")

# 🔒 FEATURE LOCKED: Notif Ready
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def get_market_data(mode):
    # List saham gorengan & lq45 campuran untuk testing
    tickers = ["PADI.JK", "GOTO.JK", "BUMI.JK", "BRMS.JK", "RAAM.JK", "TINS.JK", "ELSA.JK", "ENRG.JK", "ASRI.JK", "GZCO.JK", "WIFI.JK"]
    results, histories = [], {}
    
    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
        
        for s in tickers:
            if s not in data or data[s].empty: continue
            valid_data = data[s].dropna()
            if len(valid_data) < 10: continue
            
            # Data Point
            px = valid_data['Close'].iloc[-1]
            pc = data[s]['Open'].iloc[0]
            chg = ((px - pc) / pc) * 100
            vol_now = valid_data['Volume'].iloc[-1]
            vol_avg = valid_data['Volume'].mean()
            vwap = (valid_data['Close'] * valid_data['Volume']).sum() / valid_data['Volume'].sum()
            
            status = "⚪ MONITOR"
            score = chg

            # --- LOGIC SELECTION (ADDITIVE METHODS) ---
            if mode == "BSJP":
                power_15m = ((px - valid_data['Close'].iloc[-3]) / valid_data['Close'].iloc[-3]) * 100
                if px > vwap and power_15m > 0.3: status = "🔥 BSJP READY"
                score = power_15m + chg

            elif mode == "Day Trade":
                if px > vwap and chg > 1.5: status = "📈 TREND UP"
                score = chg

            elif mode == "Gorengan Finder (Method G)":
                vol_ratio = vol_now / vol_avg if vol_avg > 0 else 0
                if vol_ratio > 3.0 and 1.0 < chg < 6.0: 
                    status = "💥 MELEDAK"
                    send_telegram(f"⚠️ **GORENGAN ALERT!**\nSaham: {s}\nVol Ratio: {round(vol_ratio,1)}x")
                score = vol_ratio

            else: # Scalping
                if px > vwap and chg > 2.0: status = "🚀 SCALP"
                score = chg

            results.append({
                "Saham": s.replace(".JK", ""), "Harga": int(px), 
                "Chg%": round(chg, 2), "Status": status, "Score": score
            })
            histories[s.replace(".JK", "")] = valid_data[['Close']]
            
    except: return pd.DataFrame(), {}
    
    df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
    return df, histories

# --- UI DASHBOARD ---
st.title(f"🚀 Provanch v3.2 - {trading_mode}")
st.write(f"Sistem deteksi otomatis menggunakan algoritma **Method A-G**.")

placeholder = st.empty()

# 🔒 FEATURE LOCKED: Refresh Logic
while True:
    now_wib = datetime.utcnow() + timedelta(hours=7)
    df, all_hist = get_market_data(trading_mode)

    with placeholder.container():
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader(f"Scanner List ({now_wib.strftime('%H:%M:%S')})")
            st.dataframe(df.drop(columns=['Score']), use_container_width=True)
            if not df.empty:
                st.line_chart(all_hist[df.iloc[0]['Saham']])
        
        with c2:
            if not df.empty:
                s_name, s_px = df.iloc[0]['Saham'], df.iloc[0]['Harga']
                st.subheader(f"Plan: {s_name}")
                st.metric("Price", f"Rp {s_px}")
                st.success(f"🎯 Take Profit: {int(s_px * (1 + TP_PCT/100))}")
                st.error(f"🛑 Stop Loss: {int(s_px * (1 - SL_PCT/100))}")

        # --- PENJELASAN ANALISA (FOOTER) ---
        st.markdown("---")
        st.subheader("📝 Ringkasan Analisa Strategi")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.write("**Scalping & Day Trade**")
            st.caption("Fokus pada harga di atas VWAP dan momentum HAKA. Scalping keluar dalam hitungan menit, Day Trade sebelum market tutup.")
        
        with col_b:
            st.write("**BSJP (Beli Sore Jual Pagi)**")
            st.caption("Mencari akumulasi di jam 14:30. Syarat utama: Harga 'Close near High' untuk mengejar Gap Up saat open besok pagi.")
            
        with col_c:
            st.write("**Gorengan Finder (Method G)**")
            st.caption("Mendeteksi Volume Spike > 3x rata-rata pada saham yang baru 'bangun'. Disiplin Stop Loss ketat sangat wajib di sini!")

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
