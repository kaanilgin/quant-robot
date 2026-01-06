import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v9.0 - Final", layout="wide")
# Grafikleri koyu tema yap (Terminal havası için)
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
    # Kırmızı/Yeşil Bantlar
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

# --- ÜST PANEL (KONTROLLER) ---
st.title("💎 Quant Terminal Pro")

with st.container():
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        s_in = st.text_input("🔍 Sembol Arayın:", value="THYAO.IS", placeholder="Örn: GARAN.IS, BTC-USD")
    with c2:
        window = st.number_input("Ortalama (Gün)", min_value=10, max_value=200, value=50, step=5)
    with c3:
        z_threshold = st.number_input("Hassasiyet", min_value=1.0, max_value=3.0, value=2.0, step=0.1)

st.divider()

# --- SEKMELER ---
tab1, tab2, tab3 = st.tabs(["📊 Teknik Analiz", "📡 Mega Radar", "🎲 Simülasyon"])

# ==========================
# SEKME 1: KLASİK ANALİZ (KIRMIZI/YEŞİL GRAFİKLİ)
# ==========================
with tab1:
    if s_in:
        df = veri_getir(s_in)
        if df is not None:
            df = teknik_hesapla(df, window, z_threshold)
            
            last_p = df['Close'].iloc[-1]
            last_z = df['Z_Score'].iloc[-1]
            last_sma = df['SMA'].iloc[-1]
            fark = ((last_p - last_sma) / last_sma) * 100
            
            # --- METRİKLER ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Fiyat", f"{last_p:.2f}")
            m2.metric("Ortalama", f"{last_sma:.2f}")
            m3.metric("Fark", f"%{fark:.1f}", delta_color="off")
            
            if last_z > z_threshold: m4.metric("Stres (Z)", f"{last_z:.2f}", "Pahalı 🔴")
            elif last_z < -z_threshold: m4.metric("Stres (Z)", f"{last_z:.2f}", "Ucuz 🟢")
            else: m4.metric("Stres (Z)", f"{last_z:.2f}", "Nötr ⚪")

            # --- GRAFİK 1: FİYAT ---
            st.subheader("📈 Fiyat Trendi ve Kanallar")
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            ax1.plot(df.index, df['Close'], color='white', linewidth=2, label='Fiyat')
            ax1.plot(df.index, df['SMA'], color='orange', linestyle='--', linewidth=1.5, label='Ortalama')
            ax1.plot(df.index, df['Upper'], color='red', alpha=0.6, linewidth=1, label='Üst Bant')
            ax1.plot(df.index, df['Lower'], color='green', alpha=0.6, linewidth=1, label='Alt Bant')
            ax1.fill_between(df.index, df['Upper'], df['Lower'], color='gray', alpha=0.15)
            ax1.set_title(f"{s_in.upper()} Fiyat Analizi")
            ax1.legend(loc="upper left")
            ax1.grid(True, alpha=0.2)
            st.pyplot(fig1)

            # --- GRAFİK 2: Z-SCORE (ALAN BOYAMALI) ---
            st.subheader("⚡ Gerginlik Ölçer (Z-Score)")
            fig2, ax2 = plt.subplots(figsize=(12, 4))
            ax2.plot(df.index, df['Z_Score'], color='cyan', linewidth=1.5, label='Gerginlik')
            ax2.axhline(0, color='white', linestyle=':', alpha=0.5)
            ax2.axhline(z_threshold, color='red', linestyle='--', linewidth=2, label='Pahalı Sınırı')
            ax2.axhline(-z_threshold, color='green', linestyle='--', linewidth=2, label='Ucuz Sınırı')
            
            ax2.fill_between(df.index, z_threshold, df['Z_Score'], where=(df['Z_Score'] > z_threshold), color='red', alpha=0.6)
            ax2.fill_between(df.index, -z_threshold, df['Z_Score'], where=(df['Z_Score'] < -z_threshold), color='green', alpha=0.6)
            
            ax2.set_title("Alım/Satım Bölgeleri")
            ax2.legend(loc="upper left")
            ax2.grid(True, alpha=0.2)
            st.pyplot(fig2)
            
        else:
            st.error("Veri bulunamadı.")

