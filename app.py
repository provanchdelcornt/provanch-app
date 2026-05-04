import streamlit as st
import yfinance as yf
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Provanch Stock Scanner", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTable { background-color: #1e2130; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Provanch Stock Intelligence")

# --- SIDEBAR MENU ---
st.sidebar.header("🎯 Trading Strategy")
menu = st.sidebar.radio("Pilih Mode:", [
    "Scalping (Method A)", 
    "BSJP (Method B)", 
    "Day Trade (Method C)", 
    "Swing Trade (Method D)",
    "Gorengan Finder (Method G)"
])

# --- ENGINE SCANNER ---
@st.cache_data(ttl=300)
def scan_top_10(mode):
    # Daftar universe saham di bawah 500 & likuid
    watchlist = [
        "GOTO.JK", "BUMI.JK", "ANTM.JK", "DOID.JK", "ELSA.JK", 
        "BRMS.JK", "ENRG.JK", "BUKA.JK", "ADMR.JK", "WIFI.JK",
        "AUTO.JK", "SMBR.JK", "PBSA.JK", "HAIS.JK", "MPXL.JK",
        "SMDR.JK", "MEDC.JK", "PGAS.JK", "PTBA.JK", "TINS.JK"
    ]
    
    results = []
    for s in watchlist:
        try:
            d = yf.download(s, period="20d", progress=False)
            if not d.empty:
                if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
                
                price = float(d['Close'].iloc[-1])
                # Filter Utama: Harga di bawah 500
                if price > 500: continue 
                
                prev_c = float(d['Close'].iloc[-2])
                pct = ((price - prev_c) / prev_c) * 100
                vol = float(d['Volume'].iloc[-1])
                avg_vol = d['Volume'].mean()
                
                # Logika Spesifik Per Menu
                fit = False
                if mode == "Scalping (Method A)" and pct > 1 and vol > avg_vol: fit = True
                elif mode == "BSJP (Method B)" and price >= d['High'].iloc[-1] * 0.98: fit = True
                elif mode == "Day Trade (Method C)" and pct > 0: fit = True
                elif mode == "Swing Trade (Method D)" and price > d['Close'].rolling(20).mean().iloc[-1]: fit = True
                elif mode == "Gorengan Finder (Method G)" and vol > (avg_vol * 2): fit = True
                
                if fit:
                    # Kalkulasi Harga Otomatis
                    if mode == "Scalping (Method A)": entry, cl, tp = price, price * 0.98, price * 1.02
                    elif mode == "BSJP (Method B)": entry, cl, tp = price, price * 0.985, price * 1.03
                    elif mode == "Day Trade (Method C)": entry, cl, tp = price, price * 0.97, price * 1.05
                    elif mode == "Swing Trade (Method D)": entry, cl, tp = price, price * 0.93, price * 1.15
                    else: entry, cl, tp = price, price * 0.97, price * 1.10
                    
                    results.append({
                        "Ticker": s,
                        "Price": price,
                        "Entry": entry,
                        "Stop Loss": cl,
                        "Take Profit": tp,
                        "Change (%)": round(pct, 2)
                    })
        except: continue
        
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        return df_res.sort_values(by="Change (%)", ascending=False).head(10)
    return pd.DataFrame()

# --- TAMPILAN TABEL ---
st.subheader(f"🚀 Top 10 Saham Terbaik - {menu}")
data_tabel = scan_top_10(menu)

if not data_tabel.empty:
    st.table(data_tabel.style.format({
        "Price": "Rp {:,.0f}", 
        "Entry": "Rp {:,.0f}", 
        "Stop Loss": "Rp {:,.0f}", 
        "Take Profit": "Rp {:,.0f}"
    }))
else:
    st.warning("Tidak ada saham yang memenuhi kriteria untuk mode ini saat ini.")

# --- AREA EDUKASI (LOCKED) ---
st.divider()
st.subheader("📚 Logika Analisa & Strategi")

if menu == "Scalping (Method A)":
    st.info("""
    **Analisa Scalping:** Fokus pada volatilitas tinggi dan volume masif. 
    * Mencari saham yang sedang 'running' dengan volume di atas rata-rata.
    * Target cuan tipis (1-2%) tapi frekuensi tinggi. 
    * Pantau HAKA di Stockbit segera setelah ticker muncul di sini.
    """)
elif menu == "BSJP (Method B)":
    st.info("""
    **Analisa BSJP:** Mencari saham yang ditutup kuat (Close near High). 
    * Logikanya: Jika sore ini kuat, kemungkinan besar besok pagi akan 'Gap Up' (loncat harga).
    * Jual di 15 menit pertama pasar buka besok pagi.
    """)
elif menu == "Day Trade (Method C)":
    st.info("""
    **Analisa Day Trade:** Memanfaatkan tren satu hari penuh. 
    * Saham yang dipilih adalah yang memiliki momentum kenaikan stabil sejak pagi.
    * Wajib cash out (jual semua) sebelum market tutup sore ini.
    """)
elif menu == "Swing Trade (Method D)":
    st.info("""
    **Analisa Swing Trade:** Mencari saham di atas MA20 (Uptrend). 
    * Fokus pada ketahanan tren beberapa hari.
    * Target profit lebih lebar dengan Stop Loss yang lebih longgar.
    """)
elif menu == "Gorengan Finder (Method G)":
    st.info("""
    **Analisa Method G:** Mencari saham 'tidur' yang tiba-tiba volumenya meledak > 2x lipat. 
    * Ini adalah deteksi dini pergerakan bandar (Mark Up).
    * Spekulasi tinggi, wajib disiplin Stop Loss!
    """)
