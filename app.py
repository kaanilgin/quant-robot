import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import json
import os
import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v5.1 - Mega Tarayıcı", layout="wide")

# --- DOSYA YÖNETİMİ (HAFIZA SİSTEMİ) ---
DOSYA_ADI = "robot_cuzdan.json"

def verileri_yukle():
    if os.path.exists(DOSYA_ADI):
        try:
            with open(DOSYA_ADI, "r") as f:
                return json.load(f)
        except:
            return None
    return None

def verileri_kaydet(bakiye, portfoy, islem_gecmisi):
    veri = {
        "bakiye": bakiye,
        "portfoy": portfoy,
        "islem_gecmisi": islem_gecmisi
    }
    with open(DOSYA_ADI, "w") as f:
        json.dump(veri, f)

# --- BAŞLANGIÇ AYARLARI (SESSION STATE) ---
kayitli_veri = verileri_yukle()

if 'bakiye' not in st.session_state:
    st.session_state['bakiye'] = kayitli_veri["bakiye"] if kayitli_veri else 100000.0
if 'portfoy' not in st.session_state:
    st.session_state['portfoy'] = kayitli_veri["portfoy"] if kayitli_veri else {}
if 'islem_gecmisi' not in st.session_state:
    st.session_state['islem_gecmisi'] = kayitli_veri["islem_gecmisi"] if kayitli_veri else []
if 'tarama_sonuclari' not in st.session_state:
    st.session_state['tarama_sonuclari'] = None

# --- FONKSİYONLAR ---
@st.cache_data
def veri_getir(sembol, periyot="1y"):
    denenecekler = [sembol, sembol.upper(), sembol.upper().replace('.IS', '.is'), sembol.lower()]
    for s in denenecekler:
        try:
            df = yf.download(s, period=periyot, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
        except: continue
    return None

def z_score_hesapla(df, window):
    df['SMA'] = df['Close'].rolling(window=window).mean()
    df['STD'] = df['Close'].rolling(window=window).std()
    df['Z_Score'] = (df['Close'] - df['SMA']) / df['STD']
    return df

def monte_carlo_simulasyon(df, gun_sayisi=90, sim_sayisi=200):
    getiriler = df['Close'].pct_change().dropna()
    mu, sigma = getiriler.mean(), getiriler.std()
    son_fiyat = df['Close'].iloc[-1]
    sim_df = pd.DataFrame()
    for x in range(sim_sayisi):
        fiyatlar = [son_fiyat]
        for i in range(gun_sayisi):
            fiyatlar.append(fiyatlar[-1] * (1 + np.random.normal(mu, sigma)))
        sim_df[f"Senaryo {x}"] = fiyatlar
    return sim_df

# --- SOL MENÜ ---
st.sidebar.header("⚙️ Ayarlar")
window = st.sidebar.slider("Ortalama (SMA) Günü", 10, 200, 50, 5)
z_threshold = st.sidebar.slider("Al/Sat Hassasiyeti", 1.0, 3.0, 2.0, 0.1)
st.sidebar.info("v5.1 - BIST 100 + Global Liste Eklendi 🌍")

# --- ANA EKRAN ---
st.title("💎 Ultimate Quant Terminali")
tab1, tab2, tab3, tab4 = st.tabs(["📊 Detaylı Analiz", "📡 Mega Tarayıcı", "🎲 Gelecek", "🤖 Canlı Trader"])

# ==========================
# SEKME 1: DETAYLI ANALİZ
# ==========================
with tab1:
    st.subheader("Tekli Hisse Analizi")
    s_in = st.text_input("Sembol:", value="THYAO.IS", key="t1")
    if s_in:
        df = veri_getir(s_in)
        if df is not None:
            df = z_score_hesapla(df, window)
            last_z = df['Z_Score'].iloc[-1]
            last_p = df['Close'].iloc[-1]
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Fiyat", f"{last_p:.2f}")
            c2.metric("Z-Score", f"{last_z:.2f}")
            
            durum = "NÖTR"
            if last_z < -z_threshold: durum = "🟢 UCUZ (AL)"
            elif last_z > z_threshold: durum = "🔴 PAHALI (SAT)"
            c3.metric("Sinyal", durum)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df.index, df['Z_Score'], label='Z-Score', color='blue', linewidth=1.5)
            ax.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.7)
            ax.axhline(z_threshold, color='red', linestyle='--', label='Pahalı')
            ax.axhline(-z_threshold, color='green', linestyle='--', label='Ucuz')
            ax.fill_between(df.index, z_threshold, df['Z_Score'], where=(df['Z_Score'] > z_threshold), color='red', alpha=0.2)
            ax.fill_between(df.index, -z_threshold, df['Z_Score'], where=(df['Z_Score'] < -z_threshold), color='green', alpha=0.2)
            ax.legend()
            ax.set_title(f"{s_in.upper()} Gerginlik Analizi")
            st.pyplot(fig)
        else:
            st.error("Veri bulunamadı.")

