"""
🧥 Wearther — Akıllı Kıyafet Öneri Sistemi
Hava durumuna göre makine öğrenmesi ile kıyafet önerisi yapar.
Her gün veri girdikçe daha akıllı hale gelir.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from hava_durumu import hava_durumunu_getir, hava_ikonu_url, hava_durumu_emoji
from model import (
    tahmin_yap, veri_kaydet, veri_yukle, istatistikler,
    UST_GIYIM_SECENEKLERI, ALT_GIYIM_SECENEKLERI, DIS_GIYIM_SECENEKLERI,
    AYAKKABI_SECENEKLERI, EKSTRA_SECENEKLERI, GERI_BILDIRIM_SECENEKLERI
)

# ────────────────────────────────────────────────────────
# Sayfa Konfigürasyonu
# ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wearther — Akıllı Kıyafet Önerisi",
    page_icon="🧥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────────────────
# Custom CSS — Premium Görünüm
# ────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Sadece Deploy butonunu gizle (Menü ve yan panel açma/kapama geri gelsin) */
    .stDeployButton {display:none;}

    /* Başlıkların yanındaki bağlantı/aksiyon butonlarını gizle */
    [data-testid="stHeaderActionElements"],
    .stHeaderActionElements {
        display: none !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stTextInput label {
        color: #a78bfa !important;
        font-weight: 600;
    }

    /* Hava durumu kartı */
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 28px 32px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    .weather-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -30%;
        width: 300px;
        height: 300px;
        background: rgba(255, 255, 255, 0.06);
        border-radius: 50%;
    }
    .weather-card h2 {
        margin: 0 0 4px 0;
        font-size: 18px;
        font-weight: 500;
        opacity: 0.9;
    }
    .weather-card .temp {
        font-size: 56px;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 8px;
    }
    .weather-card .details {
        display: flex;
        gap: 24px;
        font-size: 14px;
        opacity: 0.85;
        flex-wrap: wrap;
    }
    .weather-card .details span {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Öneri kartı */
    .recommendation-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(167, 139, 250, 0.2);
        border-radius: 20px;
        padding: 28px 32px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
    }
    .recommendation-card h3 {
        color: #a78bfa;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 12px;
        font-weight: 600;
    }
    .recommendation-card .item {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .recommendation-card .confidence {
        font-size: 13px;
        color: #8b8b9e;
    }

    /* Güven bar */
    .confidence-bar {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        height: 6px;
        margin-top: 8px;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #667eea, #a78bfa);
        transition: width 0.5s ease;
    }

    /* Benzer gün kartı */
    .similar-day {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        color: #ccc;
    }
    .similar-day .date {
        color: #a78bfa;
        font-weight: 600;
        font-size: 13px;
    }

    /* Stat kartları */
    .stat-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(167, 139, 250, 0.15);
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        color: white;
    }
    .stat-card .value {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stat-card .label {
        font-size: 12px;
        color: #8b8b9e;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 4px;
    }

    /* Başarı bildirimi */
    .success-toast {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        border-radius: 12px;
        padding: 16px 24px;
        color: white;
        font-weight: 500;
        margin: 16px 0;
    }

    /* Info kutusu */
    .info-box {
        background: rgba(167, 139, 250, 0.08);
        border-left: 3px solid #a78bfa;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        color: #d4d4d8;
        margin: 16px 0;
        font-size: 14px;
    }

    /* Tab stili */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 10px 24px;
        font-weight: 600;
    }

    /* Form alanları iyileştirmesi */
    .stSelectbox > div > div {
        border-radius: 12px !important;
    }

    /* Tablo stili */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Alternatifler */
    .alt-chip {
        display: inline-block;
        background: rgba(167, 139, 250, 0.12);
        border: 1px solid rgba(167, 139, 250, 0.25);
        border-radius: 20px;
        padding: 4px 14px;
        margin: 3px 4px;
        font-size: 13px;
        color: #c4b5fd;
    }
</style>
""", unsafe_allow_html=True)


