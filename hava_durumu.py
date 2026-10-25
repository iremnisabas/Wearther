"""
Hava Durumu Modülü
OpenWeatherMap API kullanarak anlık hava durumunu çeker.
"""

import requests
from datetime import datetime, timezone

import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# OpenWeatherMap API anahtarı artık .env'den alınıyor
DEFAULT_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Anlık ve tahmin verisini harmanlama ağırlıkları
ANLIK_AGIRLIK = 0.6   # Anlık verinin ağırlığı (%60)
TAHMIN_AGIRLIK = 0.4   # 6 saatlik ortalamanın ağırlığı (%40)

SEHIR_DUZELTMELERI = {
    "Istanbul": "İstanbul",
    "Uskudar": "Üsküdar",
    "Izmir": "İzmir",
    "Canakkale": "Çanakkale",
    "Mugla": "Muğla",
    "Eskisehir": "Eskişehir",
    "Sanliurfa": "Şanlıurfa",
    "Diyarbakir": "Diyarbakır",
    "Nigde": "Niğde",
    "Tekirdag": "Tekirdağ",
    "Kirsehir": "Kırşehir",
    "Kirikkale": "Kırıkkale",
    "Balikesir": "Balıkesir",
    "Gumushane": "Gümüşhane",
    "Sirnak": "Şırnak",
    "Usak": "Uşak",
    "Igdir": "Iğdır",
    "Agri": "Ağrı",
    "Bingol": "Bingöl",
    "Elazig": "Elazığ",
    "Kutahya": "Kütahya",
    "Cankiri": "Çankırı",
    "Corum": "Çorum",
    "Karabuk": "Karabük",
    "Aydin": "Aydın",
    "Kirklareli": "Kırklareli"
}

def hava_durumunu_getir(sehir: str, api_key: str = None) -> dict | None:
    """
    Verilen şehir için anlık hava durumunu OpenWeatherMap API'den çeker.

    Args:
        sehir: Hava durumu sorgulanacak şehir adı (örn: "Istanbul")
        api_key: OpenWeatherMap API anahtarı

    Returns:
        Hava durumu bilgilerini içeren dict veya hata durumunda None
    """
    key = api_key or DEFAULT_API_KEY
    if not key:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": sehir,
        "appid": key,
        "units": "metric",  # Celsius cinsinden
        "lang": "tr",       # Türkçe açıklamalar
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        ham_sehir = data["name"]
        duzeltilmis_sehir = SEHIR_DUZELTMELERI.get(ham_sehir, ham_sehir)

        return {
            "sehir": duzeltilmis_sehir,
            "sicaklik": round(data["main"]["temp"], 1),
            "hissedilen": round(data["main"]["feels_like"], 1),
            "nem": data["main"]["humidity"],
            "ruzgar": round(data["wind"]["speed"] * 3.6, 1),  # m/s → km/h
            "aciklama": data["weather"][0]["description"].capitalize(),
            "ikon": data["weather"][0]["icon"],
            "tarih": datetime.now().strftime("%Y-%m-%d"),
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ Hava durumu alınamadı: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"❌ Hava durumu verisi işlenemedi: {e}")
        return None


def hava_ikonu_url(ikon_kodu: str) -> str:
    """OpenWeatherMap ikon URL'si oluşturur."""
    return f"https://openweathermap.org/img/wn/{ikon_kodu}@2x.png"


def hava_durumu_emoji(aciklama: str) -> str:
    """Hava durumu açıklamasına göre emoji döndürür."""
    aciklama_lower = aciklama.lower()
    if "güneş" in aciklama_lower or "açık" in aciklama_lower:
        return "☀️"
    elif "kapalı" in aciklama_lower or "çok bulutlu" in aciklama_lower:
        return "☁️"
    elif "az bulut" in aciklama_lower:
        return "🌤️"
    elif "bulut" in aciklama_lower or "parçalı" in aciklama_lower:
        return "⛅"
    elif "yağmur" in aciklama_lower:
        return "🌧️"
    elif "kar" in aciklama_lower:
        return "❄️"
    elif "fırtına" in aciklama_lower or "gök gürültü" in aciklama_lower:
        return "⛈️"
    elif "sis" in aciklama_lower or "pus" in aciklama_lower:
        return "🌫️"
    else:
        return "🌤️"


