import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v7", layout="wide")
plt.style.use('dark_background') # Grafikler hep koyu olsun

# --- HAFIZA (Session State) ---
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

def teknik_hesapla(df, window, z_thresh):
    df['SMA'] = df['Close'].rolling(window=window).mean()
    df['STD'] = df['Close'].rolling(window=window).std()
    df['Z_Score'] = (df['Close'] - df['SMA']) / df['STD']
    df['Upper'] = df['SMA'] + (z_thresh * df['STD'])
    df['Lower'] = df['SMA'] - (z_thresh * df['STD'])
    return df

def monte_carlo_simulasyon(df, gun_sayisi, sim_sayisi=100):
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

# --- ANA BAŞLIK ---
st.title("💎 Ultimate Quant Terminali")

# --- AYARLAR PANELİ (SOL MENÜ YERİNE BURADA) ---
# Kullanıcı bu kutuya tıklayınca ayarlar açılır, yer kaplamaz.
with st.expander("⚙️ ROBOT AYARLARI (Tıkla ve Düzenle)", expanded=False):
    col_set1, col_set2 = st.columns(2)
    with col_set1:
        window = st.slider("Ortalama (SMA) Periyodu", 10, 200, 50, 5)
    with col_set2:
        z_threshold = st.slider("Hassasiyet (Standart Sapma)", 1.0, 3.0, 2.0, 0.1)

# --- SEKMELER ---
tab1, tab2, tab3 = st.tabs(["📊 PRO Analiz", "📡 Mega Tarayıcı", "🎲 Gelecek Tahmini"])

# ==========================
# SEKME 1: PRO ANALİZ (ÇİFT GRAFİK 📈)
# ==========================
with tab1:
    # Arama Kutusu
    col_input, col_info = st.columns([1, 3])
    with col_input:
        s_in = st.text_input("Hisse/Coin Sembolü:", value="THYAO.IS", key="analiz_input")
    
    if s_in:
        df = veri_getir(s_in)
        if df is not None:
            df = teknik_hesapla(df, window, z_threshold)
            
            # Son Veriler
            son_fiyat = df['Close'].iloc[-1]
            son_z = df['Z_Score'].iloc[-1]
            son_sma = df['SMA'].iloc[-1]
            fark_yuzde = ((son_fiyat - son_sma) / son_sma) * 100
            
            # --- 1. METRİKLER ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Anlık Fiyat", f"{son_fiyat:.2f}")
            m2.metric("Adil Değer (Ortalama)", f"{son_sma:.2f}")
            m3.metric("Ortalamadan Fark", f"%{fark_yuzde:.1f}")
            
            # Z-Score Rengi
            z_renk = "off"
            if son_z > z_threshold: z_renk = "inverse" # Kırmızımsı
            elif son_z < -z_threshold: z_renk = "normal" # Yeşilimsi
            m4.metric("Z-Score (Gerginlik)", f"{son_z:.2f}")

            # --- 2. GRAFİK: FİYAT VE KANALLAR ---
            st.markdown("#### 1️⃣ Fiyat Trendi ve Kanallar")
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            ax1.plot(df.index, df['Close'], color='white', linewidth=2, label='Fiyat')
            ax1.plot(df.index, df['SMA'], color='orange', linestyle='--', linewidth=1.5, label='Ortalama')
            ax1.plot(df.index, df['Upper'], color='red', alpha=0.5, linewidth=1, label='Üst Bant')
            ax1.plot(df.index, df['Lower'], color='green', alpha=0.5, linewidth=1, label='Alt Bant')
            ax1.fill_between(df.index, df['Upper'], df['Lower'], color='gray', alpha=0.1)
            ax1.set_title(f"{s_in.upper()} Fiyat Analizi")
            ax1.legend(loc="upper left")
            ax1.grid(True, alpha=0.2)
            st.pyplot(fig1)

            # --- 3. GRAFİK: Z-SCORE (GERGİNLİK) ---
            st.markdown("#### 2️⃣ Gerginlik Ölçer (Z-Score)")
            fig2, ax2 = plt.subplots(figsize=(12, 4))
            ax2.plot(df.index, df['Z_Score'], color='cyan', linewidth=1.5, label='Gerginlik')
            ax2.axhline(0, color='white', linestyle=':', alpha=0.5)
            ax2.axhline(z_threshold, color='red', linestyle='--', linewidth=2, label='Pahalı')
            ax2.axhline(-z_threshold, color='green', linestyle='--', linewidth=2, label='Ucuz')
            
            # Alanları Boya
            ax2.fill_between(df.index, z_threshold, df['Z_Score'], where=(df['Z_Score'] > z_threshold), color='red', alpha=0.6)
            ax2.fill_between(df.index, -z_threshold, df['Z_Score'], where=(df['Z_Score'] < -z_threshold), color='green', alpha=0.6)
            
            ax2.set_title("Alım/Satım Bölgeleri")
            ax2.legend(loc="upper left")
            ax2.grid(True, alpha=0.2)
            st.pyplot(fig2)
            
        else:
            st.error("Veri bulunamadı.")

