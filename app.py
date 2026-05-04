import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Provanch Intelligence v3", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Provanch Stock Intelligence")

# --- SIDEBAR MENU ---
st.sidebar.header("🎯 Trading Method")
menu = st.sidebar.radio("Pilih Strategi:", [
    "Scalping (Method A)", 
    "BSJP (Method B)", 
    "Day Trade (Method C)", 
    "Swing Trade (Method D)",
    "Gorengan Finder (Method G)"
])

ticker = st.sidebar.text_input("Kode Saham", "GOTO.JK").upper()

# --- ENGINE DATA (PERHITUNGAN MANUAL) ---
@st.cache_data(ttl=60)
def get_data(symbol):
    try:
        df = yf.download(symbol, period="60d", interval="1d")
        if not df.empty:
            # Hitung MA20 manual tanpa pandas_ta
            df['MA20'] = df['Close'].rolling(window=20).mean()
            # Hitung Avg Vol 20 harian
            df['Avg_Vol_20'] = df['Volume'].rolling(window=20).mean()
            return df
    except:
        return None
    return None

df = get_data(ticker)

if df is not None and not df.empty:
    # Ambil harga terakhir (pastikan formatnya angka tunggal)
    curr = float(df['Close'].iloc[-1])
    
    # --- LOGIKA HARGA & EDUKASI ---
    if menu == "Scalping (Method A)":
        entry, cl, tp = curr, curr * 0.98, curr * 1.02
        edu = "Analisa Scalping: Fokus Tape Reading (Order Book) & Power of HAKA. VWAP wajib Bullish."
    elif menu == "BSJP (Method B)":
        entry, cl, tp = curr, curr * 0.985, curr * 1.03
        edu = "BSJP: Beli 14:30 - 14:50 WIB. Cari Close near High. Jual 09:00 - 09:15 besok pagi."
    elif menu == "Day Trade (Method C)":
        entry, cl, tp = curr, curr * 0.97, curr * 1.05
        edu = "Day Trade: Memanfaatkan Opening Range Breakout. Posisi harus Cash sebelum market tutup."
    elif menu == "Swing Trade (Method D)":
        entry = float(df['MA20'].iloc[-1])
        cl, tp = entry * 0.93, entry * 1.15
        edu = "Swing: Beli di area Support MA20 saat Uptrend. Target 10% - 20% hitungan minggu."
    elif menu == "Gorengan Finder (Method G)":
        entry, cl, tp = curr, curr * 0.97, curr * 1.10
        vol_r = float(df['Volume'].iloc[-1] / df['Avg_Vol_20'].iloc[-1])
        edu = f"Method G: Speculative Meledak. Vol Ratio saat ini: {vol_r:.2f}x (Target > 3x)."

    # --- TAMPILAN ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Harga Terkini", f"Rp {curr:,.0f}")
    m2.metric("🎯 Entry Point", f"Rp {entry:,.0f}")
    m3.metric("🔴 Stop Loss (CL)", f"Rp {cl:,.0f}")
    m4.metric("🟢 Take Profit (TP)", f"Rp {tp:,.0f}")

    st.info(f"**📚 Logika Strategi:** {edu}")
    st.subheader(f"Chart {ticker}")
    st.line_chart(df[['Close', 'MA20']])
else:
    st.error("Ticker salah atau data kosong, Ky.")
