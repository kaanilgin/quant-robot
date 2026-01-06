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
st.set_page_config(page_title="Quant Robot v6.0 - PRO", layout="wide")

# Grafikleri koyu tema yapalım (Terminal havası için)
plt.style.use('dark_background')

# --- DOSYA YÖNETİMİ (HAFIZA SİSTEMİ) ---
DOSYA_ADI = "robot_cuzdan.json"

def verileri_yukle():
    if os.path.exists(DOSYA_ADI):
        try:
            with open(DOSYA_ADI, "r") as f:
                return json.load(f)
        except: return None
    return None

def verileri_kaydet(bakiye, portfoy, islem_gecmisi):
    veri = {"bakiye": bakiye, "portfoy": portfoy, "islem_gecmisi": islem_gecmisi}
    with open(DOSYA_ADI, "w") as f:
        json.dump(veri, f)

# --- BAŞLANGIÇ AYARLARI ---
kayitli_veri = verileri_yukle()
if 'bakiye' not in st.session_state: st.session_state['bakiye'] = kayitli_veri["bakiye"] if kayitli_veri else 100000.0
if 'portfoy' not in st.session_state: st.session_state['portfoy'] = kayitli_veri["portfoy"] if kayitli_veri else {}
if 'islem_gecmisi' not in st.session_state: st.session_state['islem_gecmisi'] = kayitli_veri["islem_gecmisi"] if kayitli_veri else []
if 'tarama_sonuclari' not in st.session_state: st.session_state['tarama_sonuclari'] = None

# --- FONKSİYONLAR ---
@st.cache_data
def veri_getir(sembol, periyot="1y"):
    denenecekler = [sembol, sembol.upper(), sembol.upper().replace('.IS', '.is'), sembol.lower()]
    for s in denenecekler:
        try:
            df = yf.download(s, period=periyot, progress=False)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                return df
        except: continue
    return None

def teknik_hesapla(df, window, z_thresh):
    # Temel Hesaplamalar
    df['SMA'] = df['Close'].rolling(window=window).mean() # Adil Değer
    df['STD'] = df['Close'].rolling(window=window).std()
    
    # Z-Score
    df['Z_Score'] = (df['Close'] - df['SMA']) / df['STD']
    
    # Bantlar (Fiyat Grafiği İçin)
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
            # Rastgele şok
            sok = np.random.normal(mu, sigma)
            fiyatlar.append(fiyatlar[-1] * (1 + sok))
        sim_df[f"Senaryo {x}"] = fiyatlar
    return sim_df

# --- SOL MENÜ ---
st.sidebar.header("⚙️ Ayarlar")
window = st.sidebar.slider("Ortalama (SMA) Günü", 10, 200, 50, 5)
z_threshold = st.sidebar.slider("Hassasiyet (Sigma)", 1.0, 3.0, 2.0, 0.1)

# --- ANA EKRAN ---
st.title("💎 Ultimate Quant Robotu (Web Sürümü)")
tab1, tab2, tab3, tab4 = st.tabs(["📊 PRO Analiz", "📡 Mega Tarayıcı", "🎲 Monte Carlo", "🤖 Canlı Trader"])

