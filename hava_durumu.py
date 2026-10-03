"""
Hava Durumu Modülü
OpenWeatherMap API kullanarak anlık hava durumunu çeker.
"""

import requests
from datetime import datetime

import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# OpenWeatherMap API anahtarı artık .env'den alınıyor
DEFAULT_API_KEY = os.getenv("OPENWEATHER_API_KEY")

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