# ==========================
# SEKME 2: MEGA RADAR (DEV LİSTE GERİ GELDİ! 🚀)
# ==========================
with tab2:
    st.caption("Aşağıdaki liste BIST 100, Kripto ve Emtiaları kapsar.")
    
    # DEV LİSTE
    takip_listesi = [
        # BIST 30 & LOKOMOTİFLER
        'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'ISCTR.IS', 'YKBNK.IS', 'VAKBN.IS', 'HALKB.IS',
        'EREGL.IS', 'KRDMD.IS', 'ISDMR.IS', 'TUPRS.IS', 'PETKM.IS', 'ASELS.IS', 'SISE.IS', 'SASA.IS', 'HEKTS.IS',
        'KCHOL.IS', 'SAHOL.IS', 'DOHOL.IS', 'ENKAI.IS', 'TEKFEN.IS', 'ALARK.IS', 'BIMAS.IS', 'MGROS.IS', 'SOKM.IS',
        'FROTO.IS', 'TOASO.IS', 'TTRAK.IS', 'PGSUS.IS', 'TAVHL.IS',
        # ENERJİ & TEKNOLOJİ
        'ODAS.IS', 'ZOREN.IS', 'ASTOR.IS', 'KONTR.IS', 'SMRTG.IS', 'MIATK.IS', 'REEDR.IS', 'SDTTR.IS',
        'KOZAL.IS', 'KOZAA.IS', 'IPEKE.IS', 'EKGYO.IS', 'OYAKC.IS',
        # FOREX & KRİPTO & EMTİA
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'XRP-USD', 'DOGE-USD',
        'GC=F', 'SI=F', 'CL=F', # Altın, Gümüş, Petrol
        'EURUSD=X', 'TRY=X'
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
                    d = teknik_hesapla(d, window, z_threshold)
                    z = d['Z_Score'].iloc[-1]
                    durum = "NÖTR"
                    if z < -z_threshold: durum = "🟢 UCUZ"
                    elif z > z_threshold: durum = "🔴 PAHALI"
                    res.append({"Sembol": s.replace(".IS",""), "Fiyat": d['Close'].iloc[-1], "Z-Score": z, "Durum": durum})
            except: continue
        
        st.session_state['tarama_sonuclari'] = pd.DataFrame(res)
        durum_text.text("✅ Tarama Tamamlandı!")

    if st.session_state['tarama_sonuclari'] is not None:
        df_g = st.session_state['tarama_sonuclari'].copy()
        col_filt1, col_filt2 = st.columns(2)
        with col_filt1:
            if st.checkbox("Sadece Fırsatları Göster", value=True):
                df_g = df_g[df_g["Durum"] != "NÖTR"]
        st.dataframe(df_g.style.format({"Fiyat": "{:.2f}", "Z-Score": "{:.2f}"}), use_container_width=True)

# ==========================
# SEKME 3: SİMÜLASYON (KLASİK)
# ==========================
with tab3:
    c1, c2 = st.columns([1, 4])
    with c1:
        mc_sym = st.text_input("Sembol:", value="BTC-USD", key="mc_s")
        mc_gun = st.number_input("Gün", 30, 365, 90)
        btn = st.button("Başlat ▶️")
    
    with c2:
        if btn and mc_sym:
            with st.spinner("Hesaplanıyor..."):
                d_mc = veri_getir(mc_sym)
                if d_mc is not None:
                    sim_df = monte_carlo_simulasyon(d_mc, mc_gun)
                    
                    fig_mc, ax_mc = plt.subplots(figsize=(10, 5))
                    ax_mc.plot(sim_df, color='cyan', alpha=0.1, linewidth=0.5)
                    ax_mc.plot(sim_df.mean(axis=1), color='yellow', linewidth=2, label='Ortalama Rota')
                    
                    ax_mc.set_title(f"{mc_sym} - {mc_gun} Günlük Olasılıklar")
                    ax_mc.legend()
                    ax_mc.grid(True, alpha=0.2)
                    st.pyplot(fig_mc)
                    
                    res = sim_df.iloc[-1]
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Min Beklenti", f"{res.min():.2f}")
                    k2.metric("Ortalama", f"{res.mean():.2f}")
                    k3.metric("Max Beklenti", f"{res.max():.2f}")
                else: st.error("Veri yok.")
