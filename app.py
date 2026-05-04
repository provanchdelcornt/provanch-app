import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURATION UI ---
st.set_page_config(page_title="Provanch Stock Analyzer", layout="wide")
st.title("📈 Provanch Stock Analysis")
st.subheader("Bot 1: Khusus Analisa Teknikal & Data Saham")

# --- SIDEBAR INPUT ---
ticker = st.sidebar.text_input("Masukkan Kode Saham (Contoh: GOTO.JK, BBCA.JK)", "GOTO.JK")
period = st.sidebar.selectbox("Periode Data", ("1mo", "3mo", "6mo", "1y", "max"))

# --- PROSES AMBIL DATA ---
try:
    data = yf.download(ticker, period=period)
    
    if not data.empty:
        # Kalkulasi MA sederhana untuk bantu day trade
        data['MA20'] = data['Close'].rolling(window=20).mean()
        
        # Tampilan Grafik Utama
        st.line_chart(data[['Close', 'MA20']])
        
        # Kolom Statistik
        col1, col2, col3 = st.columns(3)
        last_price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        change = ((last_price - prev_price) / prev_price) * 100
        
        col1.metric("Harga Terakhir", f"Rp {last_price:,.0f}", f"{change:.2f}%")
        col2.metric("Volume", f"{data['Volume'].iloc[-1]:,.0f}")
        col3.metric("Highest (Period)", f"Rp {data['High'].max():,.0f}")

        # Tabel Data
        st.write("### Data Historis Terakhir")
        st.dataframe(data.tail(10))
        
    else:
        st.error("Data tidak ditemukan. Pastikan kode saham benar (pakai .JK untuk IHSG).")

except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")

# Footer tetap bersih tanpa kodingan Telegram
st.divider()
st.caption("Provanch Stock Analysis System v1.0")
