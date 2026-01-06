import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Robot v2", layout="wide")

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
    # Basit Hareketli Ortalama (SMA) ve Standart Sapma
    df['SMA'] = df['Close'].rolling(window=window).mean()
    df['STD'] = df['Close'].rolling(window=window).std()
    # Z-Score Formülü: (Fiyat - Ortalama) / Sapma
    df['Z_Score'] = (df['Close'] - df['SMA']) / df['STD']
    return df

# --- SOL MENÜ (AYARLAR) ---
st.sidebar.header("⚙️ Robot Ayarları")
st.sidebar.write("Bu ayarlar hem analiz hem radar için geçerlidir.")

window = st.sidebar.slider("Ortalama Periyodu (Gün)", 10, 200, 50, 5)
z_threshold = st.sidebar.slider("Hassasiyet (Sigma)", 1.0, 3.0, 2.0, 0.1)

# --- ANA EKRAN: SEKMELER ---
st.title("💎 Ultimate Quant Terminali")
tab1, tab2 = st.tabs(["📊 Detaylı Analiz", "📡 Fırsat Radarı"])

# ==========================
# SEKME 1: DETAYLI ANALİZ (Eski Kodumuz)
# ==========================
with tab1:
    st.subheader("Tekli Hisse/Coin Analizi")
    
    # Giriş Kutusu (Sadece bu sekme için)
    symbol_input = st.text_input("Analiz edilecek sembolü girin:", value="", placeholder="Örn: THYAO.IS, BTC-USD")
    
    if not symbol_input:
        st.info("👈 Analize başlamak için yukarıya bir sembol yazın.")
    else:
        # Türkçe karakter düzeltme
        symbol = symbol_input.replace('İ', 'I').replace('ı', 'i').upper().strip()
        if symbol.endswith(".IS"): symbol = symbol.replace(".IS", ".is")

        with st.spinner(f'{symbol} verileri çekiliyor...'):
            df = veri_getir(symbol)

        if df is None:
            st.error("Veri bulunamadı! Sembolü kontrol et.")
        else:
            df = z_score_hesapla(df, window)
            last_z = df['Z_Score'].iloc[-1]
            last_price = df['Close'].iloc[-1]
            
            # Skor Kartları
            col1, col2, col3 = st.columns(3)
            col1.metric("Son Fiyat", f"{last_price:.2f}")
            col2.metric("Z-Score", f"{last_z:.2f}")
            
            durum = "NÖTR"
            if last_z < -z_threshold: durum = "🟢 UCUZ (AL FIRSATI)"
            elif last_z > z_threshold: durum = "🔴 PAHALI (SAT FIRSATI)"
            col3.metric("Robot Kararı", durum)

            # Grafik
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df.index, df['Z_Score'], label='Z-Score', color='blue')
            ax.axhline(0, color='black', linestyle='--', alpha=0.5)
            ax.axhline(z_threshold, color='red', linestyle='--', label='Pahalı Bölgesi')
            ax.axhline(-z_threshold, color='green', linestyle='--', label='Ucuz Bölgesi')
            ax.fill_between(df.index, z_threshold, df['Z_Score'], where=(df['Z_Score'] > z_threshold), color='red', alpha=0.3)
            ax.fill_between(df.index, -z_threshold, df['Z_Score'], where=(df['Z_Score'] < -z_threshold), color='green', alpha=0.3)
            ax.legend()
            st.pyplot(fig)