def _tahmin_verisi_getir(sehir: str, api_key: str = None) -> list[dict] | None:
    """
    OpenWeatherMap 3-saatlik tahmin API'sinden önümüzdeki ~6 saatlik
    hava verilerini çeker.

    Returns:
        6 saat içindeki tahmin dilimlerinin listesi veya hata durumunda None
    """
    key = api_key or DEFAULT_API_KEY
    if not key:
        return None

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": sehir,
        "appid": key,
        "units": "metric",
        "lang": "tr",
        "cnt": 3,  # 3 dilim × 3 saat = 9 saat (ilk 2 dilim ≈ 6 saat)
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        simdi = datetime.now(timezone.utc).timestamp()
        alti_saat_sonra = simdi + 6 * 3600

        dilimler = []
        for item in data.get("list", []):
            dt = item["dt"]
            if dt <= alti_saat_sonra:
                dilimler.append({
                    "sicaklik": item["main"]["temp"],
                    "hissedilen": item["main"]["feels_like"],
                    "nem": item["main"]["humidity"],
                    "ruzgar": item["wind"]["speed"] * 3.6,  # m/s → km/h
                })
        return dilimler if dilimler else None

    except Exception as e:
        print(f"❌ Tahmin verisi alınamadı: {e}")
        return None


def tahmin_icin_hava_getir(sehir: str, api_key: str = None) -> dict | None:
    """
    Kıyafet tahmini için optimize edilmiş hava verisi döndürür.

    Anlık hava durumunu (%60 ağırlık) ve önümüzdeki 6 saatin
    ortalamasını (%40 ağırlık) birleştirerek daha isabetli bir
    "hissedilen hava" üretir.

    Eğer tahmin verisi alınamazsa salt anlık verileri kullanır.

    Returns:
        Hem görüntüleme (anlık) hem tahmin (harmanlanmış) verisi içeren dict
    """
    # 1) Anlık hava durumunu al
    anlik = hava_durumunu_getir(sehir, api_key)
    if anlik is None:
        return None

    # 2) 6 saatlik tahmin ortalamasını al
    tahmin_dilimleri = _tahmin_verisi_getir(sehir, api_key)

    if tahmin_dilimleri:
        # Tahmin dilimlerinin ortalamasını hesapla
        ort_sicaklik = sum(d["sicaklik"] for d in tahmin_dilimleri) / len(tahmin_dilimleri)
        ort_hissedilen = sum(d["hissedilen"] for d in tahmin_dilimleri) / len(tahmin_dilimleri)
        ort_nem = sum(d["nem"] for d in tahmin_dilimleri) / len(tahmin_dilimleri)
        ort_ruzgar = sum(d["ruzgar"] for d in tahmin_dilimleri) / len(tahmin_dilimleri)

        # Anlık × %60 + Tahmin ortalaması × %40
        anlik["tahmin_sicaklik"] = round(
            anlik["sicaklik"] * ANLIK_AGIRLIK + ort_sicaklik * TAHMIN_AGIRLIK, 1
        )
        anlik["tahmin_hissedilen"] = round(
            anlik["hissedilen"] * ANLIK_AGIRLIK + ort_hissedilen * TAHMIN_AGIRLIK, 1
        )
        anlik["tahmin_nem"] = round(
            anlik["nem"] * ANLIK_AGIRLIK + ort_nem * TAHMIN_AGIRLIK, 1
        )
        anlik["tahmin_ruzgar"] = round(
            anlik["ruzgar"] * ANLIK_AGIRLIK + ort_ruzgar * TAHMIN_AGIRLIK, 1
        )
        anlik["tahmin_kaynagi"] = "harmanlanmis"  # anlık + 6 saat ortalama
    else:
        # Tahmin verisi yoksa anlık değerleri doğrudan kullan
        anlik["tahmin_sicaklik"] = anlik["sicaklik"]
        anlik["tahmin_hissedilen"] = anlik["hissedilen"]
        anlik["tahmin_nem"] = anlik["nem"]
        anlik["tahmin_ruzgar"] = anlik["ruzgar"]
        anlik["tahmin_kaynagi"] = "anlik"  # salt anlık

    return anlik