# ==========================
# SEKME 2: MEGA TARAYICI (100+ VARLIK) 🚀
# ==========================
with tab2:
    st.subheader("📡 Piyasa Tarayıcısı (BIST 100 + Kripto + Emtia)")
    
    # DEV LİSTE
    takip_listesi = [
        # --- BIST 30 & LOKOMOTİFLER ---
        'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'ISCTR.IS', 'YKBNK.IS', 'VAKBN.IS', 'HALKB.IS', 'TSKB.IS', 'SKBNK.IS',
        'EREGL.IS', 'KRDMD.IS', 'ISDMR.IS', 'TUPRS.IS', 'PETKM.IS', 'ASELS.IS', 'SISE.IS', 'SASA.IS', 'HEKTS.IS',
        'KCHOL.IS', 'SAHOL.IS', 'DOHOL.IS', 'ENKAI.IS', 'TEKFEN.IS', 'ALARK.IS', 'TKFEN.IS', 'GSDHO.IS',
        'BIMAS.IS', 'MGROS.IS', 'SOKM.IS', 'AEFES.IS', 'CCOLA.IS', 'ULKER.IS', 'TUKAS.IS',
        'FROTO.IS', 'TOASO.IS', 'TTRAK.IS', 'DOAS.IS', 'OTKAR.IS', 'KARSAN.IS', 'TMSN.IS', 'VESTL.IS', 'VESBE.IS',
        'PGSUS.IS', 'TAVHL.IS', 'CLEBI.IS', 
        # --- ENERJİ & TEKNOLOJİ & ÇİMENTO ---
        'ODAS.IS', 'ZOREN.IS', 'AKSEN.IS', 'AYDEM.IS', 'GWIND.IS', 'BIOEN.IS', 'ASTOR.IS', 'SMRTG.IS', 'KONTR.IS', 'GESAN.IS', 'EGEEN.IS',
        'MIATK.IS', 'LOGO.IS', 'NETAS.IS', 'KFEIN.IS', 'REEDR.IS', 'SDTTR.IS', 'PENTA.IS',
        'AKCNS.IS', 'CIMSA.IS', 'OYAKC.IS', 'NUHCM.IS', 
        'KOZAL.IS', 'KOZAA.IS', 'IPEKE.IS', 'EKGYO.IS', 'ISGYO.IS', 'TRGYO.IS', 'AKFGY.IS', 'ARCLK.IS',
        # --- KÜRESEL PİYASALAR ---
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'XRP-USD', 'DOGE-USD', 'ADA-USD', 'BNB-USD', 'SHIB-USD',
        'GC=F', 'SI=F', 'CL=F', 'NG=F', # Altın, Gümüş, Petrol, Doğalgaz
        'EURUSD=X', 'GBPUSD=X', 'JPY=X', 'TRY=X'
    ]

    if st.button("🚀 DEV TARAMAYI BAŞLAT"):
        res = []
        bar = st.progress(0)
        durum_text = st.empty()
        
        for i, s in enumerate(takip_listesi):
            bar.progress((i+1)/len(takip_listesi))
            durum_text.text(f"Taranıyor: {s} ...") # Kullanıcı ne tarandığını görsün
            try:
                d = veri_getir(s, "1y")
                if d is not None:
                    d = z_score_hesapla(d, window)
                    z = d['Z_Score'].iloc[-1]
                    p = d['Close'].iloc[-1]
                    durum = "NÖTR"
                    if z < -z_threshold: durum = "🟢 UCUZ"
                    elif z > z_threshold: durum = "🔴 PAHALI"
                    res.append({"Sembol": s.replace(".IS",""), "Fiyat": f"{p:.2f}", "Z-Score": f"{z:.2f}", "Durum": durum})
            except: continue
            
        st.session_state['tarama_sonuclari'] = pd.DataFrame(res)
        durum_text.text("✅ Tarama Tamamlandı!")

    if st.session_state['tarama_sonuclari'] is not None:
        df_g = st.session_state['tarama_sonuclari'].copy()
        if st.checkbox("Sadece Fırsatları (AL/SAT) Göster", value=True):
            df_g = df_g[df_g["Durum"] != "NÖTR"]
        st.dataframe(df_g, use_container_width=True)