# ==========================
# SEKME 1: PRO ANALİZ (YENİLENDİ! 🌟)
# ==========================
with tab1:
    st.subheader("Fiyat & Gerginlik Analizi")
    s_in = st.text_input("Sembol Gir:", value="THYAO.IS", key="analiz_input")
    
    if s_in:
        df = veri_getir(s_in)
        if df is not None:
            df = teknik_hesapla(df, window, z_threshold)
            
            # Son Değerler
            last_p = df['Close'].iloc[-1]
            last_sma = df['SMA'].iloc[-1]
            last_z = df['Z_Score'].iloc[-1]
            fark = last_p - last_sma
            
            # 1. METRİKLER (Screenshottaki gibi)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Anlık Fiyat", f"{last_p:.2f}")
            c2.metric("Adil Değer (MA)", f"{last_sma:.2f}")
            c3.metric("Fark (Köpük)", f"{fark:.2f}")
            c4.metric("Z-Score (Gerginlik)", f"{last_z:.2f}")
            
            # 2. AKILLI UYARI KUTUSU
            if last_z > z_threshold:
                st.error(f"🔴 KIRMIZI ALARM! Fiyat çok şişti ({last_z:.2f} Sigma). Düzeltme gelebilir, ALMA!")
            elif last_z < -z_threshold:
                st.success(f"🟢 YEŞİL ALARM! Fiyat çok ucuzladı ({last_z:.2f} Sigma). Tepki gelebilir, ALIM FIRSATI!")
            elif last_z > (z_threshold * 0.7):
                st.warning("⚠️ SARI ALARM (ISINIYOR)! Fiyat kritik sınıra yaklaştı. Dikkatli ol.")
            elif last_z < -(z_threshold * 0.7):
                st.warning("⚠️ SARI ALARM (SOĞUYOR)! Fiyat dip seviyeye yaklaşıyor.")
            else:
                st.info("⚪ PİYASA NÖTR. Fiyat ortalamalarda geziniyor.")

            # 3. GRAFİK 1: FİYAT VE BANTLAR
            st.markdown("### 📈 Fiyat Analizi")
            fig1, ax1 = plt.subplots(figsize=(12, 5))
            ax1.plot(df.index, df['Close'], color='white', linewidth=1.5, label='Fiyat')
            ax1.plot(df.index, df['SMA'], color='orange', linestyle='--', linewidth=1.5, label=f'{window} Günlük Ort.')
            ax1.plot(df.index, df['Upper'], color='red', alpha=0.3, linewidth=0.5, label='Üst Sınır')
            ax1.plot(df.index, df['Lower'], color='green', alpha=0.3, linewidth=0.5, label='Alt Sınır')
            ax1.fill_between(df.index, df['Upper'], df['Lower'], color='gray', alpha=0.1)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.2)
            st.pyplot(fig1)

            # 4. GRAFİK 2: Z-SCORE (Screenshottaki gibi)
            st.markdown("### ⚡ Z-Score Radarı (Gerginlik Ölçer)")
            fig2, ax2 = plt.subplots(figsize=(12, 4))
            ax2.plot(df.index, df['Z_Score'], color='cyan', linewidth=1.5, label='Z-Score')
            ax2.axhline(z_threshold, color='red', linestyle='--', linewidth=2, label='Pahalı')
            ax2.axhline(-z_threshold, color='green', linestyle='--', linewidth=2, label='Ucuz')
            ax2.axhline(0, color='white', linestyle=':', alpha=0.5)
            
            # Boyamalar (Kırmızı ve Yeşil Alanlar)
            ax2.fill_between(df.index, z_threshold, df['Z_Score'], where=(df['Z_Score'] > z_threshold), color='red', alpha=0.5)
            ax2.fill_between(df.index, -z_threshold, df['Z_Score'], where=(df['Z_Score'] < -z_threshold), color='green', alpha=0.5)
            
            ax2.legend(loc='upper left')
            ax2.grid(True, alpha=0.2)
            st.pyplot(fig2)
            
        else:
            st.error("Veri bulunamadı.")

# ==========================
# SEKME 2: MEGA TARAYICI
# ==========================
with tab2:
    st.subheader("📡 Piyasa Tarayıcısı (BIST + Kripto + FX)")
    
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

    if st.button("🚀 DEV TARAMAYI BAŞLAT"):
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
                    res.append({"Sembol": s.replace(".IS",""), "Fiyat": d['Close'].iloc[-1], "Z-Score": z, "Durum": "🟢 UCUZ" if z < -z_threshold else "🔴 PAHALI" if z > z_threshold else "NÖTR"})
            except: continue
        
        st.session_state['tarama_sonuclari'] = pd.DataFrame(res)
        durum_text.text("✅ Bitti!")

    if st.session_state['tarama_sonuclari'] is not None:
        df_g = st.session_state['tarama_sonuclari'].copy()
        if st.checkbox("Sadece Fırsatları Göster", value=True):
            df_g = df_g[df_g["Durum"] != "NÖTR"]
        st.dataframe(df_g, use_container_width=True)

