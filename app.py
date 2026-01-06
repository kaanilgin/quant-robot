import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v12.1", layout="wide")
plt.style.use('dark_background')

# --- HAFIZA ---
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

# Satır bazlı renklendirme (Styler)
def satir_boya(row):
    stiller = [''] * len(row)
    if "PAHALI" in row['Durum']:
        stiller = ['color: #ff4b4b; font-weight: bold'] * len(row) # Kırmızı
    elif "UCUZ" in row['Durum']:
        stiller = ['color: #00c853; font-weight: bold'] * len(row) # Yeşil
    return stiller

# --- ANA BAŞLIK ---
st.title("💎 Quant Terminal Pro")

# --- SEKMELER ---
tab1, tab2 = st.tabs(["📊 Teknik Analiz", "📡 Mega Radar"])

# ==========================
# SEKME 1: TEKNİK ANALİZ
# ==========================
with tab1:
    st.markdown("### 🔍 Varlık Analizi")
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
            df = teknik_hesapla(df, window, z_threshold)
            last_p = df['Close'].iloc[-1]
            last_z = df['Z_Score'].iloc[-1]
            last_sma = df['SMA'].iloc[-1]
            fark = ((last_p - last_sma) / last_sma) * 100
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Fiyat", f"{last_p:.2f}")
            m2.metric("Ortalama", f"{last_sma:.2f}")
            m3.metric("Fark", f"%{fark:.1f}", delta_color="off")
            
            if last_z > z_threshold: m4.metric("Stres (Z)", f"{last_z:.2f}", "Pahalı 🔴")
            elif last_z < -z_threshold: m4.metric("Stres (Z)", f"{last_z:.2f}", "Ucuz 🟢")
            else: m4.metric("Stres (Z)", f"{last_z:.2f}", "Nötr ⚪")

            st.subheader("📈 Fiyat Trendi")
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            ax1.plot(df.index, df['Close'], color='white', linewidth=2, label='Fiyat')
            ax1.plot(df.index, df['SMA'], color='orange', linestyle='--', linewidth=1.5, label='Ortalama')
            ax1.plot(df.index, df['Upper'], color='red', alpha=0.6, linewidth=1, label='Üst Bant')
            ax1.plot(df.index, df['Lower'], color='green', alpha=0.6, linewidth=1, label='Alt Bant')
            ax1.fill_between(df.index, df['Upper'], df['Lower'], color='gray', alpha=0.15)
            ax1.legend(loc="upper left")
            ax1.grid(True, alpha=0.2)
            st.pyplot(fig1)

            st.subheader("⚡ Gerginlik Ölçer")
            fig2, ax2 = plt.subplots(figsize=(12, 4))
            ax2.plot(df.index, df['Z_Score'], color='cyan', linewidth=1.5, label='Gerginlik')
            ax2.axhline(0, color='white', linestyle=':', alpha=0.5)
            ax2.axhline(z_threshold, color='red', linestyle='--', linewidth=2)
            ax2.axhline(-z_threshold, color='green', linestyle='--', linewidth=2)
            ax2.fill_between(df.index, z_threshold, df['Z_Score'], where=(df['Z_Score'] > z_threshold), color='red', alpha=0.6)
            ax2.fill_between(df.index, -z_threshold, df['Z_Score'], where=(df['Z_Score'] < -z_threshold), color='green', alpha=0.6)
            ax2.legend(loc="upper left")
            ax2.grid(True, alpha=0.2)
            st.pyplot(fig2)
        else:
            st.error("Veri bulunamadı.")

# ==========================
# SEKME 2: MEGA RADAR (AYARLAR AÇIK ✅)
# ==========================
with tab2:
    st.markdown("### 📡 BIST 100 & Global Tarayıcı")
    
    # Kutu (Expander) kalktı, direkt kolonlar geldi.
    col_set1, col_set2 = st.columns(2)
    window_scan = col_set1.number_input("Ortalama Gün (Tarama İçin)", 10, 200, 50, 5, key="w2")
    z_thresh_scan = col_set2.number_input("Hassasiyet (Sigma)", 1.0, 3.0, 2.0, 0.1, key="z2")
    
    st.divider() # Araya çizgi çekelim, karışmasın

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
            durum_text.text(f"Taranıyor: {s} ...")
            try:
                d = veri_getir(s, "1y")
                if d is not None:
                    d = teknik_hesapla(d, window_scan, z_thresh_scan)
                    z = d['Z_Score'].iloc[-1]
                    durum = "NÖTR"
                    if z < -z_thresh_scan: durum = "🟢 UCUZ"
                    elif z > z_thresh_scan: durum = "🔴 PAHALI"
                    res.append({"Sembol": s.replace(".IS",""), "Fiyat": d['Close'].iloc[-1], "Z-Score": z, "Durum": durum})
            except: continue
        
        st.session_state['tarama_sonuclari'] = pd.DataFrame(res)
        durum_text.text("✅ Tarama Tamamlandı!")

    if st.session_state['tarama_sonuclari'] is not None:
        df_g = st.session_state['tarama_sonuclari'].copy()
        
        # Filtreleme (Varsayılan: KAPALI)
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
            
        # Renkli Tablo
        st.dataframe(
            df_g.style
            .apply(satir_boya, axis=1)
            .format({"Fiyat": "{:.2f}", "Z-Score": "{:.2f}"}),
            use_container_width=True,
            height=(len(df_g) + 1) * 35 + 3
        )import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v12.1", layout="wide")
