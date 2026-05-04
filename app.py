import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- CONFIGURATION ---
st.set_page_config(page_title="Provanch Intelligence v3", layout="wide")

# CSS untuk styling agar user-friendly
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

ticker = st.sidebar.text_input("Kode Saham (Contoh: GOTO.JK)", "GOTO.JK").upper()

# --- ENGINE DATA ---
@st.cache_data(ttl=60)
def get_analysis_data(symbol):
    try:
        df = yf.download(symbol, period="60d", interval="1d")
        if not df.empty:
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['Avg_Vol_20'] = df['Volume'].rolling(window=20).mean()
            return df
    except:
        return None
    return None

df = get_analysis_data(ticker)

if df is not None and not df.empty:
    curr = float(df['Close'].iloc[-1])
    
    # --- LOGIKA HARGA & EDUKASI ---
    if menu == "Scalping (Method A)":
        entry, cl, tp = curr, curr * 0.98, curr * 1.02
        edu_text = """
        **Analisa Scalping (Cuan Kilat):**
        1. **Tape Reading:** Pantau Order Book. Bid harus lebih tebal dari Offer secara wajar.
        2. **Power of HAKA:** Masuk jika ada transaksi besar yang menghabiskan antrean Offer.
        3. **VWAP:** Harga wajib di atas garis VWAP harian.
        4. **Target:** 1% - 3% saja, jangan serakah.
        """

    elif menu == "BSJP (Method B)":
        entry, cl, tp = curr, curr * 0.985, curr * 1.03
        edu_text = """
        **Analisa BSJP (Beli Sore Jual Pagi):**
        1. **Timing:** Beli di menit terakhir (14:30 - 14:50 WIB).
        2. **Konfirmasi:** Harga penutupan harus dekat dengan harga tertinggi harian (Close near High).
        3. **Exit Strategi:** Jual di 15 menit pertama pasar buka besok (09:00 - 09:15 WIB).
        """

    elif menu == "Day Trade (Method C)":
        entry, cl, tp = curr, curr * 0.97, curr * 1.05
        edu_text = """
        **Analisa Day Trading:**
        1. **Opening Range:** Manfaatkan harga yang breakout dari konsolidasi pagi.
        2. **Momentum:** Gunakan chart 15m/30m untuk melihat tren harian.
        3. **Closing:** Semua posisi harus bersih (Cash) sebelum pasar tutup.
        """

    elif menu == "Swing Trade (Method D)":
        entry = float(df['MA20'].iloc[-1])
        cl, tp = entry * 0.93, entry * 1.15
        edu_text = """
        **Analisa Swing Trading:**
        1. **Structure:** Beli saat saham Uptrend (Higher High).
        2. **Garis Keramat:** Manfaatkan pantulan harga (Buy on Weakness) di area MA20.
        3. **Sabar:** Target 10% - 20% dalam hitungan minggu.
        """

    elif menu == "Gorengan Finder (Method G)":
        entry, cl, tp = curr, curr * 0.97, curr * 1.10
        vol_ratio = df['Volume'].iloc[-1] / df['Avg_Vol_20'].iloc[-1]
        edu_text = f"""
        **Analisa Method G (Speculative Meledak):**
        1. **Silent Accumulation:** Deteksi volume masif (>3x rata-rata).
        2. **Volume Ratio Saat Ini:** {vol_ratio:.2f}x.
        3. **Kunci:** Ikut saat tembok Offer dimakan habis oleh lot-lot besar (Bandar).
        """

    # --- TAMPILAN INTERFACE ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Harga Terkini", f"Rp {curr:,.0f}")
    m2.metric("🎯 Entry Point", f"Rp {entry:,.0f}")
    m3.metric("🔴 Stop Loss (CL)", f"Rp {cl:,.0f}")
    m4.metric("🟢 Take Profit (TP)", f"Rp {tp:,.0f}")

    st.write("---")
    st.markdown("### 📚 Logika & Edukasi Strategi")
    st.info(edu_text)
    
    st.subheader(f"Pergerakan Harga {ticker}")
    st.line_chart(df[['Close', 'MA20']])

else:
    st.error("Ticker tidak ditemukan atau data kosong.")
