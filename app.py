import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Provanch Stock Scanner Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTable { background-color: #1e2130; border-radius: 10px; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Provanch Stock Intelligence")
st.write("Fungsi Utama: Scanner 10 Saham Terbaik < Rp 500 per Strategi")

# --- 2. SIDEBAR STRATEGY SELECTION ---
st.sidebar.header("🎯 Trading Strategy")
menu = st.sidebar.radio("Pilih Mode Analisa:", [
    "Scalping (Method A)", 
    "BSJP (Method B)", 
    "Day Trade (Method C)", 
    "Swing Trade (Method D)",
    "Gorengan Finder (Method G)"
])

# --- 3. ENGINE SCANNER (ANTI-KOSONG & AUTO-FILTER) ---
@st.cache_data(ttl=300)
def scan_stocks(mode):
    # Daftar universe saham di bawah 500 & likuid (IHSG)
    watchlist = [
        "GOTO.JK", "BUMI.JK", "ANTM.JK", "DOID.JK", "ELSA.JK", 
        "BRMS.JK", "ENRG.JK", "BUKA.JK", "ADMR.JK", "WIFI.JK",
        "AUTO.JK", "SMBR.JK", "PBSA.JK", "HAIS.JK", "MPXL.JK",
        "SMDR.JK", "MEDC.JK", "PGAS.JK", "PTBA.JK", "TINS.JK",
        "TLKM.JK", "ASII.JK", "BBRI.JK" # Ditambah buat variasi data
    ]
    
    results = []
    for s in watchlist:
        try:
            # Ambil data 30 hari terakhir
            d = yf.download(s, period="30d", progress=False)
            if not d.empty:
                # Perbaikan Multi-Index Kolom (Biar gak TypeError)
                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = d.columns.get_level_values(0)
                
                # Ambil data penutupan terakhir (Last Close)
                price = float(d['Close'].iloc[-1])
                
                # FILTER UTAMA: Harga harus dibawah 500
                if price > 500: continue 
                
                prev_c = float(d['Close'].iloc[-2])
                pct = ((price - prev_c) / prev_c) * 100
                vol = float(d['Volume'].iloc[-1])
                avg_vol = d['Volume'].mean()
                
                # LOGIKA FILTER PER MENU
                fit = False
                if mode == "Scalping (Method A)":
                    if pct > 0.5 and vol > (avg_vol * 0.8): fit = True
                elif mode == "BSJP (Method B)":
                    if price >= (d['High'].iloc[-1] * 0.97): fit = True # Close near High
                elif mode == "Day Trade (Method C)":
                    if pct > 0: fit = True
                elif mode == "Swing Trade (Method D)":
                    ma20 = d['Close'].rolling(20).mean().iloc[-1]
                    if price > ma20: fit = True # Uptrend
                elif mode == "Gorengan Finder (Method G)":
                    if vol > (avg_vol * 1.5): fit = True # Volume Spike

                if fit:
                    # KALKULASI HARGA OTOMATIS
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
                        "Change (%)": round(pct, 2)
                    })
        except:
            continue
        
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        # Sortir berdasarkan kenaikan tertinggi
        return df_res.sort_values(by="Change (%)", ascending=False).head(10)
    return pd.DataFrame()

# --- 4. TAMPILAN TABEL UTAMA ---
st.subheader(f"🚀 Top 10 Saham Terbaik - {menu}")
data_tabel = scan_stocks(menu)

if not data_tabel.empty:
    st.table(data_tabel.style.format({
        "Price": "Rp {:,.0f}", 
        "Entry": "Rp {:,.0f}", 
        "Stop Loss": "Rp {:,.0f}", 
        "Take Profit": "Rp {:,.0f}"
    }))
else:
    st.warning("⚠️ Sedang mencari data... Jika kosong, kemungkinan tidak ada saham < 500 yang sesuai kriteria strategi saat ini.")

# --- 5. AREA EDUKASI (LOCKED & DYNAMIC) ---
st.divider()
st.subheader("📚 Logika Analisa & Strategi")

if menu == "Scalping (Method A)":
    st.info("""
    **Analisa Scalping (Cuan Kilat):**
    * **Logika:** Mencari saham dengan volatilitas dan volume yang mulai 'bangun'.
    * **Tape Reading:** Wajib konfirmasi Bid/Offer di Stockbit. Pastikan Bid lebih tebal.
    * **Action:** Target profit 1-2%. Jangan hold kelamaan kalau harga stagnan.
    """)
elif menu == "BSJP (Method B)":
    st.info("""
    **Analisa BSJP (Beli Sore Jual Pagi):**
    * **Logika:** Mencari saham yang akumulasi di akhir sesi (14:30 - 14:50).
    * **Close near High:** Harga tutup harus kuat mendekati harga tertinggi hari ini.
    * **Action:** Jual saat pembukaan pasar besok (09:00 - 09:15) untuk ambil Gap Up.
    """)
elif menu == "Day Trade (Method C)":
    st.info("""
    **Analisa Day Trade:**
    * **Logika:** Mengikuti tren harian yang stabil.
    * **Rule:** Posisi harus Cash (sudah dijual) sebelum market tutup sore ini.
    * **Target:** Mencari profit di rentang 3-5% dalam satu hari perdagangan.
    """)
elif menu == "Swing Trade (Method D)":
    st.info("""
    **Analisa Swing Trade:**
    * **Logika:** Memanfaatkan gelombang tren menengah (Uptrend di atas MA20).
    * **Sabar:** Menahan posisi selama 3-14 hari sampai target tercapai.
    * **Risk:** Stop Loss lebih longgar (7%) untuk memberi ruang 'nafas' harga.
    """)
elif menu == "Gorengan Finder (Method G)":
    st.info("""
    **Analisa Method G (Speculative Meledak):**
    * **Logika:** Deteksi dini 'Volume Spike' (>1.5x rata-rata) pada saham yang harganya masih murah.
    * **Kunci:** Fokus pada saham yang baru mulai naik (Change 2-5%).
    * **Danger:** Risiko tinggi (ditarik lalu dibanting), wajib disiplin Cut Loss!
    """)