# ────────────────────────────────────────────────────────
# Sidebar — Ayarlar & Şehir Seçimi
# ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧥 Wearther")
    st.markdown("*Akıllı Kıyafet Önerisi*")
    st.markdown("---")

    st.markdown("### ⚙️ Ayarlar")

    sehir = st.text_input(
        "📍 Şehir",
        value=st.session_state.get("sehir", "Istanbul"),
        placeholder="Şehir adını yazın...",
    )
    st.session_state["sehir"] = sehir

    st.markdown("---")

    # İstatistikler
    stats = istatistikler()
    if stats["toplam"] > 0:
        st.markdown("### 📊 Özet")
        st.markdown(f"**Toplam Kayıt:** {stats['toplam']}")
        st.markdown(f"**En Sık Üst:** {stats.get('en_sik_ust', '-')}")
        st.markdown(f"**En Sık Alt:** {stats.get('en_sik_alt', '-')}")
        st.markdown(f"**Ort. Sıcaklık:** {stats.get('ort_sicaklik', '-')}°C")


# ────────────────────────────────────────────────────────
# Hava Durumunu Al
# ────────────────────────────────────────────────────────
hava = hava_durumunu_getir(sehir)

if hava is None:
    st.error("❌ Hava durumu verisi alınamadı. Lütfen API bağlantınızı kontrol edin.")
    st.stop()


# ────────────────────────────────────────────────────────
# Ana İçerik — Sekmeler
# ────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 Günlük Öneri", "👕 Bugün Ne Giydin?", "📋 Geçmiş Verilerim"])


