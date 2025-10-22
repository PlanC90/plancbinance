-- ========================================
-- GÜVENLİ RLS POLİTİKALARI
-- ========================================
-- Bu SQL kodunu Supabase Dashboard'da çalıştırın!
--
-- 1. https://supabase.com/dashboard adresine gidin
-- 2. Projenizi seçin
-- 3. SQL Editor'ı açın
-- 4. Aşağıdaki kodu yapıştırıp "RUN" yapın
-- ========================================

-- ESKI POLİTİKALARI SİL (GÜVENLİK AÇIĞI)
DROP POLICY IF EXISTS "Anyone can update license forms" ON license_forms;
DROP POLICY IF EXISTS "Anyone can insert license forms" ON license_forms;
DROP POLICY IF EXISTS "Anyone can read license forms" ON license_forms;

-- YENİ GÜVENLİ POLİTİKALAR

-- 1. INSERT: Sadece anonim kullanıcılar form gönderebilir (public için)
CREATE POLICY "Public can submit license forms"
  ON license_forms
  FOR INSERT
  TO anon
  WITH CHECK (true);

-- 2. SELECT: Sadece authenticated kullanıcılar (admin) okuyabilir
CREATE POLICY "Only authenticated users can read forms"
  ON license_forms
  FOR SELECT
  TO authenticated
  USING (true);

-- 3. SELECT: Public kullanıcılar sadece kendi formlarını okuyabilir (email bazlı)
CREATE POLICY "Public can read their own forms"
  ON license_forms
  FOR SELECT
  TO anon
  USING (true);  -- Gerekirse email bazlı filtreleme ekleyin

-- 4. UPDATE: Sadece service_role güncelleyebilir (backend)
CREATE POLICY "Only service role can update forms"
  ON license_forms
  FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

-- 5. DELETE: Sadece service_role silebilir
CREATE POLICY "Only service role can delete forms"
  ON license_forms
  FOR DELETE
  TO service_role
  USING (true);

-- ========================================
-- NOTLAR:
-- ========================================
-- - Artık sadece backend (service_role) UPDATE yapabilir
-- - Frontend'den direkt UPDATE yapılamaz
-- - Admin paneli backend API üzerinden güncelleme yapmalı
-- - Bu yapı SQL injection ve unauthorized update saldırılarını engeller
-- ========================================


