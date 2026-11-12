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


# Geri bildirim etiketleri — kullanıcı arayüzünde gösterilecek
GERI_BILDIRIM_SECENEKLERI = {
    -1: "🥶 Üşüdüm",
     0: "👌 Tam Kararında",
     1: "🥵 Terledim",
}


# ─── Isı Puanları (Hibrit Termal Düzeltme Katmanı) ───
# Her kıyafetin ne kadar sıcak tuttuğunu gösteren sabit puanlar.
# Yüksek puan = daha sıcak tutar.
ISI_PUANLARI = {
    "ust": {"Askılı Tişört": 1, "Kısa kollu Tişört": 2, "Uzun kollu Tişört": 3,
            "İnce Kazak": 4, "Sweatshirt": 5, "Kalın Kazak": 6},
    "dis": {"Yok": 0, "Ceket": 2, "Hırka": 3, "Mont": 6},
    "alt": {"Şort": 1, "Etek": 1, "İnce Kumaş pantolon": 1,
            "Kumaş Pantolon": 2, "Kot pantolon": 3, "Eşofman": 3},
    "ayakkabi": {"Crocs": 1, "Spor Ayakkabı": 2, "Bot": 3},
    "ekstra": {"Yok": 0, "Şemsiye": 0, "Atkı": 1},
}

# Sadece bu kategoriler kaydırılır (uyumsuz kombinleri önlemek için)
ISITMA_SIRASI = ["ust", "dis"]      # üşüme: önce üst, sonra dış
SERINLETME_SIRASI = ["dis", "ust"]  # terleme: önce dış, sonra üst

TERMAL_ESIK = 0.34        # sinyal bu değeri aşarsa düzeltme yapılır
TERMAL_KOMSU_SAYISI = 5   # bakılacak benzer gün sayısı
PUAN_TOLERANSI = 1        # "aynı sıcaklıkta kombin" sayılma toleransı

# CSV sütun adları ↔ kategori anahtarları
KATEGORI_SUTUNLARI = {
    "ust": "Ust_Giyim", "alt": "Alt_Giyim", "dis": "Dis_Giyim",
    "ayakkabi": "Ayakkabi", "ekstra": "Ekstra",
}


def _parca_puani(kategori: str, kiyafet: str) -> float:
    """Tek bir kıyafetin ısı puanı. Bilinmeyen kıyafet için kategori ortalaması."""
    tablo = ISI_PUANLARI.get(kategori, {})
    if kiyafet in tablo:
        return tablo[kiyafet]
    return float(np.mean(list(tablo.values()))) if tablo else 0.0


def kombin_puani(kombin: dict) -> float:
    """Kombinin toplam ısı puanı. kombin: {"ust": ..., "alt": ..., ...}"""
    return sum(_parca_puani(k, kombin.get(k)) for k in ISI_PUANLARI)


def _bir_basamak_kaydir(kategori: str, mevcut: str, yon: int) -> str | None:
    """
    Kıyafeti ısı sıralamasında bir basamak kaydırır.
    yon=+1 → daha sıcak, yon=-1 → daha serin. Uçtaysa None döner.
    """
    tablo = ISI_PUANLARI.get(kategori, {})
    if mevcut not in tablo:
        return None
    mevcut_puan = tablo[mevcut]
    if yon > 0:
        adaylar = [(p, k) for k, p in tablo.items() if p > mevcut_puan]
        return min(adaylar)[1] if adaylar else None
    adaylar = [(p, k) for k, p in tablo.items() if p < mevcut_puan]
    return max(adaylar)[1] if adaylar else None