# ═══════════════════════════════════════════════════════
# SEKME 1: Günlük Öneri
# ═══════════════════════════════════════════════════════
with tab1:
    emoji = hava_durumu_emoji(hava.get("aciklama", ""))

    # Hava durumu kartı
    st.markdown(f"""
    <div class="weather-card">
        <h2>{emoji} {hava['sehir']} — {hava['aciklama']}</h2>
        <div class="temp">{hava['sicaklik']}°C</div>
        <div class="details">
            <span>🌡️ Hissedilen: {hava['hissedilen']}°C</span>
            <span>💧 Nem: {hava['nem']}%</span>
            <span>💨 Rüzgar: {hava['ruzgar']} km/h</span>
            <span>📅 {datetime.now().strftime('%d %B %Y')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tahmin yap
    oneri = tahmin_yap(hava["sicaklik"], hava["hissedilen"], hava["nem"], hava["ruzgar"])

    if oneri is None:
        st.markdown("""
        <div class="info-box">
            🧠 <strong>Henüz yeterli veri yok.</strong><br>
            Sistemin seni tanıması için "Bugün Ne Giydin?" sekmesinden en az 3 gün veri girmelisin.
            Ne kadar çok veri girersen, öneriler o kadar isabetli olur!
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### 🤖 Yapay Zeka Önerisi")

        col1, col2, col3 = st.columns(3)

        with col1:
            ust = oneri["ust_giyim"]
            alt_chips = " ".join(
                [f'<span class="alt-chip">{a["kiyafet"]} %{a["oran"]}</span>'
                 for a in ust["alternatifler"][1:3]]
            )
            st.markdown(f"""
            <div class="recommendation-card">
                <h3>👕 Üst Giyim</h3>
                <div class="item">{ust['tahmin']}</div>
                <div class="confidence">Güven: %{ust['guven']}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {ust['guven']}%"></div>
                </div>
                <div style="margin-top:12px">{alt_chips}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            alt = oneri["alt_giyim"]
            alt_chips2 = " ".join(
                [f'<span class="alt-chip">{a["kiyafet"]} %{a["oran"]}</span>'
                 for a in alt["alternatifler"][1:3]]
            )
            st.markdown(f"""
            <div class="recommendation-card">
                <h3>👖 Alt Giyim</h3>
                <div class="item">{alt['tahmin']}</div>
                <div class="confidence">Güven: %{alt['guven']}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {alt['guven']}%"></div>
                </div>
                <div style="margin-top:12px">{alt_chips2}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            dis = oneri["dis_giyim"]
            alt_chips3 = " ".join(
                [f'<span class="alt-chip">{a["kiyafet"]} %{a["oran"]}</span>'
                 for a in dis["alternatifler"][1:3]]
            )
            st.markdown(f"""
            <div class="recommendation-card">
                <h3>🧥 Dış Giyim</h3>
                <div class="item">{dis['tahmin']}</div>
                <div class="confidence">Güven: %{dis['guven']}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {dis['guven']}%"></div>
                </div>
                <div style="margin-top:12px">{alt_chips3}</div>
            </div>
            """, unsafe_allow_html=True)

        col4, col5 = st.columns(2)

        with col4:
            ayakkabi = oneri["ayakkabi"]
            alt_chips4 = " ".join(
                [f'<span class="alt-chip">{a["kiyafet"]} %{a["oran"]}</span>'
                 for a in ayakkabi["alternatifler"][1:3]]
            )
            st.markdown(f"""
            <div class="recommendation-card">
                <h3>👟 Ayakkabı</h3>
                <div class="item">{ayakkabi['tahmin']}</div>
                <div class="confidence">Güven: %{ayakkabi['guven']}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {ayakkabi['guven']}%"></div>
                </div>
                <div style="margin-top:12px">{alt_chips4}</div>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            ekstra = oneri["ekstra"]
            alt_chips5 = " ".join(
                [f'<span class="alt-chip">{a["kiyafet"]} %{a["oran"]}</span>'
                 for a in ekstra["alternatifler"][1:3]]
            )
            st.markdown(f"""
            <div class="recommendation-card">
                <h3>🧣 Ekstralar</h3>
                <div class="item">{ekstra['tahmin']}</div>
                <div class="confidence">Güven: %{ekstra['guven']}</div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {ekstra['guven']}%"></div>
                </div>
                <div style="margin-top:12px">{alt_chips5}</div>
            </div>
            """, unsafe_allow_html=True)

        # Benzer günler
        if oneri["benzer_gunler"]:
            st.markdown("### 📅 Bu Havaya En Benzer Geçmiş Günler")
            for gun in oneri["benzer_gunler"][:3]:
                st.markdown(f"""
                <div class="similar-day">
                    <span class="date">📌 {gun['tarih']}</span> —
                    🌡️ {gun['sicaklik']}°C (hiss: {gun['hissedilen']}°C) &nbsp;
                    💧 %{gun['nem']} &nbsp; 💨 {gun['ruzgar']} km/h
                    <br>
                    👕 {gun['ust']} &nbsp;|&nbsp; 👖 {gun['alt']} &nbsp;|&nbsp; 🧥 {gun['dis']} &nbsp;|&nbsp; 👟 {gun['ayakkabi']} &nbsp;|&nbsp; 🧣 {gun['ekstra']}
                    &nbsp;&nbsp; {gun.get('geri_bildirim_etiket', '')}
                </div>
                """, unsafe_allow_html=True)

        # Veri sayısı bilgisi
        st.markdown(f"""
        <div class="info-box">
            📈 Model şu an <strong>{oneri['toplam_veri']}</strong> günlük veriyle eğitildi.
            Ne kadar çok veri girersen, öneriler o kadar kişiselleşir!
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════
# SEKME 2: Bugün Ne Giydin?
# ═══════════════════════════════════════════════════════
with tab2:
    st.markdown("### 👕 Bugün Ne Giydiğini Kaydet")
    st.markdown("""
    <div class="info-box">
        🧠 Her kayıt sistemi daha akıllı yapar. Bugünkü hava durumuyla birlikte
        giydiğin kıyafetleri kaydet — yapay zeka senin tarzını öğrensin!
    </div>
    """, unsafe_allow_html=True)

    # Mevcut hava durumu özeti
    st.markdown(f"""
    <div class="weather-card" style="padding: 18px 24px;">
        <h2 style="font-size:14px; margin:0;">📍 Bugünkü Hava — {hava['sehir']}</h2>
        <div class="details" style="margin-top:8px;">
            <span>🌡️ {hava['sicaklik']}°C</span>
            <span>🤒 Hiss: {hava['hissedilen']}°C</span>
            <span>💧 %{hava['nem']}</span>
            <span>💨 {hava['ruzgar']} km/h</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("kiyafet_formu", clear_on_submit=True):
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            secilen_ust = st.selectbox(
                "👕 Üst Giyim",
                UST_GIYIM_SECENEKLERI,
                index=0,
            )
        with col_b:
            secilen_alt = st.selectbox(
                "👖 Alt Giyim",
                ALT_GIYIM_SECENEKLERI,
                index=1,
            )
        with col_c:
            secilen_dis = st.selectbox(
                "🧥 Dış Giyim",
                DIS_GIYIM_SECENEKLERI,
                index=0,
            )

        col_d, col_e, col_f = st.columns(3)
        with col_d:
            secilen_ayakkabi = st.selectbox(
                "👟 Ayakkabı",
                AYAKKABI_SECENEKLERI,
                index=0,
            )
        with col_e:
            secilen_ekstra = st.selectbox(
                "🧣 Ekstra (Opsiyonel)",
                EKSTRA_SECENEKLERI,
                index=0,
            )
        with col_f:
            gb_secenekler = list(GERI_BILDIRIM_SECENEKLERI.values())
            gb_anahtarlar = list(GERI_BILDIRIM_SECENEKLERI.keys())
            secilen_gb_idx = st.selectbox(
                "🎯 Nasıl Hissettin?",
                range(len(gb_secenekler)),
                format_func=lambda i: gb_secenekler[i],
                index=1,  # Varsayılan: Tam Kararında
                help="Bu geri bildirim, yapı zekanın kendini düzeltmesini sağlar.",
            )
            secilen_geri_bildirim = gb_anahtarlar[secilen_gb_idx]

        gonder = st.form_submit_button(
            "💾 Sisteme Kaydet ve Öğret",
            use_container_width=True,
            type="primary",
        )

        if gonder:
            basarili = veri_kaydet(
                tarih=hava["tarih"],
                sicaklik=hava["sicaklik"],
                hissedilen=hava["hissedilen"],
                nem=hava["nem"],
                ruzgar=hava["ruzgar"],
                ust=secilen_ust,
                alt=secilen_alt,
                dis=secilen_dis,
                ayakkabi=secilen_ayakkabi,
                ekstra=secilen_ekstra,
                geri_bildirim=secilen_geri_bildirim,
            )
            if basarili:
                st.markdown(f"""
                <div class="success-toast">
                    ✅ Kaydedildi! {secilen_ust} + {secilen_alt} + {secilen_dis} + {secilen_ayakkabi}
                    — Sistem bu veriyi öğrendi 🧠
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
            else:
                st.error("❌ Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.")


# ═══════════════════════════════════════════════════════
# SEKME 3: Geçmiş Verilerim
# ═══════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📋 Tüm Geçmiş Kayıtlar")

    df = veri_yukle()

    if df.empty:
        st.markdown("""
        <div class="info-box">
            📭 Henüz hiç kayıt yok. "Bugün Ne Giydin?" sekmesinden ilk kaydını gir!
        </div>
        """, unsafe_allow_html=True)
    else:
        # İstatistik kartları
        stats = istatistikler()
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="value">{stats['toplam']}</div>
                <div class="label">Toplam Kayıt</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="value">{stats.get('ort_sicaklik', '-')}°</div>
                <div class="label">Ort. Sıcaklık</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="value">{stats.get('min_sicaklik', '-')}°</div>
                <div class="label">Min Sıcaklık</div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="value">{stats.get('max_sicaklik', '-')}°</div>
                <div class="label">Max Sıcaklık</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Sütun isimlerini güzelleştir
        gorunum_df = df.copy()
        # Geri bildirim değerlerini emoji etiketlere çevir
        gorunum_df["Geri_Bildirim"] = gorunum_df["Geri_Bildirim"].map(
            GERI_BILDIRIM_SECENEKLERI
        ).fillna("❓")
        gorunum_df.columns = [
            "📅 Tarih", "🌡️ Sıcaklık", "🤒 Hissedilen",
            "💧 Nem", "💨 Rüzgar", "👕 Üst", "👖 Alt", "🧥 Dış", "👟 Ayakkabı", "🧣 Ekstra",
            "🎯 Geri Bildirim"
        ]

        # Tabloyu ters sırala (en yeni üstte)
        gorunum_df = gorunum_df.iloc[::-1].reset_index(drop=True)

        st.dataframe(
            gorunum_df,
            use_container_width=True,
            hide_index=True,
            height=450,
        )

        # CSV İndirme
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Verileri CSV Olarak İndir",
            data=csv_data,
            file_name="kiyafet_verileri_yedek.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Silme işlemi
        st.markdown("---")
        with st.expander("🗑️ Son Kaydı Sil"):
            st.warning("Bu işlem geri alınamaz!")
            if st.button("Son kaydı sil", type="secondary"):
                if len(df) > 0:
                    df = df.iloc[:-1]
                    df.to_csv(
                        __import__("model").CSV_DOSYASI,
                        index=False,
                    )
                    st.success("Son kayıt silindi. Sayfa yenileniyor...")
                    st.rerun()


# ────────────────────────────────────────────────────────
# Footer
# ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#666; font-size:13px;'>"
    "🧥 Wearther v1.0 — Yapay zeka destekli kıyafet öneri sistemi<br>"
    "Her gün veri girdikçe daha akıllı olur ✨"
    "</p>",
    unsafe_allow_html=True,
)