# ==========================
# SEKME 3: MONTE CARLO
# ==========================
with tab3:
    st.subheader("🎲 Gelecek Simülasyonu")
    ms = st.text_input("Sembol:", value="THYAO.IS", key="mc")
    if st.button("Simüle Et"):
        d = veri_getir(ms)
        if d is not None:
            sim = monte_carlo_simulasyon(d)
            st.line_chart(sim.iloc[:, :50])

# ==========================
# SEKME 4: CANLI TRADER
# ==========================
with tab4:
    st.subheader("🤖 Otomatik Al-Sat Robotu")
    st.markdown("Sayfa açık kaldığı sürece robot piyasayı izler.")
    
    col1, col2 = st.columns(2)
    bakiye = st.session_state['bakiye']
    portfoy = st.session_state['portfoy']
    col1.metric("💵 Nakit", f"{bakiye:,.2f} TL")
    col2.metric("💼 Pozisyonlar", f"{len(portfoy)} Adet")
    
    oto_mod = st.checkbox("✅ ROBOTU ÇALIŞTIR")
    
    if oto_mod:
        st.success("📡 Robot devrede... (Sayfayı kapatma)")
        # Robot için daha kısa, hızlı bir liste (Sunucuyu yormamak için)
        bot_listesi = ['THYAO.IS', 'GARAN.IS', 'BTC-USD', 'ETH-USD', 'GC=F', 'ASELS.IS', 'EREGL.IS']
        
        for s in bot_listesi:
            try:
                df = veri_getir(s, "1y")
                if df is not None:
                    df = z_score_hesapla(df, window)
                    son_z = df['Z_Score'].iloc[-1]
                    son_fiyat = df['Close'].iloc[-1]
                    tarih = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    if son_z < -z_threshold and bakiye > son_fiyat:
                        adet = int(bakiye * 0.10 / son_fiyat)
                        if adet > 0:
                            bakiye -= adet * son_fiyat
                            portfoy[s] = portfoy.get(s, 0) + adet
                            st.session_state['islem_gecmisi'].append(f"{tarih} - AL: {s} | {adet} lot")
                            st.toast(f"🟢 ALINDI: {s}")
                    
                    elif son_z > z_threshold and s in portfoy and portfoy[s] > 0:
                        adet = portfoy[s]
                        bakiye += adet * son_fiyat
                        del portfoy[s]
                        st.session_state['islem_gecmisi'].append(f"{tarih} - SAT: {s} | {adet} lot")
                        st.toast(f"🔴 SATILDI: {s}")
            except: continue
            
        st.session_state['bakiye'] = bakiye
        st.session_state['portfoy'] = portfoy
        verileri_kaydet(bakiye, portfoy, st.session_state['islem_gecmisi'])
        time.sleep(10)
        st.rerun()

    st.subheader("📜 İşlem Geçmişi")
    if st.session_state['islem_gecmisi']:
        st.write(st.session_state['islem_gecmisi'])
