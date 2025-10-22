# 🔒 Güvenlik Önlemleri

Bu proje için uygulanan güvenlik önlemleri:

## ✅ Uygulanan Güvenlik Katmanları

### 1. Backend Authentication
- ✅ Admin şifresi **backend**'de saklanıyor (`ADMIN_PASSWORD` env variable)
- ✅ Frontend'de şifre **görünmüyor**
- ✅ `/api/admin-auth` endpoint üzerinden doğrulama
- ✅ Brute force koruması (1 saniye delay)

### 2. Input Validation
- ✅ Email formatı doğrulanıyor (regex)
- ✅ Wallet adresi formatı kontrol ediliyor (`0x` + 40 hex)
- ✅ Payment hash formatı doğrulanıyor (`0x` + 64 hex)
- ✅ XSS saldırılarına karşı korumalı

### 3. Database Security (RLS)
- ✅ Row Level Security (RLS) aktif
- ✅ **INSERT**: Sadece public (form gönderimi)
- ✅ **UPDATE**: Sadece service_role (backend)
- ✅ **DELETE**: Sadece service_role (backend)
- ✅ Unauthorized update engellendi

### 4. Payment Verification
- ✅ Blockchain üzerinden ödeme doğrulaması
- ✅ Doğru alıcı adresi kontrolü
- ✅ Sahte payment hash tespiti

### 5. API Security
- ✅ CORS yapılandırması
- ✅ Method restriction (sadece POST)
- ✅ Error handling
- ✅ Rate limiting (brute force protection)

---

## ⚠️ ÖNEMLİ NOTLAR

### Production Deployment için:

1. **Environment Variables**:
   ```env
   # .env dosyasında MUTLAKA ayarlayın:
   ADMIN_PASSWORD=your_strong_password_here  # Karmaşık şifre kullanın
   SUPABASE_SERVICE_ROLE_KEY=your_service_key  # Service role key ekleyin
   MAILJET_API_KEY=your_mailjet_key
   MAILJET_SECRET_KEY=your_mailjet_secret
   EMAIL_FROM=license@planc.space
   ```

2. **Supabase RLS Politikaları**:
   - `supabase/migrations/20251022_secure_policies.sql` dosyasını çalıştırın
   - Eski güvensiz politikaları silin

3. **CORS Ayarları**:
   - Production'da `Access-Control-Allow-Origin` değerini domain'inize göre ayarlayın
   - Wildcard (`*`) kullanmayın

4. **Rate Limiting**:
   - Vercel/Cloudflare üzerinden rate limiting ekleyin
   - DDoS koruması için CDN kullanın

5. **HTTPS**:
   - MUTLAKA HTTPS kullanın
   - SSL sertifikası yükleyin

---

## 🚨 Hala Dikkat Edilmesi Gerekenler

### Orta Risk:
1. **Session Management**: JWT token implementasyonu eklenebilir
2. **Rate Limiting**: Form submission için client-side rate limit yok
3. **Email Verification**: Email doğrulaması yok

### Düşük Risk:
1. **CAPTCHA**: Bot koruması için CAPTCHA eklenebilir
2. **2FA**: Admin paneli için iki faktörlü kimlik doğrulama
3. **Audit Log**: Admin işlemlerini log'lama

---

## 📝 Güvenlik Checklist

### Deployment Öncesi:
- [ ] `.env` dosyasında ADMIN_PASSWORD değiştirildi
- [ ] Supabase RLS politikaları güncellendi
- [ ] CORS ayarları production domain'e göre ayarlandı
- [ ] HTTPS aktif
- [ ] Service role key güvenli şekilde saklandı
- [ ] Email credentials güvenli
- [ ] Rate limiting aktif

### İzleme:
- [ ] Failed login attempts monitör ediliyor
- [ ] Supabase logs kontrol ediliyor
- [ ] Unusual activity detection

---

## 🔐 Güvenlik İhlali Durumunda

1. Hemen ADMIN_PASSWORD değiştirin
2. Supabase service key'i rotate edin
3. Mailjet credentials'ı yenileyin
4. Database'de suspicious activity kontrol edin
5. Logs'u inceleyin

---

## 📧 İletişim

Güvenlik açığı bulursanız lütfen rapor edin:
- Email: security@planc.space
- Responsible disclosure policy

---

**Son Güncelleme**: 22 Ekim 2025