# ==========================
# SEKME 2: MEGA TARAYICI
# ==========================
with tab2:
    st.subheader("📡 Piyasa Tarayıcısı")
    st.markdown("_Ayarları yukarıdaki panelden değiştirebilirsin._")
    
    takip_listesi = [
        'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'EREGL.IS', 'ASELS.IS', 'SISE.IS', 'SASA.IS', 'HEKTS.IS',
        'BIMAS.IS', 'KCHOL.IS', 'SAHOL.IS', 'TUPRS.IS', 'FROTO.IS', 'TOASO.IS', 'PGSUS.IS', 
        'ODAS.IS', 'ZOREN.IS', 'ASTOR.IS', 'KONTR.IS', 'SMRTG.IS', 'MIATK.IS', 'REEDR.IS',
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'XRP-USD',
        'GC=F', 'SI=F', 'CL=F', 'EURUSD=X', 'TRY=X'
    ]

    if st.button("🚀 TARAMAYI BAŞLAT"):
        res = []
        bar = st.progress(0)
        durum_text = st.empty()
        
        for i, s in enumerate(takip_listesi):
            bar.progress((i+1)/len(takip_listesi))
            durum_text.text(f"İnceleniyor: {s}")
            try:
                d = veri_getir(s, "1y")
                if d is not None:
                    d = teknik_hesapla(d, window, z_threshold)
                    z = d['Z_Score'].iloc[-1]
                    res.append({
                        "Sembol": s.replace(".IS",""), 
                        "Fiyat": d['Close'].iloc[-1], 
                        "Z-Score": z, 
                        "Durum": "🟢 UCUZ" if z < -z_threshold else "🔴 PAHALI" if z > z_threshold else "NÖTR"
                    })
            except: continue
        
        st.session_state['tarama_sonuclari'] = pd.DataFrame(res)
        durum_text.text("✅ Tarama Bitti!")

    if st.session_state['tarama_sonuclari'] is not None:
        df_g = st.session_state['tarama_sonuclari'].copy()
        if st.checkbox("Sadece Fırsatları Göster", value=True):
            df_g = df_g[df_g["Durum"] != "NÖTR"]
        st.dataframe(df_g, use_container_width=True)

# ==========================
# SEKME 3: MONTE CARLO
# ==========================
with tab3:
    st.subheader("🎲 Gelecek Simülasyonu")
    
    col_m1, col_m2 = st.columns([1, 3])
    with col_m1:
        mc_sym = st.text_input("Sembol:", value="BTC-USD", key="mc_sym")
        mc_gun = st.slider("Gün İleri", 30, 180, 90)
        mc_btn = st.button("Simüle Et")
        
    with col_m2:
        if mc_btn and mc_sym:
            with st.spinner("Kahin çalışıyor..."):
                d_mc = veri_getir(mc_sym)
                if d_mc is not None:
                    # Mevcut Durum
                    son = d_mc['Close'].iloc[-1]
                    degisim = (son - d_mc['Close'].iloc[-2])
                    yuzde = (degisim / d_mc['Close'].iloc[-2]) * 100
                    
                    st.metric("Şu Anki Fiyat", f"{son:.2f}", f"%{yuzde:.2f}")
                    
                    # Simülasyon ve Grafik
                    sim_df = monte_carlo_simulasyon(d_mc, mc_gun)
                    fig_mc, ax_mc = plt.subplots(figsize=(10, 5))
                    ax_mc.plot(sim_df, color='cyan', alpha=0.1, linewidth=0.5)
                    ax_mc.plot(sim_df.mean(axis=1), color='yellow', linewidth=2, label='Ortalama Rota')
                    ax_mc.legend()
                    ax_mc.grid(True, alpha=0.2)
                    st.pyplot(fig_mc)
                    
                    # İstatistikler
                    bitis = sim_df.iloc[-1]
                    c1, c2, c3 = st.columns(3)
                    c1.metric("En Kötü", f"{bitis.min():.2f}")
                    c2.metric("Ortalama", f"{bitis.mean():.2f}")
                    c3.metric("En İyi", f"{bitis.max():.2f}")
