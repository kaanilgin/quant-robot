import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v13 - Pro", layout="wide")
plt.style.use('dark_background')

# --- HAFIZA ---
if 'tarama_sonuclari' not in st.session_state:
    st.session_state['tarama_sonuclari'] = None

# --- GELİŞMİŞ HESAPLAMA MOTORU ---
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

def indikatorleri_hesapla(df, window, z_thresh):
    # 1. Z-SCORE (Konum)
    df['SMA'] = df['Close'].rolling(window=window).mean()
    df['STD'] = df['Close'].rolling(window=window).std()
    df['Z_Score'] = (df['Close'] - df['SMA']) / df['STD']
    df['Upper'] = df['SMA'] + (z_thresh * df['STD'])
    df['Lower'] = df['SMA'] - (z_thresh * df['STD'])
    
    # 2. RSI (Momentum - 14 Günlük Standart)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 3. MACD (Trend - 12/26/9 Standart)
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

# Tablo Renklendirme
def satir_boya(row):
    stiller = [''] * len(row)
    # Z-Score Renkleri
    if "PAHALI" in row['Durum']:
        stiller = ['color: #ff4b4b; font-weight: bold'] * len(row)
    elif "UCUZ" in row['Durum']:
        stiller = ['color: #00c853; font-weight: bold'] * len(row)
    return stiller

# --- ANA BAŞLIK ---
st.title("💎 Quant Terminal Pro (Multi-Indicator)")

# --- SEKMELER ---
tab1, tab2 = st.tabs(["📊 Detaylı Analiz", "📡 Mega Radar"])

# ==========================
# SEKME 1: DETAYLI ANALİZ
# ==========================
with tab1:
    st.markdown("### 🔍 Çoklu İndikatör Analizi")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        s_in = st.text_input("Sembol:", value="THYAO.IS", placeholder="Örn: GARAN.IS")
    with c2:
        window = st.number_input("Ortalama (Gün)", 10, 200, 50, 5, key="w1")
    with c3:
        z_threshold = st.number_input("Hassasiyet", 1.0, 3.0, 2.0, 0.1, key="z1")
        
    st.divider()

    if s_in:
        df = veri_getir(s_in)
        if df is not None:
            df = indikatorleri_hesapla(df, window, z_threshold)
            
            # Son Değerler
            last_p = df['Close'].iloc[-1]
            last_z = df['Z_Score'].iloc[-1]
            last_rsi = df['RSI'].iloc[-1]
            last_macd = df['MACD'].iloc[-1]
            last_sig = df['Signal_Line'].iloc[-1]
            
            # --- 1. ANA METRİKLER ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Fiyat", f"{last_p:.2f}")
            
            # Z-Score Yorumu
            z_durum = "Nötr ⚪"
            if last_z > z_threshold: z_durum = "Pahalı 🔴"
            elif last_z < -z_threshold: z_durum = "Ucuz 🟢"
            m2.metric("Z-Score (Konum)", f"{last_z:.2f}", z_durum)
            
            # RSI Yorumu
            rsi_durum = "Nötr ⚪"
            if last_rsi > 70: rsi_durum = "Aşırı Alım 🔴"
            elif last_rsi < 30: rsi_durum = "Aşırı Satım 🟢"
            m3.metric("RSI (Güç)", f"{last_rsi:.1f}", rsi_durum)
            
            # MACD Yorumu
            macd_durum = "Nötr ⚪"
            if last_macd > last_sig: macd_durum = "Al Sinyali (Pozitif) 🟢"
            else: macd_durum = "Sat Sinyali (Negatif) 🔴"
            m4.metric("MACD (Trend)", f"{last_macd:.2f}", macd_durum)
            
            # --- 2. GRAFİKLER ---
            
            # Grafik A: Fiyat ve Bantlar
            st.subheader("📈 Fiyat ve Bollinger Bantları")
            fig1, ax1 = plt.subplots(figsize=(12, 4))
            ax1.plot(df.index, df['Close'], color='white', linewidth=2, label='Fiyat')
            ax1.plot(df.index, df['SMA'], color='orange', linestyle='--', label='Ortalama')
            ax1.fill_between(df.index, df['Upper'], df['Lower'], color='gray', alpha=0.15)
            ax1.legend(loc="upper left")
            ax1.grid(True, alpha=0.2)
            st.pyplot(fig1)

            # Grafik B: RSI ve MACD (Yan Yana)
            c_g1, c_g2 = st.columns(2)
            
            with c_g1:
                st.markdown("**RSI İndikatörü**")
                fig2, ax2 = plt.subplots(figsize=(6, 3))
                ax2.plot(df.index, df['RSI'], color='cyan')
                ax2.axhline(70, color='red', linestyle='--')
                ax2.axhline(30, color='green', linestyle='--')
                ax2.set_ylim(0, 100)
                ax2.grid(True, alpha=0.2)
                st.pyplot(fig2)
                
            with c_g2:
                st.markdown("**MACD İndikatörü**")
                fig3, ax3 = plt.subplots(figsize=(6, 3))
                ax3.plot(df.index, df['MACD'], color='yellow', label='MACD')
                ax3.plot(df.index, df['Signal_Line'], color='red', label='Sinyal')
                ax3.bar(df.index, df['MACD']-df['Signal_Line'], color='gray', alpha=0.3)
                ax3.grid(True, alpha=0.2)
                st.pyplot(fig3)

        else:
            st.error("Veri bulunamadı.")

