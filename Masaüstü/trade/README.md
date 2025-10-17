# Binance Futures Trading Bot

Modern, kullanıcı dostu Tkinter GUI ile Binance vadeli işlemler trading bot'u.

## Özellikler

### 🎨 Modern GUI
- Koyu tema ile modern arayüz
- Gerçek zamanlı fiyat grafiği
- Pozisyon yönetimi tablosu
- Detaylı log sistemi

### 📊 Trading Özellikleri
- **Long/Short Pozisyonlar**: Market emirleri ile hızlı pozisyon açma
- **Leverage Ayarı**: 1x - 20x arası leverage seçimi
- **Pozisyon Yönetimi**: Tüm pozisyonları tek tıkla kapatma
- **Gerçek Zamanlı Fiyat**: 1 saniye aralıkla güncellenen fiyat bilgileri
- **Symbol Seçimi**: Popüler kripto çiftleri (BTC, ETH, ADA, SOL, DOGE)

### 🔒 Güvenlik
- API key şifrelenmiş gösterim
- Otomatik config kaydetme/yükleme
- Hata yönetimi ve loglama
- Risk kontrolü

## Kurulum

### 1. Gereksinimler
```bash
pip install python-binance matplotlib pandas numpy
```

### 2. Bot'u Çalıştır
```bash
python binance_futures_bot.py
```

## Kullanım

### 1. API Ayarları
1. Binance hesabınızdan API Key ve Secret oluşturun
2. **Futures Trading** iznini etkinleştirin
3. Bot'ta API bilgilerini girin ve "Bağlan" butonuna tıklayın

### 2. Trading
1. **Symbol seçin** (BTCUSDT, ETHUSDT, vb.)
2. **Position Size** girin (USDT cinsinden)
3. **Leverage** seçin (1-20x arası)
4. **LONG** veya **SHORT** butonuna tıklayın

### 3. Pozisyon Yönetimi
- Açık pozisyonlar otomatik olarak tabloda görünür
- **"Tüm Pozisyonları Kapat"** ile hepsini kapatabilirsiniz
- PNL (Kar/Zarar) gerçek zamanlı güncellenir

## ⚠️ Önemli Notlar

### Testnet vs Mainnet
- **TEST İÇİN**: Kod'da `testnet=True` yapın (219. satır)
- **GERÇEK TİCARET İÇİN**: `testnet=False` (varsayılan)

### Risk Yönetimi
- Küçük miktarlarla başlayın
- Stop loss kullanmayı unutmayın
- Leverage ile dikkatli olun
- Sadece kaybetmeyi göze alabileceğiniz para ile işlem yapın

### API İzinleri
Binance API'nızda şu izinlerin aktif olması gerekir:
- ✅ **Enable Reading**
- ✅ **Enable Futures** 
- ❌ **Enable Withdrawals** (güvenlik için kapalı tutun)

## Dosya Yapısı

```
trade/
├── binance_futures_bot.py  # Ana bot dosyası
├── config.json            # API ayarları (otomatik oluşur)
└── README.md              # Bu dosya
```

## Sorun Giderme

### Bağlantı Hataları
- API key/secret doğru mu?
- Futures trading izni var mı?
- İnternet bağlantınız stable mi?

### Trading Hataları
- Yeterli bakiyeniz var mı?
- Symbol'ın minimum order miktarını karşılıyor musunuz?
- API rate limit'ine takılmış olabilirsiniz

## Gelişmiş Özellikler

Bot'a eklenebilecek özellikler:
- 🎯 Stop Loss / Take Profit otomasyonu
- 📈 Teknik analiz indikatörleri
- 🤖 Otomatik trading stratejileri
- 📨 Telegram/Email bildirimleri
- 💾 Trading geçmişi kaydetme

## ⚡ Hızlı Başlangıç

1. **API bilgilerinizi hazırlayın**
2. **Bot'u çalıştırın**: `python binance_futures_bot.py`
3. **API bilgilerini girin** ve bağlanın
4. **Küçük bir miktarla test edin**
5. **İyi ticaatlar! 💰**

## Uyarı

Bu bot eğitim amaçlıdır. Finansal tavsiye değildir. Kendi sorumluluğunuzda kullanın.

---

**🚀 Happy Trading!**