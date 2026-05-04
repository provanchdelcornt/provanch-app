import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Provanch Stock Scanner", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Provanch Stock Intelligence")
st.subheader("Fungsi Utama: Scanner 10 Saham Terbaik < Rp 500")

# --- ENGINE DATA ---
@st.cache_data(ttl=300)
def get_top_under_500():
    # Daftar pantauan saham likuid & potensial gorengan/second liner
    watchlist = [
        "GOTO.JK", "BUMI.JK", "ANTM.JK", "DOID.JK", "ELSA.JK", 
        "BRMS.JK", "ENRG.JK", "BUKA.JK", "ADMR.JK", "WIFI.JK",
        "AUTO.JK", "SMBR.JK", "PBSA.JK", "HAIS.JK", "MPXL.JK"
    ]
    
    scanned_data = []
    for s in watchlist:
        try:
            d = yf.download(s, period="5d", progress=False)
            if not d.empty:
                if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
                price = float(d['Close'].iloc[-1])
                
                # FILTER UTAMA: Harga dibawah 500
                if price < 500:
                    prev_c = float(d['Close'].iloc[-2])
                    pct = ((price - prev_c) / prev_c) * 100
                    vol = float(d['Volume'].iloc[-1])
                    scanned_data.append({
                        "Ticker": s, 
                        "Price": price, 
                        "Change (%)": round(pct, 2), 
                        "Volume": vol
                    })
        except:
            continue
            
    # Sortir berdasarkan kenaikan (%) tertinggi (Terbaik)
    df_result = pd.DataFrame(scanned_data)
    if not df_result.empty:
        return df_result.sort_values(by="Change (%)", ascending=False).head(10)
    return pd.DataFrame()

# --- TAMPILAN SCANNER (FITUR UTAMA) ---
st.write("### 🚀 Top 10 Saham Terbaik (Dibawah Rp 500)")
top_df = get_top_under_500()
if not top_df.empty:
    st.table(top_df.style.format({"Price": "Rp {:,.0f}", "Volume": "{:,.0f}"}))
else:
    st.warning("Tidak ada saham dibawah 500 yang memenuhi kriteria saat ini.")

st.divider()

# --- FITUR ANALISA METHOD (ADDITIVE) ---
st.sidebar.header("🎯 Detailed Analysis")
menu = st.sidebar.selectbox("Pilih Method:", [
    "Scalping (Method A)", "BSJP (Method B)", 
    "Day Trade (Method C)", "Swing Trade (Method D)", 
    "Gorengan Finder (Method G)"
])
ticker_input = st.sidebar.text_input("Analisa Spesifik Ticker", "GOTO.JK").upper()

def get_detail_analysis(symbol):
    df = yf.download(symbol, period="60d", progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df['MA20'] = df['Close'].rolling(window=20).mean()
        return df
    return None

detail_df = get_detail_analysis(ticker_input)

if detail_df is not None:
    curr = float(detail_df['Close'].iloc[-1])
    
    # Logika Harga & Edukasi
    if menu == "Scalping (Method A)":
        entry, cl, tp = curr, curr * 0.98, curr * 1.02
        edu = "Scalping: Fokus Tape Reading & HAKA. VWAP wajib Bullish."
    elif menu == "Gorengan Finder (Method G)":
        entry, cl, tp = curr, curr * 0.97, curr * 1.10
        edu = "Method G: Speculative Meledak. Deteksi Volume > 3x rata-rata."
    else:
        entry, cl, tp = curr, curr * 0.97, curr * 1.05
        edu = "Analisa standar mode aktif."

    # Display Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current", f"Rp {curr:,.0f}")
    col2.metric("Entry", f"Rp {entry:,.0f}")
    col3.metric("Stop Loss", f"Rp {cl:,.0f}")
    col4.metric("Target", f"Rp {tp:,.0f}")
    
    st.info(f"**Edukasi:** {edu}")
    st.line_chart(detail_df[['Close', 'MA20']])
