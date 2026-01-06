import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v3.2 - Hafızalı", layout="wide")

# --- FONKSİYONLAR ---
@st.cache_data
def veri_getir(sembol, periyot="2y"):
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

def monte_carlo_simulasyon(df, gun_sayisi=90, sim_sayisi=200):
    getiriler = df['Close'].pct_change().dropna()
    mu = getiriler.mean()
    sigma = getiriler.std()
    son_fiyat = df['Close'].iloc[-1]
    
    simulasyon_df = pd.DataFrame()
    
    for x in range(sim_sayisi):
        fiyatlar = [son_fiyat]
        for i in range(gun_sayisi):
            sok = np.random.normal(mu, sigma)
            yeni_fiyat = fiyatlar[-1] * (1 + sok)
            fiyatlar.append(yeni_fiyat)
        simulasyon_df[f"Senaryo {x}"] = fiyatlar
        
    return simulasyon_df

# --- AYARLAR ---
st.sidebar.header("⚙️ Genel Ayarlar")
window = st.sidebar.slider("SMA Periyodu (Gün)", 10, 200, 50, 5)
z_threshold = st.sidebar.slider("Z-Score Hassasiyeti", 1.0, 3.0, 2.0, 0.1)
st.sidebar.info("v3.2 - Hafıza Modülü Aktif 🧠")

# --- ANA EKRAN ---
st.title("💎 Ultimate Quant Terminali")
tab1, tab2, tab3 = st.tabs(["📊 Detaylı Analiz", "📡 Fırsat Radarı", "🎲 Monte Carlo Lab"])

# ==========================
# SEKME 1: DETAYLI ANALİZ
# ==========================
with tab1:
    st.subheader("Tekli Hisse Analizi")
    symbol_input = st.text_input("Analiz edilecek sembol:", value="", placeholder="Örn: THYAO.IS")
    
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
# SEKME 2: FIRSAT RADARI (HAFIZALI VERSİYON 🧠)
# ==========================
with tab2:
    st.subheader("📡 Piyasa Tarayıcısı")
    
    # Session State (Hafıza) Kontrolü
    if 'tarama_sonuclari' not in st.session_state:
        st.session_state['tarama_sonuclari'] = None

    # ---------------------------------------------------------
    # GÜNCELLENMİŞ DEV TAKİP LİSTESİ (BIST 100 + KRİPTO + EMTİA + FX)
    # ---------------------------------------------------------
    takip_listesi = [
        # --- BIST 30 & 50 DEVLERİ ---
        'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'ISCTR.IS', 'YKBNK.IS', 'VAKBN.IS', 'HALKB.IS',
        'EREGL.IS', 'KRDMD.IS', 'ISDMR.IS', 'TUPRS.IS', 'PETKM.IS', 'ASELS.IS', 'SISE.IS',
        'KCHOL.IS', 'SAHOL.IS', 'DOHOL.IS', 'ENKAI.IS', 'TEKFEN.IS', 'ALARK.IS', 'GSDHO.IS',
        'BIMAS.IS', 'MGROS.IS', 'SOKM.IS', 'AEFES.IS', 'CCOLA.IS', 'ULKER.IS',
        'FROTO.IS', 'TOASO.IS', 'TTRAK.IS', 'DOAS.IS', 'OTKAR.IS', 'KARSAN.IS', 'TMSN.IS',
        'PGSUS.IS', 'TAVHL.IS', 'CLEBI.IS', 
        'HEKTS.IS', 'SASA.IS', 'GUBRF.IS', 'KONTR.IS', 'SMRTG.IS', 'GESAN.IS', 'EGEEN.IS',
        'KOZAL.IS', 'KOZAA.IS', 'IPEKE.IS',
        'EKGYO.IS', 'ISGYO.IS', 'TRGYO.IS',
        'ODAS.IS', 'ZOREN.IS', 'AKSEN.IS', 'AYDEM.IS', 'GWIND.IS', 'BIOEN.IS', 'ASTOR.IS',
        
        # --- TEKNOLOJİ & YAZILIM ---
        'MIATK.IS', 'LOGO.IS', 'NETAS.IS', 'KFEIN.IS', 'REEDR.IS', 'SDTTR.IS',
        
        # --- ÇİMENTO & ENERJİ ---
        'AKCNS.IS', 'CIMSA.IS', 'OYAKC.IS', 'NUHCM.IS', 

        # --- KÜRESEL PİYASALAR ---
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'XRP-USD', 'DOGE-USD', 'ADA-USD', # Kripto
        'GC=F', 'SI=F', 'CL=F', 'NG=F', 'HG=F',  # Emtia (Altın, Gümüş, Petrol, Gaz, Bakır)
        'EURUSD=X', 'GBPUSD=X', 'JPY=X', 'TRY=X' # Forex (Euro, Sterlin, Yen, Dolar/TL)
    ]
    
    # Butona basılınca tarama yap ve HAFIZAYA KAYDET
    if st.button("🚀 Taramayı Başlat"):
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
        
        # Sonuçları DataFrame'e çevirip hafızaya atıyoruz
        if firsatlar:
            st.session_state['tarama_sonuclari'] = pd.DataFrame(firsatlar)
        else:
            st.warning("Veri bulunamadı.")

    # --- SONUÇLARI GÖSTERME (BUTONDAN BAĞIMSIZ) ---
    # Eğer hafızada veri varsa, her durumda (sayfa yenilense bile) göster
    if st.session_state['tarama_sonuclari'] is not None:
        df_goster = st.session_state['tarama_sonuclari'].copy()
        
        # Filtreleme Kutusu
        sadece_firsat = st.checkbox("Sadece Fırsatları (AL/SAT) Göster", value=False)
        
        if sadece_firsat:
            df_goster = df_goster[df_goster["Durum"] != "NÖTR"]
        
        st.success(f"Sonuçlar Görüntüleniyor ({len(df_goster)} Kayıt)")
        st.dataframe(df_goster, use_container_width=True, hide_index=True)

