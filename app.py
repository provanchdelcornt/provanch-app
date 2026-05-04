import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta

# ========================================================
# --- PERMANENT LOCK CONFIGURATION ---
# ========================================================
# STATUS: PERMANENT LOCK ACTIVE 🔒
REFRESH_INTERVAL = 30    
# ========================================================

st.set_page_config(page_title="Provanch 3.2 - Professional Dashboard", layout="wide")

# Sidebar - Strategi Selection
st.sidebar.header("⚙️ Strategy Selector")
trading_mode = st.sidebar.selectbox(
    "Pilih Metode:", 
    ["Scalping", "BSJP", "Day Trade", "Gorengan Finder (Method G)"]
)

def get_market_data(mode):
    tickers = ["PADI.JK", "GOTO.JK", "BUMI.JK", "BRMS.JK", "RAAM.JK", "TINS.JK", "ELSA.JK", "ENRG.JK", "ASRI.JK", "GZCO.JK", "WIFI.JK"]
    results, histories = [], {}
    
    try:
        data = yf.download(tickers, period="5d", interval="5m", group_by='ticker', threads=True, progress=False)
        for s in tickers:
            if s not in data or data[s].empty: continue
            valid_data = data[s].dropna()
            
            px = valid_data['Close'].iloc[-1]
            pc = data[s]['Open'].iloc[0]
            chg = ((px - pc) / pc) * 100
            vol_now = valid_data['Volume'].iloc[-1]
            vol_avg = valid_data['Volume'].mean()
            vwap = (valid_data['Close'] * valid_data['Volume']).sum() / valid_data['Volume'].sum()
            
            status, score = "⚪ MONITOR", chg

            if mode == "BSJP":
                power_15m = ((px - valid_data['Close'].iloc[-3]) / valid_data['Close'].iloc[-3]) * 100
                if px > vwap and power_15m > 0.4: status = "🔥 BSJP READY"
                score = power_15m + chg
            elif mode == "Day Trade":
                if px > vwap and chg > 1.5: status = "📈 TREND UP"
                score = chg
            elif mode == "Gorengan Finder (Method G)":
                vol_ratio = vol_now / vol_avg if vol_avg > 0 else 0
                if vol_ratio > 3.0 and 1.0 < chg < 6.0: status = "💥 MELEDAK"
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
                st.success(f"🎯 Target: {int(s_px * (1 + tp_p/100))}")
                st.error(f"🛑 Stop Loss: {int(s_px * (1 - sl_p/100))}")

        st.markdown("---")
        st.subheader(f"📑 Detail Analisa: {trading_mode}")
        if trading_mode == "Scalping":
            st.markdown("- **Tape Reading:** Dominasi **HAKA**.\n- **Indicator:** Harga > **VWAP**.\n- **Exit:** Cepat 1-3%.")
        elif trading_mode == "BSJP":
            st.markdown("- **Timing:** 14:30 - 14:50 WIB.\n- **Price Action:** **Close near High**.\n- **Goal:** Gap Up pagi.")
        elif trading_mode == "Day Trade":
            st.markdown("- **Momentum:** Breakout Opening Range.\n- **Rule:** Cash sebelum market tutup.")
        elif trading_mode == "Gorengan Finder (Method G)":
            st.markdown("- **Wake Up:** Saham tidur meledak.\n- **Volume:** Spike >3x rata-rata.\n- **Risk:** High Risk!")

    time.sleep(REFRESH_INTERVAL)
    st.rerun()