# ==========================
# SEKME 2: FIRSAT RADARI (Yeni Özellik)
# ==========================
with tab2:
    st.subheader("📡 Piyasa Tarayıcısı")
    st.markdown("Aşağıdaki **'Taramayı Başlat'** butonuna basarak popüler listeyi tara.")
    
    # Sabit Takip Listesi (Bunu istediğin gibi genişletebilirsin)
    # ---------------------------------------------------------
    # GÜNCELLENMİŞ DEV TAKİP LİSTESİ (BIST 100 + Kripto + Emtia)
    # ---------------------------------------------------------
    takip_listesi = [
        # --- BANKALAR ---
        'AKBNK.IS', 'GARAN.IS', 'ISCTR.IS', 'YKBNK.IS', 'VAKBN.IS', 'HALKB.IS', 'TSKB.IS', 'SKBNK.IS',
        # --- HOLDİNGLER ---
        'KCHOL.IS', 'SAHOL.IS', 'DOHOL.IS', 'ENKAI.IS', 'TEKFEN.IS', 'ALARK.IS', 'TKFEN.IS', 'GSDHO.IS',
        # --- SANAYİ & METAL ---
        'EREGL.IS', 'KRDMD.IS', 'ISDMR.IS', 'TUPRS.IS', 'PETKM.IS', 'SISE.IS', 'SASA.IS', 'HEKTS.IS',
        # --- OTOMOTİV ---
        'FROTO.IS', 'TOASO.IS', 'TTRAK.IS', 'DOAS.IS', 'OTKAR.IS', 'KARSAN.IS', 'TMSN.IS',
        # --- HAVACILIK & ULAŞIM ---
        'THYAO.IS', 'PGSUS.IS', 'TAVHL.IS', 'CLEBI.IS',
        # --- PERAKENDE & GIDA ---
        'BIMAS.IS', 'MGROS.IS', 'SOKM.IS', 'AEFES.IS', 'CCOLA.IS', 'ULKER.IS', 'TUKAS.IS',
        # --- TEKNOLOJİ & SAVUNMA ---
        'ASELS.IS', 'KFEIN.IS', 'LOGO.IS', 'NETAS.IS', 'KONTR.IS', 'MIATK.IS', 'SMRTG.IS', 'REEDR.IS',
        # --- ENERJİ ---
        'AKSEN.IS', 'ZOREN.IS', 'ODAS.IS', 'AYDEM.IS', 'GWIND.IS', 'CANT.IS', 'BIOEN.IS', 'ASTOR.IS',
        # --- GYO & İNŞAAT ---
        'EKGYO.IS', 'ISGYO.IS', 'TRGYO.IS', 'AKFGY.IS',
        # --- MADEN ---
        'KOZAL.IS', 'KOZAA.IS', 'IPEKE.IS',
        # --- ÇİMENTO ---
        'AKCNS.IS', 'CIMSA.IS', 'OYAKC.IS',
        # --- KRİPTO & EMTİA & DÖVİZ (BONUSLAR) ---
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD', 'XRP-USD', 'DOGE-USD',
        'GC=F', 'SI=F', 'CL=F', 'EURUSD=X' 
    ]
    
    if st.button("🚀 Taramayı Başlat"):
        firsatlar = []
        progress_bar = st.progress(0)
        
        for i, s in enumerate(takip_listesi):
            # İlerleme çubuğunu güncelle
            progress_bar.progress((i + 1) / len(takip_listesi))
            
            try:
                # Veriyi çek ve hesapla
                d_tarama = veri_getir(s, periyot="1y") # Daha hızlı olsun diye 1 yıllık
                if d_tarama is not None and not d_tarama.empty:
                    d_tarama = z_score_hesapla(d_tarama, window)
                    son_z = d_tarama['Z_Score'].iloc[-1]
                    son_fiyat = d_tarama['Close'].iloc[-1]
                    
                    # Sadece FIRSAT olanları listeye ekle (Nötrleri alma)
                    sinyal = "NÖTR"
                    if son_z < -z_threshold: sinyal = "🟢 UCUZ"
                    elif son_z > z_threshold: sinyal = "🔴 PAHALI"
                    
                    # Sonuçları kaydet
                    firsatlar.append({
                        "Sembol": s.upper().replace(".IS", ""), # .is uzantısını gizle, şık dursun
                        "Fiyat": f"{son_fiyat:.2f}",
                        "Z-Score": f"{son_z:.2f}",
                        "Durum": sinyal
                    })
            except:
                continue # Hata vereni pas geç
        
        # --- SONUÇLARI GÖSTERME KISMI (GÜNCELLENDİ) ---
        if firsatlar:
            df_sonuc = pd.DataFrame(firsatlar)
            
            # 1. Filtreleme Seçeneği
            sadece_firsat = st.checkbox("Sadece Fırsatları (AL/SAT) Göster", value=False)
            
            if sadece_firsat:
                # İçinde "UCUZ" veya "PAHALI" geçenleri süz
                df_sonuc = df_sonuc[df_sonuc["Durum"] != "NÖTR"]
            
            st.success(f"Tarama Tamamlandı! {len(takip_listesi)} varlık incelendi.")
            
            # 2. İnteraktif Tablo (Sıralanabilir)
            # use_container_width=True tablonun sayfaya yayılmasını sağlar
            st.dataframe(df_sonuc, use_container_width=True, hide_index=True)
            
        else:
            st.warning("Veri çekilemedi veya listede sorun var.")
