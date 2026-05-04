import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Provanch Stock Scanner Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTable { background-color: #1e2130; border-radius: 10px; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Provanch Stock Intelligence")

# --- 2. SIDEBAR STRATEGY SELECTION ---
st.sidebar.header("🎯 Trading Strategy")
menu = st.sidebar.radio("Pilih Mode Analisa:", [
    "Scalping (Method A)", 
    "BSJP (Method B)", 
    "Day Trade (Method C)", 
    "Swing Trade (Method D)",
    "Gorengan Finder (Method G)"
])

# --- 3. ENGINE SCANNER ---
@st.cache_data(ttl=300)
def scan_stocks(mode):
    watchlist = [
        "GOTO.JK", "BUMI.JK", "ANTM.JK", "DOID.JK", "ELSA.JK", 
        "BRMS.JK", "ENRG.JK", "BUKA.JK", "ADMR.JK", "WIFI.JK",
        "AUTO.JK", "SMBR.JK", "PBSA.JK", "HAIS.JK", "MPXL.JK",
        "SMDR.JK", "MEDC.JK", "PGAS.JK", "PTBA.JK", "TINS.JK",
        "TLKM.JK", "ASII.JK", "BBRI.JK"
    ]
    
    results = []
    for s in watchlist:
        try:
            d = yf.download(s, period="30d", progress=False)
            if not d.empty:
                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = d.columns.get_level_values(0)
                
                price = float(d['Close'].iloc[-1])
                if price > 500: continue 
                
                prev_c = float(d['Close'].iloc[-2])
                pct = ((price - prev_c) / prev_c) * 100
                vol = float(d['Volume'].iloc[-1])
                avg_vol = d['Volume'].mean()
                ma20 = d['Close'].rolling(20).mean().iloc[-1]
                
                # LOGIKA STATUS
                if price > ma20 * 1.02 and pct > 0:
                    status = "🔥 Gacor"
                elif abs(price - ma20) / ma20 < 0.02:
                    status = "↔️ Sideways"
                else:
                    status = "📉 Buruk"
                
                # LOGIKA FILTER PER MENU
                fit = False
                if mode == "Scalping (Method A)":
                    if pct > 0.5 and vol > (avg_vol * 0.8): fit = True
                elif mode == "BSJP (Method B)":
                    if price >= (d['High'].iloc[-1] * 0.97): fit = True
                elif mode == "Day Trade (Method C)":
                    if pct > 0: fit = True
                elif mode == "Swing Trade (Method D)":
                    if price > ma20: fit = True
                elif mode == "Gorengan Finder (Method G)":
                    if vol > (avg_vol * 1.5): fit = True

                if fit:
                    # KALKULASI HARGA
                    if mode == "Scalping (Method A)": entry, cl, tp = price, price * 0.98, price * 1.02
                    elif mode == "BSJP (Method B)": entry, cl, tp = price, price * 0.985, price * 1.03
                    elif mode == "Day Trade (Method C)": entry, cl, tp = price, price * 0.97, price * 1.05
                    elif mode == "Swing Trade (Method D)": entry, cl, tp = price, price * 0.93, price * 1.15
                    else: entry, cl, tp = price, price * 0.97, price * 1.10
                    
                    results.append({
                        "Ticker": s,
                        "Price": price,
                        "Entry": entry,
                        "Stop Loss": round(cl, 0),
                        "Take Profit": round(tp, 0),
                        "Change (%)": round(pct, 2),
                        "Status": status # KOLOM STATUS BARU
                    })
        except: continue
        
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        # Urutkan biar yang Gacor naik ke atas
        return df_res.sort_values(by="Change (%)", ascending=False).head(10)
    return pd.DataFrame()

# --- 4. TAMPILAN TABEL ---
st.subheader(f"🚀 Top 10 Saham Terbaik - {menu}")
data_tabel = scan_stocks(menu)

if not data_tabel.empty:
    st.table(data_tabel.style.format({
        "Price": "Rp {:,.0f}", 
        "Entry": "Rp {:,.0f}", 
        "Stop Loss": "Rp {:,.0f}", 
        "Take Profit": "Rp {:,.0f}",
        "Change (%)": "{:.2f}%"
    }))
else:
    st.warning("⚠️ Data belum tersedia. Tunggu sebentar atau ganti strategi.")

# --- 5. AREA EDUKASI ---
st.divider()
st.subheader("📚 Logika Analisa & Strategi")
if menu == "Scalping (Method A)":
    st.info("**Scalping:** Fokus volatilitas dan volume. Target 1-2%.")
elif menu == "BSJP (Method B)":
    st.info("**BSJP:** Beli sore (14:30-14:50). Jual besok pagi (09:00-09:15).")
elif menu == "Day Trade (Method C)":
    st.info("**Day Trade:** Ikuti tren harian. Wajib Cash Out sebelum market tutup.")
elif menu == "Swing Trade (Method D)":
    st.info("**Swing Trade:** Tren menengah di atas MA20. Hold 3-14 hari.")
elif menu == "Gorengan Finder (Method G)":
    st.info("**Method G:** Deteksi Volume Spike > 1.5x. Fokus saham murah baru mulai naik.")
