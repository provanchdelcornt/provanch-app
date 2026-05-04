import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Provanch Stock Scanner Pro", layout="wide")

# CSS Custom untuk tampilan dark mode ala terminal pro
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTable { background-color: #1e2130; border-radius: 10px; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border-left: 5px solid #00ff00; }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Provanch Stock Intelligence")
st.write("Fungsi Utama: Scanner 10 Saham Terbaik < Rp 500 Berdasarkan Strategi")

# --- 2. SIDEBAR STRATEGY SELECTION ---
st.sidebar.header("🎯 Trading Strategy")
menu = st.sidebar.radio("Pilih Mode Analisa:", [
    "Scalping (Method A)", 
    "BSJP (Method B)", 
    "Day Trade (Method C)", 
    "Swing Trade (Method D)",
    "Gorengan Finder (Method G)"
])

# --- 3. ENGINE SCANNER (LOGIKA FILTRASI & STATUS) ---
@st.cache_data(ttl=300)
def scan_stocks(mode):
    # Universe saham di bawah 500 & likuid di IHSG
    watchlist = [
        "GOTO.JK", "BUMI.JK", "ANTM.JK", "DOID.JK", "ELSA.JK", 
        "BRMS.JK", "ENRG.JK", "BUKA.JK", "ADMR.JK", "WIFI.JK",
        "AUTO.JK", "SMBR.JK", "PBSA.JK", "HAIS.JK", "MPXL.JK",
        "SMDR.JK", "MEDC.JK", "PGAS.JK", "PTBA.JK", "TINS.JK",
        "TLKM.JK", "ASII.JK", "BBRI.JK", "WBNI.JK", "BDMN.JK"
    ]
    
    results = []
    for s in watchlist:
        try:
            # Ambil data 30 hari terakhir untuk kalkulasi status & indikator
            d = yf.download(s, period="30d", progress=False)
            if not d.empty:
                # Perbaikan Multi-Index Kolom agar tidak TypeError
                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = d.columns.get_level_values(0)
                
                # Data Point Penting
                price = float(d['Close'].iloc[-1])
                prev_c = float(d['Close'].iloc[-2])
                high_today = float(d['High'].iloc[-1])
                pct = ((price - prev_c) / prev_c) * 100
                vol = float(d['Volume'].iloc[-1])
                avg_vol = d['Volume'].mean()
                ma20 = d['Close'].rolling(20).mean().iloc[-1]
                
                # FILTER UTAMA: Harga harus dibawah 500
                if price > 500: continue 
                
                # LOGIKA PENENTUAN STATUS
                if price > ma20 * 1.02 and pct > 0:
                    status = "🔥 Gacor"
                elif abs(price - ma20) / ma20 < 0.02:
                    status = "↔️ Sideways"
                else:
                    status = "📉 Buruk"
                
                # LOGIKA FILTRASI BERDASARKAN MENU
                fit = False
                if mode == "Scalping (Method A)":
                    if pct > 0.5 and vol > (avg_vol * 0.8): fit = True
                elif mode == "BSJP (Method B)":
                    if price >= (high_today * 0.97): fit = True # Close Near High
                elif mode == "Day Trade (Method C)":
                    if pct > 0: fit = True
                elif mode == "Swing Trade (Method D)":
                    if price > ma20: fit = True # Uptrend MA20
                elif mode == "Gorengan Finder (Method G)":
                    if vol > (avg_vol * 1.5): fit = True # Volume Spike

                if fit:
                    # KALKULASI TARGET HARGA
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
                        "Status": status
                    })
        except:
            continue
        
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        # Sortir berdasarkan persentase kenaikan tertinggi
        return df_res.sort_values(by="Change (%)", ascending=False).head(10)
    return pd.DataFrame()

# --- 4. TAMPILAN TABEL UTAMA ---
st.subheader(f"🚀 Top 10 Saham Terbaik - {menu}")
data_tabel = scan_stocks(menu)

if not data_tabel.empty:
    # Formatting tabel agar angka rapi dan Change cuma 2 desimal
    st.table(data_tabel.style.format({
        "Price": "Rp {:,.0f}", 
        "Entry": "Rp {:,.0f}", 
        "Stop Loss": "Rp {:,.0f}", 
        "Take Profit": "Rp {:,.0f}",
        "Change (%)": "{:.2f}%"
    }))
else:
    st.warning("⚠️ Sedang mencari data yang sesuai... Jika tetap kosong, berarti tidak ada saham < 500 yang memenuhi kriteria strategi ini saat ini.")

# --- 5. AREA EDUKASI MENDALAM (LOGIKA & ANALISA) ---
st.divider()
st.subheader("📚 Logika Analisa & Strategi Mendalam")

if menu == "Scalping (Method A)":
    st.info("""
    ### ⚡ Method A: High Velocity Scalping
    **Logika Analisa:** Mencari 'Urgency' atau kecepatan transaksi. Kita mendeteksi saham yang baru bangun dari konsolidasi dengan volume mendadak.
    **Indikator:** Volume Spike wajib melampaui rata-rata. Harga naik minimal 1-2% sebagai konfirmasi HAKA.
    **Eksekusi:** Cek Bid/Offer di Stockbit. Pastikan Bid terus menebal. Target 1-3%, jika stagnan segera exit.
    """)

elif menu == "BSJP (Method B)":
    st.warning("""
    ### 🌙 Method B: BSJP (Beli Sore Jual Pagi)
    **Logika Analisa:** Memanfaatkan momentum Over-Night. Mencari saham yang diakumulasi Big Money menjelang tutup agar besok Gap Up.
    **Indikator:** Harga tutup (Close) harus berada di rentang 2-3% dari harga tertingginya (High) hari ini.
    **Eksekusi:** Masuk jam 14:40 - 14:55 WIB. Jual esok pagi di 15 menit pertama (09:00 - 09:15).
    """)

elif menu == "Day Trade (Method C)":
    st.success("""
    ### ☀️ Method C: Intraday Trend Following
    **Logika Analisa:** Berfokus pada kenaikan konsisten membentuk tangga naik (Higher High) sepanjang hari perdagangan.
    **Indikator:** Memilih saham dengan kenaikan 2-5% yang stabil dan berstatus 'Gacor' di atas MA20.
    **Eksekusi:** Beli saat pantulan (rebound). Wajib jual semua sebelum market tutup (No Overnight Risk).
    """)

elif menu == "Swing Trade (Method D)":
    st.write("""
    ### 🎢 Method D: Strategic Swing Trading
    **Logika Analisa:** Bermain pada tren besar. Mencari saham yang memantul dari area support atau garis Moving Average 20.
    **Indikator:** Wajib berstatus 'Gacor'. Kenaikan harus divalidasi dengan volume yang meningkat secara stabil.
    **Eksekusi:** Hold posisi 3 hari hingga 2 minggu. Gunakan Trailing Stop untuk menjaga keuntungan lo.
    """)

elif menu == "Gorengan Finder (Method G)":
    st.error("""
    ### 💣 Method G: Speculative Momentum (Gorengan Finder)
    **Logika Analisa:** Deteksi dini jejak kaki Bandar pada saham lapis tiga dengan anomali volume yang sangat ekstrem.
    **Indikator:** Volume Explosion minimal 2x rata-rata harian pada saham yang baru mulai bergerak naik dari dasar.
    **Eksekusi:** High Risk! Gunakan dana dingin. Wajib standby di monitor karena harga bisa dibanting dalam hitungan detik.
    """)
