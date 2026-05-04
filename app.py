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

st.set_page_config(page_title="Provanch 3.2 - Dynamic Hybrid Scanner", layout="wide")

# Sidebar - Strategi Selection
st.sidebar.header("⚙️ Strategy Selector")
trading_mode = st.sidebar.selectbox(
    "Pilih Metode:", 
    ["Scalping", "BSJP", "Day Trade", "Gorengan Finder (Method G)"]
)

# 🔒 FEATURE LOCKED: Notif Ready
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def get_market_data(mode):
    tickers = ["PADI.JK", "GOTO.JK", "BUMI.JK", "BRMS.JK", "RAAM.JK", "TINS.JK", "ELSA.JK", "ENRG.JK", "ASRI.JK", "GZCO.JK", "WIFI.JK"]
    results, histories = [], {}
    
    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
        for s in tickers:
            if s not in data or data[s].empty: continue
            valid_data = data[s].dropna()
            if len(valid_data) < 10: continue
            
            px = valid_data['Close'].iloc[-1]
            pc = data[s]['Open'].iloc[0]
            chg = ((px - pc) / pc) * 100
            vol_now = valid_data['Volume'].iloc[-1]
            vol_avg = valid_data['Volume'].mean()
            vwap = (valid_data['Close'] * valid_data['Volume']).sum() / valid_data['Volume'].sum()
            
            status, score = "⚪ MONITOR", chg

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
                score = vol_ratio
            else: # Scalping
                if px > vwap and chg > 2.0: status = "🚀 SCALP"
                score = chg

            results.append({"Saham": s.replace(".JK", ""), "Harga": int(px), "Chg%": round(chg, 2), "Status": status, "Score": score})
            histories[s.replace(".JK", "")] = valid_data[['Close']]
            
    except: return pd.DataFrame(), {}
    return pd.DataFrame(results).sort_values(by="Score", ascending=False), histories

# --- UI DASHBOARD ---
st.title(f"🚀 Provanch v3.2 - {trading_mode}")
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
            if not df.empty: st.line_chart(all_hist[df.iloc[0]['Saham']])
        with c2:
            if not df.empty:
                s_name, s_px = df.iloc[0]['Saham'], df.iloc[0]['Harga']
                tp_p = 2.0 if trading_mode in ["Scalping", "BSJP"] else (4.0 if trading_mode == "Day Trade" else 7.0)
                sl_p = 1.5 if trading_mode in ["Scalping", "BSJP"] else (2.0 if trading_mode == "Day Trade" else 3.0)
                st.subheader(f"Plan: {s_name}")
                st.metric("Price", f"Rp {s_px}")
                st.success(f"🎯 Take Profit: {int(s_px * (1 + tp_p/100))}")
                st.error(f"🛑 Stop Loss: {int(s_px * (1 - sl_p/100))}")

        # --- DYNAMIC ANALYSIS FOOTER ---
        st.markdown("---")
        st.subheader(f"📑 Detail Analisa: {trading_mode}")
        
        if trading_mode == "Scalping":
            st.markdown("""
            - **Tape Reading:** Fokus pada dominasi **HAKA** (Hajar Kanan). Cari antrean Bid yang tebal namun wajar.
            - **Indicator:** Harga wajib di atas **VWAP** dan menempel di **EMA 9/13**.
            - **Exit Strategy:** Target profit 1-3% dalam hitungan menit. Cut loss ketat jika harga menembus support.
            - **Golden Hours:** Efektif pada pukul 09:00 - 10:00 WIB.
            """)
        
        elif trading_mode == "BSJP":
            st.markdown("""
            - **Timing:** Analisa dilakukan pada pukul **14:30 - 14:50 WIB**.
            - **Price Action:** Mencari saham dengan kondisi **Close near High** (tutup di harga tertinggi).
            - **Volume:** Harus ada akumulasi/lonjakan volume di akhir sesi perdagangan.
            - **Tujuan:** Menangkap **Gap Up** (loncat harga) saat pembukaan pasar besok pagi pukul 09:00.
            """)
            
        elif trading_mode == "Day Trade":
            st.markdown("""
            - **Timeframe:** Mengamati pergerakan dalam rentang 15 - 30 menit.
            - **Analisa:** Mencari momentum **Breakout** dari rentang harga pembukaan (Opening Range).
            - **Indicator:** Menggunakan **RSI** untuk melihat kejenuhan dan **VWAP** sebagai konfirmasi tren harian.
            - **Rule:** Semua posisi harus sudah dijual (*cash*) sebelum pasar tutup sore ini.
            """)
            
        elif trading_mode == "Gorengan Finder (Method G)":
            st.markdown("""
            - **Bandarmology:** Mendeteksi fase **Wake Up** (saham tidur yang mulai bergerak).
            - **Volume Spike:** Filter otomatis mencari volume yang meledak **>3x rata-rata harian**.
            - **Price Range:** Mencari kenaikan awal (antara 1% - 6%). Jangan kejar jika sudah naik terlalu tinggi (>10%).
            - **High Risk:** Wajib disiplin! Langsung keluar jika 'tembok' Bid penjaga roboh.
            """)

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