plt.style.use('dark_background')

# --- HAFIZA ---
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

# Satır bazlı renklendirme (Styler)
def satir_boya(row):
    stiller = [''] * len(row)
    if "PAHALI" in row['Durum']:
        stiller = ['color: #ff4b4b; font-weight: bold'] * len(row) # Kırmızı
    elif "UCUZ" in row['Durum']:
        stiller = ['color: #00c853; font-weight: bold'] * len(row) # Yeşil
    return stiller

# --- ANA BAŞLIK ---
st.title("💎 Quant Terminal Pro")

# --- SEKMELER ---
tab1, tab2 = st.tabs(["📊 Teknik Analiz", "📡 Mega Radar"])

# ==========================
# SEKME 1: TEKNİK ANALİZ
# ==========================
with tab1:
    st.markdown("### 🔍 Varlık Analizi")
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
            df = teknik_hesapla(df, window, z_threshold)
            last_p = df['Close'].iloc[-1]
            last_z = df['Z_Score'].iloc[-1]
            last_sma = df['SMA'].iloc[-1]
            fark = ((last_p - last_sma) / last_sma) * 100
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Fiyat", f"{last_p:.2f}")
            m2.metric("Ortalama", f"{last_sma:.2f}")
            m3.metric("Fark", f"%{fark:.1f}", delta_color="off")
            
            if last_z > z_threshold: m4.metric("Stres (Z)", f"{last_z:.2f}", "Pahalı 🔴")
            elif last_z < -z_threshold: m4.metric("Stres (Z)", f"{last_z:.2f}", "Ucuz 🟢")
            else: m4.metric("Stres (Z)", f"{last_z:.2f}", "Nötr ⚪")

            st.subheader("📈 Fiyat Trendi")
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            ax1.plot(df.index, df['Close'], color='white', linewidth=2, label='Fiyat')
            ax1.plot(df.index, df['SMA'], color='orange', linestyle='--', linewidth=1.5, label='Ortalama')
            ax1.plot(df.index, df['Upper'], color='red', alpha=0.6, linewidth=1, label='Üst Bant')
            ax1.plot(df.index, df['Lower'], color='green', alpha=0.6, linewidth=1, label='Alt Bant')
            ax1.fill_between(df.index, df['Upper'], df['Lower'], color='gray', alpha=0.15)
            ax1.legend(loc="upper left")
            ax1.grid(True, alpha=0.2)
            st.pyplot(fig1)

            st.subheader("⚡ Gerginlik Ölçer")
            fig2, ax2 = plt.subplots(figsize=(12, 4))
            ax2.plot(df.index, df['Z_Score'], color='cyan', linewidth=1.5, label='Gerginlik')
            ax2.axhline(0, color='white', linestyle=':', alpha=0.5)
            ax2.axhline(z_threshold, color='red', linestyle='--', linewidth=2)
            ax2.axhline(-z_threshold, color='green', linestyle='--', linewidth=2)
            ax2.fill_between(df.index, z_threshold, df['Z_Score'], where=(df['Z_Score'] > z_threshold), color='red', alpha=0.6)
            ax2.fill_between(df.index, -z_threshold, df['Z_Score'], where=(df['Z_Score'] < -z_threshold), color='green', alpha=0.6)
            ax2.legend(loc="upper left")
            ax2.grid(True, alpha=0.2)
            st.pyplot(fig2)
        else:
            st.error("Veri bulunamadı.")

# ==========================
# SEKME 2: MEGA RADAR (AYARLAR AÇIK ✅)
# ==========================
with tab2:
    st.markdown("### 📡 BIST 100 & Global Tarayıcı")
    
    # Kutu (Expander) kalktı, direkt kolonlar geldi.
    col_set1, col_set2 = st.columns(2)
    window_scan = col_set1.number_input("Ortalama Gün (Tarama İçin)", 10, 200, 50, 5, key="w2")
    z_thresh_scan = col_set2.number_input("Hassasiyet (Sigma)", 1.0, 3.0, 2.0, 0.1, key="z2")
    
    st.divider() # Araya çizgi çekelim, karışmasın

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
            durum_text.text(f"Taranıyor: {s} ...")
            try:
                d = veri_getir(s, "1y")
                if d is not None:
                    d = teknik_hesapla(d, window_scan, z_thresh_scan)
                    z = d['Z_Score'].iloc[-1]
                    durum = "NÖTR"
                    if z < -z_thresh_scan: durum = "🟢 UCUZ"
                    elif z > z_thresh_scan: durum = "🔴 PAHALI"
                    res.append({"Sembol": s.replace(".IS",""), "Fiyat": d['Close'].iloc[-1], "Z-Score": z, "Durum": durum})
            except: continue
        
        st.session_state['tarama_sonuclari'] = pd.DataFrame(res)
        durum_text.text("✅ Tarama Tamamlandı!")

    if st.session_state['tarama_sonuclari'] is not None:
        df_g = st.session_state['tarama_sonuclari'].copy()
        
        # Filtreleme (Varsayılan: KAPALI)
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
            
        # Renkli Tablo
        st.dataframe(
            df_g.style
            .apply(satir_boya, axis=1)
            .format({"Fiyat": "{:.2f}", "Z-Score": "{:.2f}"}),
            use_container_width=True,
            height=(len(df_g) + 1) * 35 + 3
        )
    