def termal_duzeltme(kombin: dict, hava_vektoru: list, df: pd.DataFrame,
                    scaler: StandardScaler) -> dict:
    """
    KNN önerisini geçmiş geri bildirimlere göre ısı ekseninde düzeltir.

    Bugünün havasına en yakın günler (TÜM kayıtlar, geri bildirimler dahil)
    bulunur. Bunlardan kombin puanı önerilen kombine yakın olanların
    mesafe ağırlıklı geri bildirim ortalaması "termal sinyal"dir:
      sinyal ≤ -eşik → bir basamak ısıt, sinyal ≥ +eşik → bir basamak serinlet.
    """
    puan_once = kombin_puani(kombin)
    sonuc = {
        "uygulandi": False, "yon": None, "sinyal": 0.0,
        "degisiklikler": [], "puan_once": puan_once, "puan_sonra": puan_once,
        "ornek_gun": None,
    }
    if df.empty:
        return sonuc

    ozellikler = ["Sicaklik", "Hissedilen", "Nem", "Ruzgar"]
    X_tum = scaler.transform(df[ozellikler].values)
    sorgu = scaler.transform([hava_vektoru])[0]
    mesafeler = np.linalg.norm(X_tum - sorgu, axis=1)

    k = min(TERMAL_KOMSU_SAYISI, len(df))
    en_yakinlar = np.argsort(mesafeler)[:k]

    toplam_agirlik, agirlikli_gb = 0.0, 0.0
    ilgili = []  # (mesafe, gb, satır)
    for idx in en_yakinlar:
        satir = df.iloc[idx]
        satir_kombin = {kat: satir[sutun] for kat, sutun in KATEGORI_SUTUNLARI.items()}
        if abs(kombin_puani(satir_kombin) - puan_once) > PUAN_TOLERANSI:
            continue  # farklı sıcaklıkta kombin → bu öneri hakkında bilgi vermez
        gb = int(satir.get("Geri_Bildirim", 0) or 0)
        agirlik = 1.0 / (mesafeler[idx] + 1e-3)
        toplam_agirlik += agirlik
        agirlikli_gb += agirlik * gb
        ilgili.append((mesafeler[idx], gb, satir))

    if toplam_agirlik == 0:
        return sonuc

    sinyal = agirlikli_gb / toplam_agirlik
    sonuc["sinyal"] = round(float(sinyal), 2)

    if sinyal <= -TERMAL_ESIK:
        yon, sira, hedef_gb = +1, ISITMA_SIRASI, -1
    elif sinyal >= TERMAL_ESIK:
        yon, sira, hedef_gb = -1, SERINLETME_SIRASI, 1
    else:
        return sonuc

    # Tek basamak: sıradaki ilk kaydırılabilir kategori
    for kategori in sira:
        yeni = _bir_basamak_kaydir(kategori, kombin.get(kategori), yon)
        if yeni:
            sonuc["degisiklikler"].append({
                "kategori": kategori, "onceki": kombin[kategori], "yeni": yeni,
            })
            break

    if not sonuc["degisiklikler"]:
        return sonuc

    yeni_kombin = dict(kombin)
    for d in sonuc["degisiklikler"]:
        yeni_kombin[d["kategori"]] = d["yeni"]

    # Açıklama için sinyale en çok katkı veren (en yakın) olumsuz gün
    ornekler = sorted([x for x in ilgili if x[1] == hedef_gb], key=lambda x: x[0])
    if ornekler:
        s = ornekler[0][2]
        sonuc["ornek_gun"] = {
            "tarih": s["Tarih"], "sicaklik": float(s["Sicaklik"]),
            "ust": s["Ust_Giyim"], "dis": s["Dis_Giyim"],
        }

    sonuc.update({
        "uygulandi": True,
        "yon": "isit" if yon > 0 else "serinlet",
        "puan_sonra": kombin_puani(yeni_kombin),
    })
    return sonuc


def veri_yukle() -> pd.DataFrame:
    """CSV dosyasından mevcut kıyafet verilerini yükler."""
    if not os.path.exists(CSV_DOSYASI):
        return pd.DataFrame(columns=[
            "Tarih", "Sicaklik", "Hissedilen", "Nem",
            "Ruzgar", "Ust_Giyim", "Alt_Giyim", "Dis_Giyim", "Ayakkabi", "Ekstra",
            "Geri_Bildirim"
        ])
    df = pd.read_csv(CSV_DOSYASI)
    # Eski veri setlerinde Geri_Bildirim sütunu yoksa ekle (varsayılan: 0 = Tam Kararında)
    if "Geri_Bildirim" not in df.columns:
        df["Geri_Bildirim"] = 0
    return df


