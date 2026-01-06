import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v3 - Monte Carlo", layout="wide")

# --- FONKSİYONLAR ---
@st.cache_data
def veri_getir(sembol, periyot="2y"):
    # Robotun deneyeceği kombinasyonlar (Hata önleyici)
    denenecekler = [
        sembol, sembol.upper(), 
        sembol.upper().replace('.IS', '.is'), 
        sembol.lower()
    ]
    
    for s in denenecekler:
        try:
            df = yf.download(s, period=periyot, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
        except:
            continue
    return None

def z_score_hesapla(df, window):
    df['SMA'] = df['Close'].rolling(window=window).mean()
    df['STD'] = df['Close'].rolling(window=window).std()
    df['Z_Score'] = (df['Close'] - df['SMA']) / df['STD']
    return df

# --- YENİ: MONTE CARLO FONKSİYONU ---
def monte_carlo_simulasyon(df, gun_sayisi=90, sim_sayisi=200):
    # Günlük getirileri (değişim oranlarını) hesapla
    getiriler = df['Close'].pct_change().dropna()
    
    # Geçmişin ortalaması ve standart sapması (oynaklığı)
    mu = getiriler.mean()
    sigma = getiriler.std()
    
    # Son kapanış fiyatı (Başlangıç noktası)
    son_fiyat = df['Close'].iloc[-1]
    
    # Simülasyon matrisi oluştur
    simulasyon_df = pd.DataFrame()
    
    for x in range(sim_sayisi):
        fiyatlar = [son_fiyat]
        for i in range(gun_sayisi):
            # Rastgele bir şok (random shock) üret
            sok = np.random.normal(mu, sigma)
            yeni_fiyat = fiyatlar[-1] * (1 + sok)
            fiyatlar.append(yeni_fiyat)
            
        simulasyon_df[f"Senaryo {x}"] = fiyatlar
        
    return simulasyon_df

# --- SOL MENÜ (AYARLAR) ---
st.sidebar.header("⚙️ Genel Ayarlar")
window = st.sidebar.slider("SMA Periyodu (Gün)", 10, 200, 50, 5)
z_threshold = st.sidebar.slider("Z-Score Hassasiyeti", 1.0, 3.0, 2.0, 0.1)

st.sidebar.info("v3.0 - Monte Carlo Modülü Eklendi 🎲")

# --- ANA EKRAN ---
st.title("💎 Ultimate Quant Terminali")
st.markdown("Piyasa analizi, fırsat taraması ve gelecek simülasyonu.")

# 3 SEKME OLDU
tab1, tab2, tab3 = st.tabs(["📊 Detaylı Analiz", "📡 Fırsat Radarı", "🎲 Monte Carlo Lab"])

# ==========================
# SEKME 1: DETAYLI ANALİZ
# ==========================
with tab1:
    st.subheader("Tekli Hisse Analizi")
    symbol_input = st.text_input("Analiz edilecek sembolü girin:", value="", placeholder="Örn: THYAO.IS")
    
    if symbol_input:
        symbol = symbol_input.replace('İ', 'I').replace('ı', 'i').upper().strip()
        if symbol.endswith(".IS"): symbol = symbol.replace(".IS", ".is")
        
        df = veri_getir(symbol)
        if df is not None:
            df = z_score_hesapla(df, window)
            last_z = df['Z_Score'].iloc[-1]
            last_price = df['Close'].iloc[-1]
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Fiyat", f"{last_price:.2f}")
            col2.metric("Z-Score", f"{last_z:.2f}")
            
            durum = "NÖTR"
            if last_z < -z_threshold: durum = "🟢 UCUZ"
            elif last_z > z_threshold: durum = "🔴 PAHALI"
            col3.metric("Sinyal", durum)
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(df.index, df['Z_Score'], label='Z-Score', color='blue')
            ax.axhline(z_threshold, color='red', linestyle='--')
            ax.axhline(-z_threshold, color='green', linestyle='--')
            st.pyplot(fig)
        else:
            st.error("Veri bulunamadı.")

# ==========================
# SEKME 2: FIRSAT RADARI
# ==========================
with tab2:
    st.subheader("📡 Piyasa Tarayıcısı (BIST 100 + Kripto)")
    
    # DEV LİSTE (BIST 100 Örnekleri + Kripto)
    takip_listesi = [
        'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'EREGL.IS', 'ASELS.IS', 'SISE.IS', 'BIMAS.IS', 
        'KCHOL.IS', 'SAHOL.IS', 'TUPRS.IS', 'PETKM.IS', 'HEKTS.IS', 'SASA.IS', 'KOZAL.IS',
        'FROTO.IS', 'TOASO.IS', 'TTRAK.IS', 'PGSUS.IS', 'TAVHL.IS', 'MGROS.IS', 'SOKM.IS',
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'XRP-USD', 'GC=F', 'EURUSD=X'
    ]
    
    if st.button("🚀 Taramayı Başlat", key="tara_btn"):
        firsatlar = []
        bar = st.progress(0)
        for i, s in enumerate(takip_listesi):
            bar.progress((i + 1) / len(takip_listesi))
            try:
                d_tarama = veri_getir(s, periyot="1y")
                if d_tarama is not None:
                    d_tarama = z_score_hesapla(d_tarama, window)
                    z = d_tarama['Z_Score'].iloc[-1]
                    p = d_tarama['Close'].iloc[-1]
                    
                    durum = "NÖTR"
                    if z < -z_threshold: durum = "🟢 UCUZ"
                    elif z > z_threshold: durum = "🔴 PAHALI"
                    
                    firsatlar.append({"Sembol": s.upper().replace(".IS",""), "Fiyat": f"{p:.2f}", "Z-Score": f"{z:.2f}", "Durum": durum})
            except: continue
            
        if firsatlar:
            df_sonuc = pd.DataFrame(firsatlar)
            if st.checkbox("Sadece Fırsatları Göster"):
                df_sonuc = df_sonuc[df_sonuc["Durum"] != "NÖTR"]
            st.dataframe(df_sonuc, use_container_width=True, hide_index=True)

# ==========================
# SEKME 3: MONTE CARLO LABORATUVARI (YENİ)
# ==========================
with tab3:
    st.subheader("🎲 Gelecek Simülasyonu (Monte Carlo)")
    st.markdown("Geçmiş volatiliteye dayanarak olası gelecek senaryolarını hesaplar.")
    
    col_mc1, col_mc2 = st.columns([1, 3])
    
    with col_mc1:
        mc_symbol_input = st.text_input("Sembol Gir:", value="THYAO.IS", key="mc_input")
        # Senin istediğin 90 gün burada varsayılan ayar
        mc_gun = st.slider("Tahmin Süresi (Gün)", 30, 180, 90) 
        mc_sim_sayisi = st.slider("Senaryo Sayısı", 50, 500, 200)
        mc_btn = st.button("Simüle Et 🔮")
        
    with col_mc2:
        if mc_btn:
            mc_symbol = mc_symbol_input.replace('İ', 'I').replace('ı', 'i').upper().strip()
            if mc_symbol.endswith(".IS"): mc_symbol = mc_symbol.replace(".IS", ".is")
            
            with st.spinner("Olasılıklar hesaplanıyor..."):
                df_mc = veri_getir(mc_symbol)
                
                if df_mc is not None:
                    sim_df = monte_carlo_simulasyon(df_mc, mc_gun, mc_sim_sayisi)
                    
                    # Grafiği Çiz
                    fig, ax = plt.subplots(figsize=(10, 5))
                    # İlk 50 senaryoyu çiz (hepsini çizersek grafik karışabilir)
                    ax.plot(sim_df.iloc[:, :50], color='gray', alpha=0.1, linewidth=1)
                    # Ortalamayı çiz
                    ax.plot(sim_df.mean(axis=1), color='red', linewidth=2, label='Ortalama Beklenti')
                    
                    ax.set_title(f"{mc_symbol} - {mc_gun} Günlük Gelecek Simülasyonu")
                    ax.legend()
                    st.pyplot(fig)
                    
                    # İstatistikler
                    bitis_fiyatlari = sim_df.iloc[-1]
                    max_fiyat = bitis_fiyatlari.max()
                    min_fiyat = bitis_fiyatlari.min()
                    ort_fiyat = bitis_fiyatlari.mean()
                    
                    st.success(f"Analiz Tamamlandı! ({mc_sim_sayisi} Senaryo)")
                    
                    # Tahmin Kartları
                    k1, k2, k3 = st.columns(3)
                    k1.metric("En Kötü Senaryo", f"{min_fiyat:.2f}")
                    k2.metric("Ortalama Beklenti", f"{ort_fiyat:.2f}")
                    k3.metric("En İyi Senaryo", f"{max_fiyat:.2f}")
                    
                else:
                    st.error("Veri bulunamadı!")
        else:
            st.info("👈 Sol taraftan ayarları yap ve butona bas.")