# ==========================
# SEKME 3: MONTE CARLO (DÜZELTİLDİ 🛠️)
# ==========================
with tab3:
    st.subheader("🎲 Monte Carlo Laboratuvarı")
    st.markdown("Geçmiş volatiliteyi kullanarak 100 farklı gelecek senaryosu üretir.")
    
    col_m1, col_m2 = st.columns([1, 3])
    
    with col_m1:
        mc_sym = st.text_input("Sembol:", value="BTC-USD", key="mc_sym")
        mc_gun = st.slider("Kaç Gün İleri?", 30, 180, 90)
        mc_btn = st.button("Simüle Et 🔮")
        
    with col_m2:
        if mc_btn and mc_sym:
            with st.spinner("Hesaplanıyor..."):
                d_mc = veri_getir(mc_sym)
                if d_mc is not None:
                    # Mevcut Durum Kartları
                    son = d_mc['Close'].iloc[-1]
                    degisim = (son - d_mc['Close'].iloc[-2])
                    yuzde = (degisim / d_mc['Close'].iloc[-2]) * 100
                    
                    m1, m2 = st.columns(2)
                    m1.metric("Şu Anki Fiyat", f"{son:.2f}")
                    m2.metric("Günlük Değişim", f"%{yuzde:.2f}", f"{degisim:.2f}")
                    
                    # Simülasyon
                    sim_df = monte_carlo_simulasyon(d_mc, mc_gun)
                    
                    # Grafik
                    fig_mc, ax_mc = plt.subplots(figsize=(10, 5))
                    # Tüm senaryoları ince çizgilerle çiz
                    ax_mc.plot(sim_df, color='cyan', alpha=0.1, linewidth=0.5)
                    # Ortalamayı kalın çiz
                    ax_mc.plot(sim_df.mean(axis=1), color='yellow', linewidth=2, label='Ortalama Rota')
                    
                    ax_mc.set_title(f"{mc_sym} - {mc_gun} Günlük Gelecek Tahmini")
                    ax_mc.legend()
                    ax_mc.grid(True, alpha=0.2)
                    st.pyplot(fig_mc)
                    
                    # Sonuçlar
                    bitis = sim_df.iloc[-1]
                    k1, k2, k3 = st.columns(3)
                    k1.metric("En Kötü İhtimal", f"{bitis.min():.2f}")
                    k2.metric("Ortalama Beklenti", f"{bitis.mean():.2f}")
                    k3.metric("En İyi İhtimal", f"{bitis.max():.2f}")
                else:
                    st.error("Veri çekilemedi.")

# ==========================
# SEKME 4: CANLI TRADER (HAFIZALI)
# ==========================
with tab4:
    st.subheader("🤖 Otomatik Robot")
    col1, col2 = st.columns(2)
    bakiye = st.session_state['bakiye']
    portfoy = st.session_state['portfoy']
    col1.metric("💵 Nakit", f"{bakiye:,.2f} TL")
    col2.metric("💼 Pozisyonlar", f"{len(portfoy)} Adet")
    
    if st.checkbox("✅ ROBOTU ÇALIŞTIR"):
        st.success("📡 Robot devrede...")
        bot_listesi = ['THYAO.IS', 'GARAN.IS', 'BTC-USD', 'ETH-USD', 'ASELS.IS']
        
        for s in bot_listesi:
            try:
                df = veri_getir(s, "1y")
                if df is not None:
                    df = teknik_hesapla(df, window, z_threshold)
                    z = df['Z_Score'].iloc[-1]
                    fiyat = df['Close'].iloc[-1]
                    tarih = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    if z < -z_threshold and bakiye > fiyat:
                        adet = int(bakiye * 0.10 / fiyat)
                        if adet > 0:
                            bakiye -= adet * fiyat
                            portfoy[s] = portfoy.get(s, 0) + adet
                            st.session_state['islem_gecmisi'].append(f"{tarih} - AL: {s} | {adet} lot")
                            st.toast(f"🟢 ALINDI: {s}")
                    
                    elif z > z_threshold and s in portfoy:
                        adet = portfoy[s]
                        bakiye += adet * fiyat
                        del portfoy[s]
                        st.session_state['islem_gecmisi'].append(f"{tarih} - SAT: {s} | {adet} lot")
                        st.toast(f"🔴 SATILDI: {s}")
            except: continue
            
        st.session_state['bakiye'] = bakiye
        st.session_state['portfoy'] = portfoy
        verileri_kaydet(bakiye, portfoy, st.session_state['islem_gecmisi'])
        time.sleep(10)
        st.rerun()

    if st.session_state['islem_gecmisi']:
        st.write(st.session_state['islem_gecmisi'])