# ==========================
# SEKME 2: MEGA RADAR (GELİŞMİŞ)
# ==========================
with tab2:
    st.markdown("### 📡 BIST 100 & Global Tarayıcı")
    
    col_set1, col_set2 = st.columns(2)
    window_scan = col_set1.number_input("Ortalama Gün", 10, 200, 50, 5, key="w2")
    z_thresh_scan = col_set2.number_input("Hassasiyet", 1.0, 3.0, 2.0, 0.1, key="z2")
    
    st.divider()

    takip_listesi = [
        'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'ISCTR.IS', 'YKBNK.IS', 'VAKBN.IS', 'HALKB.IS',
        'EREGL.IS', 'KRDMD.IS', 'ISDMR.IS', 'TUPRS.IS', 'PETKM.IS', 'ASELS.IS', 'SISE.IS', 'SASA.IS', 'HEKTS.IS',
        'KCHOL.IS', 'SAHOL.IS', 'DOHOL.IS', 'ENKAI.IS', 'TEKFEN.IS', 'ALARK.IS', 'BIMAS.IS', 'MGROS.IS', 'SOKM.IS',
        'FROTO.IS', 'TOASO.IS', 'TTRAK.IS', 'PGSUS.IS', 'TAVHL.IS',
        'ODAS.IS', 'ZOREN.IS', 'ASTOR.IS', 'KONTR.IS', 'SMRTG.IS', 'MIATK.IS', 'REEDR.IS', 'SDTTR.IS',
        'KOZAL.IS', 'KOZAA.IS', 'IPEKE.IS', 'EKGYO.IS', 'OYAKC.IS',
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'XRP-USD', 'DOGE-USD',
        'GC=F', 'SI=F', 'CL=F', 'EURUSD=X', 'TRY=X'
    ]

    if st.button("🚀 Mega Taramayı Başlat"):
        res = []
        bar = st.progress(0)
        durum_text = st.empty()
        
        for i, s in enumerate(takip_listesi):
            bar.progress((i+1)/len(takip_listesi))
            durum_text.text(f"Analiz ediliyor: {s} ...")
            try:
                d = veri_getir(s, "1y")
                if d is not None:
                    d = indikatorleri_hesapla(d, window_scan, z_thresh_scan)
                    
                    z = d['Z_Score'].iloc[-1]
                    rsi = d['RSI'].iloc[-1]
                    macd = d['MACD'].iloc[-1]
                    sig = d['Signal_Line'].iloc[-1]
                    
                    # GENEL DURUM KARARI
                    durum = "NÖTR"
                    
                    # 1. Z-Score Sinyali
                    if z < -z_thresh_scan: durum = "🟢 UCUZ"
                    elif z > z_thresh_scan: durum = "🔴 PAHALI"
                    
                    # 2. RSI Filtresi (Ekstra bilgi olarak ekliyoruz)
                    rsi_not = "Normal"
                    if rsi < 30: rsi_not = "Dipte (30↓)"
                    elif rsi > 70: rsi_not = "Tepede (70↑)"
                    
                    # 3. MACD Filtresi
                    macd_not = "Negatif"
                    if macd > sig: macd_not = "Pozitif"
                    
                    res.append({
                        "Sembol": s.replace(".IS",""), 
                        "Fiyat": d['Close'].iloc[-1], 
                        "Z-Score": z, 
                        "RSI": rsi,
                        "MACD": macd_not,
                        "Durum": durum
                    })
            except: continue
        
        st.session_state['tarama_sonuclari'] = pd.DataFrame(res)
        durum_text.text("✅ Analiz Tamamlandı!")

    if st.session_state['tarama_sonuclari'] is not None:
        df_g = st.session_state['tarama_sonuclari'].copy()
        
        filtre = st.checkbox("Sadece Fırsatları Göster", value=False)
        if filtre:
            df_g = df_g[df_g["Durum"] != "NÖTR"]
        
        # Kartlar
        toplam = len(df_g)
        ucuzlar = len(df_g[df_g['Durum'] == "🟢 UCUZ"])
        pahalilar = len(df_g[df_g['Durum'] == "🔴 PAHALI"])
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Toplam Varlık", f"{toplam}")
        k2.metric("Ucuz Fırsatlar", f"{ucuzlar}", delta_color="normal")
        k3.metric("Pahalı Riskler", f"{pahalilar}", delta_color="inverse")
        
        st.markdown("---")
            
        st.dataframe(
            df_g.style
            .apply(satir_boya, axis=1)
            .format({"Fiyat": "{:.2f}", "Z-Score": "{:.2f}", "RSI": "{:.0f}"}),
            use_container_width=True,
            height=(len(df_g) + 1) * 35 + 3
        )
