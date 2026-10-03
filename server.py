"""
🧥 Wearther — Flask Backend API
Hava durumu ve kıyafet öneri sistemi için API sunucusu.
"""

import os
import json
import numpy as np
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask.json.provider import DefaultJSONProvider
from hava_durumu import hava_durumunu_getir, hava_durumu_emoji
from model import (
    tahmin_yap, veri_kaydet, veri_yukle, istatistikler,
    UST_GIYIM_SECENEKLERI, ALT_GIYIM_SECENEKLERI, DIS_GIYIM_SECENEKLERI,
    AYAKKABI_SECENEKLERI, EKSTRA_SECENEKLERI, GERI_BILDIRIM_SECENEKLERI,
    CSV_DOSYASI
)


class NumpyJSONProvider(DefaultJSONProvider):
    """numpy tiplerini JSON'a çevirebilen özel JSON provider."""
    def default(self, o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super().default(o)


app = Flask(__name__, static_folder='static', static_url_path='/static')
app.json_provider_class = NumpyJSONProvider
app.json = NumpyJSONProvider(app)


@app.route('/')
def index():
    """Ana sayfayı sunar."""
    return send_from_directory('static', 'index.html')


@app.route('/api/oneri')
def api_oneri():
    """Hava durumu + kıyafet önerisi döndürür."""
    sehir = request.args.get('sehir', 'Istanbul')
    hava = hava_durumunu_getir(sehir)
    if hava is None:
        return jsonify({'error': 'Hava durumu alınamadı'}), 500

    hava['emoji'] = hava_durumu_emoji(hava.get('aciklama', ''))
    oneri = tahmin_yap(hava['sicaklik'], hava['hissedilen'], hava['nem'], hava['ruzgar'])
    return jsonify({'oneri': oneri, 'hava': hava})


@app.route('/api/kaydet', methods=['POST'])
def api_kaydet():
    """Yeni kıyafet kaydını sisteme ekler."""
    data = request.json
    basarili = veri_kaydet(
        tarih=data['tarih'],
        sicaklik=data['sicaklik'],
        hissedilen=data['hissedilen'],
        nem=data['nem'],
        ruzgar=data['ruzgar'],
        ust=data['ust'],
        alt=data['alt'],
        dis=data['dis'],
        ayakkabi=data['ayakkabi'],
        ekstra=data['ekstra'],
        geri_bildirim=data.get('geri_bildirim', 0),
    )
    return jsonify({'basarili': basarili})


@app.route('/api/gecmis')
def api_gecmis():
    """Tüm geçmiş kayıtları döndürür."""
    df = veri_yukle()
    return jsonify(df.to_dict(orient='records'))


@app.route('/api/istatistikler')
def api_istatistikler():
    """Özet istatistikleri döndürür."""
    return jsonify(istatistikler())


@app.route('/api/son-kayit-sil', methods=['DELETE'])
def api_son_kayit_sil():
    """Son kaydı siler."""
    df = veri_yukle()
    if len(df) > 0:
        df = df.iloc[:-1]
        df.to_csv(CSV_DOSYASI, index=False)
        return jsonify({'basarili': True})
    return jsonify({'basarili': False})


@app.route('/api/indir')
def api_indir():
    """CSV dosyasını indirir."""
    if os.path.exists(CSV_DOSYASI):
        return send_file(CSV_DOSYASI, as_attachment=True,
                         download_name='kiyafet_verileri_yedek.csv')
    return jsonify({'error': 'Dosya bulunamadı'}), 404


@app.route('/api/secenekler')
def api_secenekler():
    """Dropdown seçeneklerini döndürür."""
    return jsonify({
        'ust_giyim': UST_GIYIM_SECENEKLERI,
        'alt_giyim': ALT_GIYIM_SECENEKLERI,
        'dis_giyim': DIS_GIYIM_SECENEKLERI,
        'ayakkabi': AYAKKABI_SECENEKLERI,
        'ekstra': EKSTRA_SECENEKLERI,
        'geri_bildirim': {str(k): v for k, v in GERI_BILDIRIM_SECENEKLERI.items()},
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
