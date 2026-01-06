import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v8 - Premium", layout="wide")

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

# --- ÜST PANEL (LOGO & KONTROLLER) ---
st.title("💎 Quant Terminal Pro")

# Kontrolleri tek bir şık kutuya (Container) alıyoruz
with st.container():
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        # Arama kutusu en solda
        s_in = st.text_input("🔍 Sembol Arayın:", value="THYAO.IS", placeholder="Örn: GARAN.IS, BTC-USD")
    with c2:
        window = st.number_input("Ortalama (Gün)", min_value=10, max_value=200, value=50, step=5)
    with c3:
        z_threshold = st.number_input("Hassasiyet", min_value=1.0, max_value=3.0, value=2.0, step=0.1)

st.divider()

# --- SEKMELER ---
tab1, tab2, tab3 = st.tabs(["📊 Teknik Analiz", "📡 Piyasa Radarı", "🎲 Simülasyon"])

# ==========================
# SEKME 1: PREMIUM ANALİZ (PLOTLY)
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
            
            durum_renk = "normal"
            if last_z > z_threshold: durum_renk = "inverse"
            elif last_z < -z_threshold: durum_renk = "normal"
            m4.metric("Stres Seviyesi (Z)", f"{last_z:.2f}", delta_color=durum_renk)

            # --- GRAFİK 1: FİYAT VE BANTLAR (İNTERAKTİF) ---
            st.subheader("📈 Fiyat Trendi")
            fig1 = go.Figure()
            
            # Fiyat Çizgisi
            fig1.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Fiyat', line=dict(color='white', width=2)))
            # Ortalama
            fig1.add_trace(go.Scatter(x=df.index, y=df['SMA'], mode='lines', name='Ortalama', line=dict(color='orange', width=1, dash='dash')))
            # Üst Bant
            fig1.add_trace(go.Scatter(x=df.index, y=df['Upper'], mode='lines', name='Üst Bant', line=dict(color='red', width=0), showlegend=False))
            # Alt Bant (Fill TonextY ile arası boyanır)
            fig1.add_trace(go.Scatter(x=df.index, y=df['Lower'], mode='lines', name='Alt Bant', line=dict(color='green', width=0), fill='tonexty', fillcolor='rgba(128, 128, 128, 0.1)', showlegend=False))
            
            fig1.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig1, use_container_width=True)

            # --- GRAFİK 2: Z-SCORE (RENKLİ SÜTUNLAR) ---
            st.subheader("⚡ Gerginlik Ölçer")
            
            # Renkleri belirle (Z-Score değerine göre)
            colors = np.where(df['Z_Score'] > z_threshold, 'red', 
                     np.where(df['Z_Score'] < -z_threshold, '#00FF00', '#00CCFF'))
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=df.index, y=df['Z_Score'], name='Z-Score', marker_color=colors))
            
            # Eşik Çizgileri
            fig2.add_hline(y=z_threshold, line_dash="dot", line_color="red", annotation_text="Pahalı")
            fig2.add_hline(y=-z_threshold, line_dash="dot", line_color="#00FF00", annotation_text="Ucuz")
            
            fig2.update_layout(template="plotly_dark", height=300, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)
            
        else:
            st.error("Veri bulunamadı.")

# ==========================
# SEKME 2: PİYASA RADARI
# ==========================
with tab2:
    st.caption("Aşağıdaki butona basarak tanımlı listeyi tarayabilirsiniz.")
    takip_listesi = ['THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'EREGL.IS', 'ASELS.IS', 'SISE.IS', 'BIMAS.IS', 'KCHOL.IS', 'SAHOL.IS', 'TUPRS.IS', 'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'GC=F', 'EURUSD=X']

    if st.button("🚀 Piyasayı Tara"):
        res = []
        bar = st.progress(0)
        for i, s in enumerate(takip_listesi):
            bar.progress((i+1)/len(takip_listesi))
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

    if st.session_state['tarama_sonuclari'] is not None:
        df_g = st.session_state['tarama_sonuclari'].copy()
        # Filtreleme
        col_filt1, col_filt2 = st.columns(2)
        with col_filt1:
            if st.checkbox("Sadece Fırsatları Göster", value=True):
                df_g = df_g[df_g["Durum"] != "NÖTR"]
        
        # Tabloyu Renklendirerek Göster
        st.dataframe(
            df_g.style.format({"Fiyat": "{:.2f}", "Z-Score": "{:.2f}"}),
            use_container_width=True
        )

# ==========================
# SEKME 3: SİMÜLASYON
# ==========================
with tab3:
    c1, c2 = st.columns([1, 4])
    with c1:
        mc_sym = st.text_input("Sembol:", value="BTC-USD", key="mc_s")
        mc_gun = st.number_input("Gün", 30, 365, 90)
        btn = st.button("Başlat ▶️")
    
    with c2:
        if btn and mc_sym:
            d_mc = veri_getir(mc_sym)
            if d_mc is not None:
                sim_df = monte_carlo_simulasyon(d_mc, mc_gun)
                
                # Plotly ile Simülasyon
                fig_mc = go.Figure()
                # İlk 50 senaryoyu çiz
                for col in sim_df.columns[:50]:
                    fig_mc.add_trace(go.Scatter(x=sim_df.index, y=sim_df[col], mode='lines', line=dict(color='cyan', width=0.5), opacity=0.1, showlegend=False))
                
                # Ortalama
                fig_mc.add_trace(go.Scatter(x=sim_df.index, y=sim_df.mean(axis=1), mode='lines', name='Ortalama', line=dict(color='yellow', width=3)))
                
                fig_mc.update_layout(title=f"{mc_sym} - {mc_gun} Günlük Olasılıklar", template="plotly_dark", height=500)
                st.plotly_chart(fig_mc, use_container_width=True)
                
                res = sim_df.iloc[-1]
                k1, k2, k3 = st.columns(3)
                k1.metric("Min Beklenti", f"{res.min():.2f}")
                k2.metric("Ortalama", f"{res.mean():.2f}")
                k3.metric("Max Beklenti", f"{res.max():.2f}")
