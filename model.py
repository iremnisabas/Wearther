"""
Makine Öğrenmesi Modülü
KNN (K-Nearest Neighbors) algoritması ile kıyafet tahmini yapar.
Her yeni veri girişiyle model daha akıllı hale gelir.
"""

import os
import pandas as pd
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime

# Proje kök dizinindeki CSV dosyası
CSV_DOSYASI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kiyafet_verileri.csv")

# Kıyafet seçenekleri — kullanıcı arayüzünde açılır menülerde gösterilecek
UST_GIYIM_SECENEKLERI = [
    "Askılı Tişört", "Kısa kollu Tişört", "Uzun kollu Tişört",
    "İnce Kazak", "Kalın Kazak", "Sweatshirt"
]

ALT_GIYIM_SECENEKLERI = [
    "Etek", "Şort", "Eşofman", "Kot pantolon",
    "Kumaş Pantolon", "İnce Kumaş pantolon"
]

DIS_GIYIM_SECENEKLERI = [
    "Yok", "Mont", "Hırka", "Ceket"
]

AYAKKABI_SECENEKLERI = [
    "Bot", "Spor Ayakkabı", "Crocs"
]

EKSTRA_SECENEKLERI = [
    "Yok", "Atkı", "Şemsiye"
]


def veri_yukle() -> pd.DataFrame:
    """CSV dosyasından mevcut kıyafet verilerini yükler."""
    if not os.path.exists(CSV_DOSYASI):
        return pd.DataFrame(columns=[
            "Tarih", "Sicaklik", "Hissedilen", "Nem",
            "Ruzgar", "Ust_Giyim", "Alt_Giyim", "Dis_Giyim", "Ayakkabi", "Ekstra"
        ])
    return pd.read_csv(CSV_DOSYASI)


def veri_kaydet(tarih: str, sicaklik: float, hissedilen: float,
                nem: int, ruzgar: float, ust: str, alt: str, dis: str, ayakkabi: str, ekstra: str) -> bool:
    """
    Yeni bir kıyafet kaydını CSV dosyasına ekler.

    Returns:
        True = başarılı, False = hata
    """
    try:
        df = veri_yukle()
        yeni_satir = pd.DataFrame([{
            "Tarih": tarih,
            "Sicaklik": sicaklik,
            "Hissedilen": hissedilen,
            "Nem": nem,
            "Ruzgar": ruzgar,
            "Ust_Giyim": ust,
            "Alt_Giyim": alt,
            "Dis_Giyim": dis,
            "Ayakkabi": ayakkabi,
            "Ekstra": ekstra,
        }])
        df = pd.concat([df, yeni_satir], ignore_index=True)
        df.to_csv(CSV_DOSYASI, index=False)
        return True
    except Exception:
        return False


def tahmin_yap(sicaklik: float, hissedilen: float, nem: int, ruzgar: float) -> dict | None:
    """
    KNN algoritması ile mevcut hava durumuna en uygun kıyafet önerisini üretir.

    Her kıyafet kategorisi (üst, alt, dış) için ayrı birer KNN modeli eğitilir.
    Hava verileri StandardScaler ile ölçeklenir, sonra tahmin yapılır.
    Ayrıca en yakın komşu günlerin bilgileri de detay olarak döndürülür.

    Args:
        sicaklik: Anlık sıcaklık (°C)
        hissedilen: Hissedilen sıcaklık (°C)
        nem: Nem oranı (%)
        ruzgar: Rüzgar hızı (km/h)

    Returns:
        Öneri sözlüğü veya veri yetersizse None
    """
    df = veri_yukle()

    # Yeterli veri kontrolü
    if len(df) < 3:
        return None

    # Feature'lar (hava verileri) ve label'lar (kıyafetler)
    ozellikler = ["Sicaklik", "Hissedilen", "Nem", "Ruzgar"]
    X = df[ozellikler].values
    y_ust = df["Ust_Giyim"].values
    y_alt = df["Alt_Giyim"].values
    y_dis = df["Dis_Giyim"].values
    y_ayakkabi = df["Ayakkabi"].values
    y_ekstra = df["Ekstra"].values

    # Ölçekleme — farklı birimlerdeki verileri eşitler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # K sayısını veriye göre dinamik ayarla (çok az veriyse daha küçük k)
    k = min(5, len(df))

    # Her kategori için ayrı KNN modeli
    sonuclar = {}
    benzer_gunler_indices = None

    for kategori, y in [("ust", y_ust), ("alt", y_alt), ("dis", y_dis), ("ayakkabi", y_ayakkabi), ("ekstra", y_ekstra)]:
        model = KNeighborsClassifier(n_neighbors=k, weights="distance")
        model.fit(X_scaled, y)

        yeni_veri = scaler.transform([[sicaklik, hissedilen, nem, ruzgar]])
        tahmin = model.predict(yeni_veri)[0]

        # Olasılık dağılımı (güven skoru)
        olasiliklar = model.predict_proba(yeni_veri)[0]
        siniflar = model.classes_
        en_yuksek_idx = np.argmax(olasiliklar)
        guven = round(olasiliklar[en_yuksek_idx] * 100, 1)

        sonuclar[kategori] = {
            "tahmin": tahmin,
            "guven": guven,
            "alternatifler": [
                {"kiyafet": siniflar[i], "oran": round(olasiliklar[i] * 100, 1)}
                for i in np.argsort(olasiliklar)[::-1]
                if olasiliklar[i] > 0.05  # %5'ten düşük ihtimalleri elemek
            ],
        }

        # En yakın komşu günleri sadece bir kez bul
        if benzer_gunler_indices is None:
            mesafeler, indeksler = model.kneighbors(yeni_veri)
            benzer_gunler_indices = indeksler[0]

    # Benzer günlerin detayları
    benzer_gunler = []
    if benzer_gunler_indices is not None:
        for idx in benzer_gunler_indices:
            row = df.iloc[idx]
            benzer_gunler.append({
                "tarih": row["Tarih"],
                "sicaklik": row["Sicaklik"],
                "hissedilen": row["Hissedilen"],
                "nem": row["Nem"],
                "ruzgar": row["Ruzgar"],
                "ust": row["Ust_Giyim"],
                "alt": row["Alt_Giyim"],
                "dis": row["Dis_Giyim"],
                "ayakkabi": row["Ayakkabi"],
                "ekstra": row["Ekstra"],
            })

    return {
        "ust_giyim": sonuclar["ust"],
        "alt_giyim": sonuclar["alt"],
        "dis_giyim": sonuclar["dis"],
        "ayakkabi": sonuclar["ayakkabi"],
        "ekstra": sonuclar["ekstra"],
        "benzer_gunler": benzer_gunler,
        "toplam_veri": len(df),
    }


def istatistikler() -> dict:
    """Geçmiş verilere dair özet istatistikler üretir."""
    df = veri_yukle()
    if df.empty:
        return {"toplam": 0}

    return {
        "toplam": len(df),
        "en_sik_ust": df["Ust_Giyim"].mode().iloc[0] if not df["Ust_Giyim"].mode().empty else "-",
        "en_sik_alt": df["Alt_Giyim"].mode().iloc[0] if not df["Alt_Giyim"].mode().empty else "-",
        "en_sik_dis": df["Dis_Giyim"].mode().iloc[0] if not df["Dis_Giyim"].mode().empty else "-",
        "ort_sicaklik": round(df["Sicaklik"].mean(), 1),
        "min_sicaklik": df["Sicaklik"].min(),
        "max_sicaklik": df["Sicaklik"].max(),
    }
