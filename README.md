# PlanC Binance Futures Trading Bot

[![GitHub release](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/PlanC90/plancbinance)
[![License](https://img.shields.io/badge/license-Commercial-red.svg)](https://license.planc.space/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/PlanC90/plancbinance)

**Otomatik Kripto Vadeli İşlem Trading Botu**

Binance Futures üzerinde piyasa analizi ve momentum takibi ile otomatik alım-satım yapan profesyonel trading botu.

---

## 🚀 Özellikler

### 🤖 Akıllı Trading Sistemi
- **Otomatik Piyasa Analizi**: Top 100 coin'in momentum analizi
- **Trend Takibi**: Piyasa yükseliş/düşüş/neutral tespiti
- **Momentum Kaybı Koruması**: Ani trend değişimlerinde otomatik pozisyon kapatma
- **Multi-Coin Trading**: 20'ye kadar aynı anda farklı coinlerle işlem yapma

### 💰 Risk Yönetimi
- **Stop Loss**: Otomatik zarar durdurma
- **Take Profit**: Otomatik kar alma
- **Leverage Kontrolü**: 1x - 20x arası kaldıraç desteği (lisans gerektirir)
- **Bakiye Yönetimi**: Trade başına bakiye yüzdesi ayarlama

### 📊 Canlı Veriler
- **Gerçek Zamanlı Fiyat**: Binance API'den canlı fiyat takibi
- **Hesap Özeti**: Toplam PNL, pozisyonlar, bakiye
- **Haberler**: Crypto haberleri (Türkçe/İngilizce)

### 🌍 Çoklu Dil Desteği
25+ dil desteği (Türkçe, İngilizce, İspanyolca, Fransızca, Almanca, Rusça, Arapça, Çince, Japonca, Korece ve daha fazlası)

### 🔄 Otomatik Güncelleme
GitHub üzerinden tek tıkla otomatik güncelleme

---

## 📦 İndirme ve Kurulum

### Windows (.exe)

1. **[GitHub Releases](https://github.com/PlanC90/plancbinance/releases)** sayfasından `BinanceFuturesBot.exe` dosyasını indirin
2. İndirilen `.exe` dosyasını çalıştırın
3. Program otomatik olarak açılacaktır

### macOS/Linux (Kaynak Kodu)

```bash
# Repository'yi klonlayın
git clone https://github.com/PlanC90/plancbinance.git
cd plancbinance

# Gereklilikler
pip install -r requirements.txt

# Programı başlatın
python main.py
```

---

## 🔑 Hızlı Başlangıç

### 1. API Anahtarları Alma

1. [Binance](https://www.binance.com/en/my/settings/api-management) hesabınıza giriş yapın
2. "API Oluştur" butonuna tıklayın
3. İzinleri ayarlayın:
   - ✅ Reading
   - ✅ Futures
   - ❌ Spot & Margin Trading (Güvenlik için kapalı tutun)
   - ❌ Withdrawals (Mutlaka kapalı tutun!)
4. API Key ve Secret Key'inizi kopyalayın

### 2. Programı Çalıştırma

1. **Test Modunda Başlatın** (Ortam: Test)
2. API Key ve Secret Key'inizi girin
3. "Bağlan" butonuna tıklayın
4. ✅ "Bağlandı ✓" görünene kadar bekleyin

### 3. Trading Yapmak İçin

1. Sol panelden coin seçin
2. Trading ayarlarınızı yapın:
   - **Kaldıraç**: 1x - 5x (önerilen başlangıç)
   - **Bakiye %**: 10% - 30% (önerilen)
   - **Stop Loss**: 5% - 15%
   - **Kar Al**: 3% - 10%
3. ">> Oto Trade" butonuna tıklayın

### 4. Pozisyon Kontrolü

- **Açık Pozisyonlar** bölümünden aktif işlemlerinizi takip edin
- Gerçek zamanlı PNL görüntüleyin
- İstediğiniz pozisyonu manuel kapatabilirsiniz

---

## 📖 Kullanım Kılavuzu

Programın içinde bulunan **"📖 Kullanım Kılavuzu"** butonuna tıklayarak detaylı kullanım bilgileri alabilirsiniz.

### Önemli Ayarlar

| Ayar | Önerilen Değer | Açıklama |
|------|----------------|----------|
| Piyasa Trend Eşiği | 60 | Piyasanın yükseliş/düşüş sayısı |
| Momentum Kaybı Eşiği | 8 | Pozisyonların kapanacağı değişim miktarı |
| Kaldıraç | 1x - 3x | Başlangıç için düşük kaldıraç |
| Stop Loss | 10% | Zarar durdurma yüzdesi |
| Kar Al | 3% | Otomatik kar alma yüzdesi |
| Piyasa Kontrol Süresi | 60 saniye | Piyasa analizi aralığı |

---

## 🔐 Lisans

### Lisanssız Kullanım
- **Maksimum Kaldıraç**: 1x
- Özellik kısıtlaması yok
- Tüm trading özellikleri aktif

### Lisanslı Kullanım
- **Maksimum Kaldıraç**: 20x
- Daha yüksek potansiyel karlar
- Profesyonel trading için ideal

### Lisans Alma
**Yalnızca resmi siteden**: [https://license.planc.space/](https://license.planc.space/)

⚠️ **ÖNEMLİ**: Başka kaynaklardan alınan lisanslar kullanılamaz ve programı bozabilir!

---

## ⚠️ Risk Uyarısı

1. **Test Modu ile Başlayın**: İlk kullanım için mutlaka test modunda deneyin
2. **Sadece Kaybetmeyi Göze Alabileceğiniz Para**: Tüm tasarrufunuzu yatırmayın
3. **Stop Loss Kullanın**: Her zaman stop loss kullanın
4. **Kaldıraç Riskini Anlayın**: Yüksek kaldıraç = yüksek risk
5. **Past Performance ≠ Future Results**: Geçmiş karlar gelecek sonuçları garanti etmez

---

## 🆘 Destek

- **Website**: [https://planc.space](https://planc.space)
- **Lisans**: [https://license.planc.space/](https://license.planc.space/)
- **Email**: support@planc.space
- **GitHub**: [https://github.com/PlanC90/plancbinance](https://github.com/PlanC90/plancbinance)

---

## 🔄 Güncelleme

Program otomatik olarak GitHub'dan güncellemeleri kontrol eder:
- Başlangıçta otomatik kontrol (3 saniye sonra)
- "[↓] Update" butonu ile manuel kontrol
- Yeni güncelleme varsa otomatik bildirim

### Manuel Güncelleme
1. GitHub'dan en son release'i indirin
2. Eski programı kapatın
3. Yeni `.exe` dosyasını çalıştırın

---

## 📝 Değişiklik Geçmişi

### v1.0.0 (Mevcut)
- ✅ Multi-coin trading desteği
- ✅ Otomatik piyasa analizi
- ✅ Momentum kaybı koruması
- ✅ 25+ dil desteği
- ✅ Otomatik güncelleme sistemi
- ✅ Binance Testnet desteği
- ✅ Gerçek zamanlı haberler

---

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz!
1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Push edin (`git push origin feature/AmazingFeature`)
5. Pull Request açın

---

## 📄 Lisans

Bu yazılım ticari bir üründür. Tüm hakları PlanC'ye aittir.

Kullanım için lisans şartları:
- Kişisel veya ticari kullanım için lisans gerekir
- Lisanssız kullanımda maksimum 1x kaldıraç
- Lisans için: [https://license.planc.space/](https://license.planc.space/)

---

## 🌟 Özellik İstekleri

Gerçekleştirmek istediğiniz özellikler için:
- **GitHub Issues**: [https://github.com/PlanC90/plancbinance/issues](https://github.com/PlanC90/plancbinance/issues)
- **Email**: support@planc.space

---

## ⭐ Projeyi Beğendiniz mi?

GitHub'da ⭐ vererek bizi destekleyebilirsiniz!

---

**© 2025 PlanC. Tüm hakları saklıdır.**

**NOTLAR:**
- Bu bot karlılık garantisi vermez
- Crypto trading yüksek risk taşır
- Sadece kaybetmeyi göze alabileceğiniz para ile trade yapın
- Kaldıraç risklerini iyi anlayın
- İlk başlarda küçük miktarlarla test edin