# ==========================
# SEKME 3: MONTE CARLO LABORATUVARI
# ==========================
with tab3:
    st.subheader("🎲 Gelecek Simülasyonu (Monte Carlo)")
    
    col_mc1, col_mc2 = st.columns([1, 3])
    
    with col_mc1:
        mc_symbol_input = st.text_input("Sembol Gir:", value="THYAO.IS", key="mc_input")
        mc_gun = st.slider("Tahmin Süresi (Gün)", 30, 180, 90) 
        mc_sim_sayisi = st.slider("Senaryo Sayısı", 50, 500, 200)
        mc_btn = st.button("Simüle Et 🔮")
        
    with col_mc2:
        if mc_btn:
            mc_symbol = mc_symbol_input.replace('İ', 'I').replace('ı', 'i').upper().strip()
            if mc_symbol.endswith(".IS"): mc_symbol = mc_symbol.replace(".IS", ".is")
            
            with st.spinner(f"{mc_symbol} için simülasyon çalıştırılıyor..."):
                df_mc = veri_getir(mc_symbol)
                
                if df_mc is not None and len(df_mc) > 1:
                    son_fiyat = df_mc['Close'].iloc[-1]
                    onceki_fiyat = df_mc['Close'].iloc[-2]
                    degisim = son_fiyat - onceki_fiyat
                    yuzde_degisim = (degisim / onceki_fiyat) * 100
                    
                    st.markdown("### 📊 Mevcut Piyasa Durumu")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Son Fiyat", f"{son_fiyat:.2f}")
                    m2.metric("Günlük Değişim", f"%{yuzde_degisim:.2f}", f"{degisim:.2f}")
                    m3.metric("Analiz Periyodu", f"{mc_gun} Gün")
                    st.divider() 
                    
                    sim_df = monte_carlo_simulasyon(df_mc, mc_gun, mc_sim_sayisi)
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(sim_df.iloc[:, :50], color='gray', alpha=0.1, linewidth=1)
                    ax.plot(sim_df.mean(axis=1), color='red', linewidth=2, label='Ortalama Rota')
                    
                    ax.set_title(f"{mc_symbol} - Olası Gelecek Senaryoları")
                    ax.legend()
                    st.pyplot(fig)
                    
                    bitis = sim_df.iloc[-1]
                    k1, k2, k3 = st.columns(3)
                    k1.metric("En Kötü İhtimal", f"{bitis.min():.2f}")
                    k2.metric("Ortalama Beklenti", f"{bitis.mean():.2f}")
                    k3.metric("En İyi İhtimal", f"{bitis.max():.2f}")
                else:
                    st.error("Veri bulunamadı!")