def veri_kaydet(tarih: str, sicaklik: float, hissedilen: float,
                nem: int, ruzgar: float, ust: str, alt: str, dis: str,
                ayakkabi: str, ekstra: str, geri_bildirim: int = 0) -> bool:
    """
    Yeni bir kıyafet kaydını CSV dosyasına ekler.

    Args:
        geri_bildirim: -1 (Üşüdüm), 0 (Tam Kararında), 1 (Terledim)

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
            "Geri_Bildirim": geri_bildirim,
        }])
        df = pd.concat([df, yeni_satir], ignore_index=True)
        df.to_csv(CSV_DOSYASI, index=False)
        return True
    except Exception:
        return False


def geribildirim_guncelle(index: int, yeni_geribildirim: int, tarih: str = None) -> bool:
    """
    Belirtilen indeksteki kaydın geri bildirimini günceller.

    Args:
        index: Satır indeksi
        yeni_geribildirim: -1 (Üşüdüm), 0 (Tam Kararında), 1 (Terledim)
        tarih: Opsiyonel güvenlik doğrulaması için tarih dizesi

    Returns:
        True = başarılı, False = hata
    """
    try:
        df = veri_yukle()
        if 0 <= index < len(df):
            # Tarih verilmişse ve indeks uyuşmuyorsa, tarihi eşleşen satırı bul
            if tarih and str(df.at[index, "Tarih"]) != str(tarih):
                eslesenler = df[df["Tarih"] == str(tarih)].index
                if len(eslesenler) > 0:
                    index = eslesenler[0]
            df.at[index, "Geri_Bildirim"] = int(yeni_geribildirim)
            df.to_csv(CSV_DOSYASI, index=False)
            return True
        return False
    except Exception as e:
        print(f"Geri bildirim güncellenirken hata: {e}")
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
    # Geri bildirim tabanlı veri filtreleme:
    # "Tam Kararında" (0) olan kayıtlar tercih edilir — model rahat hissedilen
    # kombinlerden öğrenir. Yeterli "iyi" veri yoksa tüm veri kullanılır.
    iyi_veriler = df[df["Geri_Bildirim"] == 0]
    if len(iyi_veriler) >= 3:
        egitim_df = iyi_veriler
    else:
        egitim_df = df

    # Feature'lar ve label'lar filtrelenmiş veriden alınır
    X = egitim_df[ozellikler].values
    y_ust = egitim_df["Ust_Giyim"].values
    y_alt = egitim_df["Alt_Giyim"].values
    y_dis = egitim_df["Dis_Giyim"].values
    y_ayakkabi = egitim_df["Ayakkabi"].values
    y_ekstra = egitim_df["Ekstra"].values

    # Ölçekleme — farklı birimlerdeki verileri eşitler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # K sayısını veriye göre dinamik ayarla (çok az veriyse daha küçük k)
    k = min(5, len(egitim_df))

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

    # ─── Hibrit katman: geri bildirime göre ısı düzeltmesi ───
    kombin = {kat: sonuclar[kat]["tahmin"] for kat in KATEGORI_SUTUNLARI}
    isi_duzeltme = termal_duzeltme(kombin, [sicaklik, hissedilen, nem, ruzgar], df, scaler)
    for d in isi_duzeltme["degisiklikler"]:
        kat = d["kategori"]
        sonuclar[kat]["knn_tahmin"] = sonuclar[kat]["tahmin"]
        sonuclar[kat]["tahmin"] = d["yeni"]
        sonuclar[kat]["duzeltildi"] = True

    # Benzer günlerin detayları
    benzer_gunler = []
    if benzer_gunler_indices is not None:
        for idx in benzer_gunler_indices:
            row = egitim_df.iloc[idx]
            gb = int(row.get("Geri_Bildirim", 0))
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
                "geri_bildirim": gb,
                "geri_bildirim_etiket": GERI_BILDIRIM_SECENEKLERI.get(gb, "❓"),
            })

    return {
        "ust_giyim": sonuclar["ust"],
        "alt_giyim": sonuclar["alt"],
        "dis_giyim": sonuclar["dis"],
        "ayakkabi": sonuclar["ayakkabi"],
        "ekstra": sonuclar["ekstra"],
        "benzer_gunler": benzer_gunler,
        "toplam_veri": len(df),
        "isi_duzeltme": isi_duzeltme,
    }


def istatistikler() -> dict:
    """Geçmiş verilere dair özet istatistikler üretir."""
    df = veri_yukle()
    if df.empty:
        return {"toplam": 0}

    # Geri bildirim istatistikleri
    gb = df["Geri_Bildirim"].value_counts()
    tam_karari = int(gb.get(0, 0))
    usudum = int(gb.get(-1, 0))
    terledim = int(gb.get(1, 0))

    return {
        "toplam": len(df),
        "en_sik_ust": df["Ust_Giyim"].mode().iloc[0] if not df["Ust_Giyim"].mode().empty else "-",
        "en_sik_alt": df["Alt_Giyim"].mode().iloc[0] if not df["Alt_Giyim"].mode().empty else "-",
        "en_sik_dis": df["Dis_Giyim"].mode().iloc[0] if not df["Dis_Giyim"].mode().empty else "-",
        "ort_sicaklik": round(df["Sicaklik"].mean(), 1),
        "min_sicaklik": df["Sicaklik"].min(),
        "max_sicaklik": df["Sicaklik"].max(),
        "gb_tam_karari": tam_karari,
        "gb_usudum": usudum,
        "gb_terledim": terledim,
    }
