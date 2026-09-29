# 🧥 Wearther — Akıllı Kıyafet Öneri Sistemi

Wearther, bulunduğunuz şehrin anlık hava durumu verilerini çekerek, o gün için en uygun kıyafetleri öneren makine öğrenmesi destekli akıllı bir web uygulamasıdır. Siz her gün ne giydiğinizi uygulamaya girdikçe, uygulama sizin tercihlerinizi öğrenir ve gelecekteki hava durumlarına göre daha isabetli kişiselleştirilmiş öneriler sunar.

## ✨ Özellikler

- ⛅ **Canlı Hava Durumu:** OpenWeatherMap API kullanarak dilediğiniz şehrin anlık sıcaklık, hissedilen sıcaklık, nem ve rüzgar verilerini çeker.
- 🧠 **Makine Öğrenmesi (KNN):** K-En Yakın Komşu (K-Nearest Neighbors) algoritması sayesinde, geçmiş verilerinizi analiz ederek yeni hava durumlarına en uygun kıyafet kombinini (Üst Giyim, Alt Giyim, Dış Giyim, Ayakkabı, Ekstra) önerir.
- 📈 **Sürekli Öğrenme:** Uygulamaya girdiğiniz her yeni kıyafet/hava durumu kaydı, modelin kendini güncellemesini ve size daha özel öneriler sunmasını sağlar.
- 📊 **İstatistikler:** Hangi hava koşullarında neleri tercih ettiğinizi gösteren analiz ve istatistik sayfası.
- 🎨 **Modern ve Kullanıcı Dostu Arayüz:** Streamlit kullanılarak geliştirilmiş, göz yormayan, modern ve şık bir arayüz.

## 🛠️ Teknolojiler

- **[Python 3.8+](https://www.python.org/)**
- **[Streamlit](https://streamlit.io/)**: Kullanıcı arayüzü (UI) geliştirme.
- **[Scikit-learn](https://scikit-learn.org/)**: Makine öğrenmesi (K-Nearest Neighbors algoritması) ve veri ölçekleme.
- **[Pandas](https://pandas.pydata.org/)**: Veri manipülasyonu (`kiyafet_verileri.csv` üzerinde).
- **[OpenWeatherMap API](https://openweathermap.org/)**: Gerçek zamanlı hava durumu verisi sağlama.
- **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Çevresel değişkenleri (API key) güvenli bir şekilde yönetme.

## 🚀 Nasıl Çalıştırılır?

Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla takip edin:

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/iremnisabas/Wearther.git
cd Wearther
```

### 2. Sanal Ortam (Virtual Environment) Oluşturun (Önerilen)

```bash
# Windows için
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux için
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Gerekli Kütüphaneleri Yükleyin

```bash
pip install -r requirements.txt
```

### 4. API Anahtarınızı Ayarlayın

Proje hava durumu verilerini çekebilmek için **OpenWeatherMap API** kullanmaktadır.

1. [OpenWeatherMap](https://home.openweathermap.org/users/sign_up) adresinden ücretsiz bir hesap oluşturun ve bir API anahtarı alın.
2. Proje ana dizininde bulunan `.env.example` dosyasının adını `.env` olarak değiştirin veya yeni bir `.env` dosyası oluşturun.
3. İçine kendi API anahtarınızı ekleyin:

```env
OPENWEATHER_API_KEY=sizin_api_anahtariniz_buraya
```

### 5. Uygulamayı Başlatın

Tüm kurulumlar tamamlandıktan sonra uygulamayı çalıştırmak için aşağıdaki komutu girin:

```bash
streamlit run app.py
```

Tarayıcınız otomatik olarak açılacak ve uygulama `http://localhost:8501` adresinde çalışmaya başlayacaktır.

## 📊 Proje Analizi ve Mantığı

Uygulama arka planda üç temel adımla çalışır:

1. **Veri Toplama:** `hava_durumu.py` üzerinden girilen şehrin o anki hava durumu (sıcaklık, hissedilen sıcaklık vb.) çekilir.
2. **Tahmin (Prediction):** `model.py` içindeki KNN (K-Nearest Neighbors) algoritması, anlık hava durumu verilerini alır ve daha önce kaydedilmiş olan `kiyafet_verileri.csv` veri setindeki geçmiş günlerle karşılaştırır. Hava durumu açısından en çok benzeyen geçmiş günleri bularak bir kombin önerisi ve bu önerinin 'Güven Skoru'nu oluşturur.
3. **Öğrenme (Training):** Kullanıcı, uygulamanın arayüzünden o gün gerçekten ne giydiğini sisteme kaydettiğinde, bu veri yeni bir satır olarak CSV dosyasına eklenir. Bir sonraki tahminde model bu yeni veriyi de hesaba katarak isabet oranını artırır.

## 🤝 Katkıda Bulunma

Eğer projeye katkıda bulunmak isterseniz:
1. Projeyi fork'layın.
2. Yeni bir özellik dalı (branch) oluşturun (`git checkout -b yeni-ozellik`).
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`).
4. Dalınızı (branch) push'layın (`git push origin yeni-ozellik`).
5. Bir Pull Request oluşturun.

## 👤 Geliştirici

- **İrem Nisa Baş** — [@iremnisabas](https://github.com/iremnisabas)
