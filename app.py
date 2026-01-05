import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Quant Avcısı", page_icon="💎", layout="wide")

# --- BAŞLIK ---
st.title("💎 Ultimate Quant Robotu (Web Sürümü)")
st.markdown("Mean Reversion (Ortalamaya Dönüş) stratejisi ile piyasadaki **ucuz/pahalı** fırsatları yakala.")

# --- SIDEBAR (AYARLAR) ---
st.sidebar.header("⚙️ Robot Ayarları")

# 1. Kullanıcı Girişleri (Varsayılan boş)
symbol_input = st.sidebar.text_input("Varlık Sembolü (Yahoo Kodu)", value="")

# Diğer Ayarlar
window = st.sidebar.slider("Ortalama Periyodu (Gün)", min_value=10, max_value=200, value=50, step=5)
z_threshold = st.sidebar.slider("Hassasiyet (Sigma)", min_value=1.0, max_value=3.0, value=2.0, step=0.1)

st.sidebar.info(f"""
**Örnek Semboller:**
* BIST: `THYAO.IS`, `ASELS.IS`
* Kripto: `BTC-USD`, `ETH-USD`
* Forex: `EURUSD=X`
* Emtia: `GC=F` (Altın)
""")

# --- AÇILIŞ EKRANI (KONTROL) ---
# Eğer kutu boşsa, hoşgeldin mesajı göster ve dur.
if not symbol_input:
    st.info("👋 **Quant Robotuna Hoşgeldin!**")
    st.markdown("""
    Analize başlamak için sol menüden bir sembol girin (Örn: THYAO.IS).
    """)
    st.stop() # Kod burada durur, aşağıya geçmez.

# TÜRKÇE KARAKTER VE FORMAT DÜZELTME
# Kullanıcı ne yazarsa yazsın (küçük, büyük, noktalı) düzeltiyoruz
symbol = symbol_input.replace('İ', 'I').replace('ı', 'i').upper().strip()

# BIST ÖZEL YAMASI (.IS -> .is dönüşümü)
if symbol.endswith(".IS"):
    symbol = symbol.replace(".IS", ".is")
# --- FONKSİYONLAR ---
@st.cache_data
def veri_getir(sembol, periyot):
    # Robotun deneyeceği kombinasyonlar
    denenecekler = [
        sembol,                                # 1. Senin yazdığın hali
        sembol.upper(),                        # 2. Tamamen büyük (THYAO.IS)
        sembol.upper().replace('.IS', '.is'),  # 3. KÜÇÜK UZANTI (THYAO.is) - Kritik Çözüm
        sembol.lower()                         # 4. Tamamen küçük
    ]

    for s in denenecekler:
        try:
            # Veriyi çekmeye çalış
            df = yf.download(s, period="2y", progress=False)
            
            # Eğer veri geldiyse (boş değilse) işlemi bitir ve gönder
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
        except:
            continue # Hata alırsan çaktırma, sıradakini dene
            
    return None # Hiçbiri tutmazsa pes et

def hesapla(df, window):
    close_price = df['Close'].dropna()
    ma = close_price.rolling(window=window).mean()
    std = close_price.rolling(window=window).std()
    spread = close_price - ma
    z_score = spread / std
    return close_price, ma, std, spread, z_score

# --- ANA PROGRAM ---
if symbol:
    with st.spinner(f'{symbol} verileri analiz ediliyor...'):
        df = veri_getir(symbol, window)

    if df is None:
        st.error("❌ Veri bulunamadı! Sembolü doğru yazdığından emin ol (Örn: THYAO.IS).")
    else:
        # Hesaplamalar
        close, ma, std, spread, z = hesapla(df, window)
        
        # Son Değerler
        last_price = close.iloc[-1]
        last_ma = ma.iloc[-1]
        last_z = z.iloc[-1]
        last_spread = last_price - last_ma

        # --- KARAR MEKANİZMASI ---
        durum_mesaji = ""
        durum_tipi = "info" # success, warning, error, info

        if last_z > z_threshold:
            durum_mesaji = f"🚨 KIRMIZI ALARM! Fiyat aşırı ısındı (+{z_threshold} Sigma). Düşüş ihtimali yüksek."
            durum_tipi = "error" # Kırmızı kutu
        elif last_z > 1.5:
            durum_mesaji = "⚠️ SARI ALARM (ISINIYOR)! Fiyat kritik sınıra yaklaştı. Yeni alım yapma."
            durum_tipi = "warning" # Sarı kutu
        elif last_z < -z_threshold:
            durum_mesaji = f"✅ YEŞİL ALARM! Fiyat aşırı ucuzladı (-{z_threshold} Sigma). Tepki yükselişi ihtimali yüksek."
            durum_tipi = "success" # Yeşil kutu
        elif last_z < -1.5:
            durum_mesaji = "⚠️ SARI ALARM (UCUZLUYOR)! Fiyat düşüş sınırında. Dönüş bekle."
            durum_tipi = "warning"
        else:
            durum_mesaji = "⚖️ NORMAL BÖLGE. Fiyat ortalamalar civarında, ekstrem bir durum yok."
            durum_tipi = "info" # Mavi kutu

        # --- GÖSTERGE PANELİ (METRICS) ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Anlık Fiyat", f"{last_price:.2f}")
        col2.metric("Adil Değer (MA)", f"{last_ma:.2f}")
        col3.metric("Fark (Köpük)", f"{last_spread:.2f}", delta_color="off")
        col4.metric("Z-Score (Gerginlik)", f"{last_z:.2f}", delta_color="inverse")

        # Durum Mesajı
        if durum_tipi == "error": st.error(durum_mesaji)
        elif durum_tipi == "warning": st.warning(durum_mesaji)
        elif durum_tipi == "success": st.success(durum_mesaji)
        else: st.info(durum_mesaji)

        # --- GRAFİKLER ---
        st.markdown("---")
        
        # Grafik Ayarları
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)

        # Grafik 1: Fiyat ve Bantlar
        ax1.plot(close, color='#e0e0e0', label='Fiyat')
        ax1.plot(ma, color='orange', linestyle='--', linewidth=1.5, label=f'{window} Günlük Ortalama')
        ax1.plot(ma + z_threshold*std, color='red', alpha=0.3, label=f'+{z_threshold} Sigma')
        ax1.plot(ma - z_threshold*std, color='lime', alpha=0.3, label=f'-{z_threshold} Sigma')
        ax1.fill_between(close.index, ma + z_threshold*std, ma - z_threshold*std, color='gray', alpha=0.1)
        ax1.set_title(f"{symbol} Fiyat Analizi", fontsize=14, color='white')
        ax1.legend(loc='upper left')
        ax1.grid(alpha=0.15)

        # Grafik 2: Z-Score Radarı
        ax2.plot(z, color='cyan', label='Z-Score', linewidth=1)
        ax2.axhline(z_threshold, color='red', linestyle='--', label='Pahalı')
        ax2.axhline(-z_threshold, color='lime', linestyle='--', label='Ucuz')
        ax2.axhline(0, color='white', alpha=0.3)
        
        # Boyama
        ax2.fill_between(z.index, z, z_threshold, where=(z > z_threshold), color='red', alpha=0.6)
        ax2.fill_between(z.index, z, -z_threshold, where=(z < -z_threshold), color='lime', alpha=0.6)
        
        ax2.set_title("Z-Score Radarı (Gerginlik Ölçer)", fontsize=14, color='white')
        ax2.legend(loc='upper left')
        ax2.grid(alpha=0.15)

        st.pyplot(fig)
