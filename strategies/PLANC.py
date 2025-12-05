try:
    from .base_strategy import BaseStrategy
except Exception:
    from base_strategy import BaseStrategy

from typing import Dict, List, Optional

class PLANCStrategy(BaseStrategy):
    """
    PLANC Strategy
    ------------------------------------------
    1. Trend Takibi: SuperTrend (10, 3.0)
    2. Testere Koruması: ADX > 25
    3. Trailing Stop: PLANC Akıllı Trailing Stop
    4. Kar Koruması: Breakeven Trigger
    """
    DEFAULTS = {
        "strategy_name": "PLANC Strategy",
        "atr_period": 10,
        "atr_multiplier": 3.0,
        "adx_period": 14,
        "adx_threshold": 25, 
    }

    def __init__(self, bot, **kwargs):
        cfg = dict(self.DEFAULTS)
        cfg.update(kwargs)
        self.cfg = cfg
        super().__init__(bot)
        # Her coin için görülen en yüksek/en düşük fiyatı tutacak hafıza
        self.trailing_memory = {} 

    def get_name(self) -> str:
        return self.cfg["strategy_name"]
    
    def get_description(self) -> str:
        return "PLANC Akıllı Trailing Stop ve SuperTrend Stratejisi"

    # ==========================================
    # 1. YARDIMCI FONKSİYONLAR
    # ==========================================

    def _get_candles(self, market_data: Dict) -> List:
        return market_data.get("candles", [])

    def _reset_trailing(self, symbol):
        """Yeni işlem açıldığında hafızayı sıfırlar"""
        if symbol in self.trailing_memory:
            del self.trailing_memory[symbol]
        # Breakeven flag'ini de temizle
        if f"{symbol}_be_active" in self.trailing_memory:
            del self.trailing_memory[f"{symbol}_be_active"]

    def _calculate_tr(self, highs, lows, closes):
        if not closes: return []
        trs = [0.0] * len(closes)
        trs[0] = highs[0] - lows[0]
        for i in range(1, len(closes)):
            trs[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
        return trs

    def _calculate_adx(self, candles: List, period=14) -> float:
        if len(candles) < period * 2: return 0.0
        highs = [float(c[2]) for c in candles]
        lows = [float(c[3]) for c in candles]
        closes = [float(c[4]) for c in candles]
        
        plus_dm = []
        minus_dm = []
        trs = []

        for i in range(1, len(closes)):
            h_diff = highs[i] - highs[i-1]
            l_diff = lows[i-1] - lows[i]
            if (h_diff > l_diff) and (h_diff > 0):
                plus_dm.append(h_diff); minus_dm.append(0.0)
            elif (l_diff > h_diff) and (l_diff > 0):
                plus_dm.append(0.0); minus_dm.append(l_diff)
            else:
                plus_dm.append(0.0); minus_dm.append(0.0)
            tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            trs.append(tr)

        if len(trs) < period: return 0.0
        sum_tr = sum(trs[-period:]); sum_p_dm = sum(plus_dm[-period:]); sum_m_dm = sum(minus_dm[-period:])
        if sum_tr == 0: return 0.0
        di_plus = (sum_p_dm / sum_tr) * 100; di_minus = (sum_m_dm / sum_tr) * 100
        dx = 0.0
        if (di_plus + di_minus) > 0: dx = (abs(di_plus - di_minus) / (di_plus + di_minus)) * 100
        return dx

    def _calculate_supertrend(self, candles: List, period=10, multiplier=3.0):
        if len(candles) < period + 1: return 0, 0.0, 0.0, 0
        highs = [float(c[2]) for c in candles]
        lows = [float(c[3]) for c in candles]
        closes = [float(c[4]) for c in candles]

        trs = self._calculate_tr(highs, lows, closes)
        atr = sum(trs[:period]) / period
        atrs = [0.0] * len(closes); atrs[period-1] = atr
        for i in range(period, len(closes)):
            atr = ((atr * (period - 1)) + trs[i]) / period
            atrs[i] = atr

        trend = 1; final_upper = 0.0; final_lower = 0.0; trend_history = [0] * len(closes)

        for i in range(period, len(closes)):
            hl2 = (highs[i] + lows[i]) / 2
            basic_upper = hl2 + (multiplier * atrs[i])
            basic_lower = hl2 - (multiplier * atrs[i])
            prev_upper = final_upper; prev_lower = final_lower; prev_close = closes[i-1]

            if (basic_upper < prev_upper) or (prev_close > prev_upper): final_upper = basic_upper
            else: final_upper = prev_upper

            if (basic_lower > prev_lower) or (prev_close < prev_lower): final_lower = basic_lower
            else: final_lower = prev_lower

            if trend == 1 and closes[i] < final_lower: trend = -1
            elif trend == -1 and closes[i] > final_upper: trend = 1
            trend_history[i] = trend

        return trend, final_lower, final_upper, trend_history[-2]

    # ==========================================
    # 2. İŞLEM AÇMA MANTIĞI (Gemini Fortress'dan alındı)
    # ==========================================

    def should_open_long(self, symbol: str, market_data: Dict) -> bool:
        candles = self._get_candles(market_data)
        if len(candles) < 100: return False

        curr_trend, lower, _, prev_trend = self._calculate_supertrend(candles, self.cfg["atr_period"], self.cfg["atr_multiplier"])
        adx_val = self._calculate_adx(candles, self.cfg["adx_period"])

        # DEBUG LOG: Stratejinin ne gördüğünü anlamak için detaylı log
        self.log(f"🔍 DEBUG [{symbol}] LONG Check: Trend={curr_trend} (Prev={prev_trend}), ADX={adx_val:.1f}, Threshold={self.cfg['adx_threshold']}")

        # Sadece Trend Yönü Kontrolü (Flip şartı kaldırıldı)
        if curr_trend != 1: return False

        if adx_val < self.cfg["adx_threshold"]:
            self.log(f"{symbol}: Trend LONG sinyali var ama ADX zayıf ({adx_val:.1f}). Pas geçildi.")
            return False

        # İşlem açılıyorsa hafızayı temizle
        self._reset_trailing(symbol)
        
        price = float(candles[-1][4])
        self.log(f"{symbol}: GÜÇLÜ LONG FIRSATI (Trend+ADX)! Fiyat: {price}")
        return True

    def should_open_short(self, symbol: str, market_data: Dict) -> bool:
        if getattr(self.bot, "trade_mode", "both") == "long_only": return False
        candles = self._get_candles(market_data)
        if len(candles) < 100: return False

        curr_trend, _, upper, prev_trend = self._calculate_supertrend(candles, self.cfg["atr_period"], self.cfg["atr_multiplier"])
        adx_val = self._calculate_adx(candles, self.cfg["adx_period"])
        
        # DEBUG LOG
        self.log(f"🔍 DEBUG [{symbol}] SHORT Check: Trend={curr_trend} (Prev={prev_trend}), ADX={adx_val:.1f}, Threshold={self.cfg['adx_threshold']}")

        # Sadece Trend Yönü Kontrolü (Flip şartı kaldırıldı)
        if curr_trend != -1: return False

        if adx_val < self.cfg["adx_threshold"]:
            self.log(f"{symbol}: Trend SHORT sinyali var ama ADX zayıf ({adx_val:.1f}). Pas geçildi.")
            return False

        self._reset_trailing(symbol)

        price = float(candles[-1][4])
        self.log(f"{symbol}: GÜÇLÜ SHORT FIRSATI (Trend+ADX)! Fiyat: {price}")
        return True

    # ==========================================
    # 3. İŞLEM KAPATMA (PLANC Özel Mantığı)
    # ==========================================

    def should_close_position(self, symbol: str, market_data: Dict) -> bool:
        try:
            amt, entry_price = self.bot.get_current_position(symbol)
            if abs(amt) < 0.000001: 
                self._reset_trailing(symbol)
                return False
            side = "LONG" if amt > 0 else "SHORT"
            entry_price = float(entry_price)
        except:
            return False

        candles = self._get_candles(market_data)
        curr_trend, lower, upper, _ = self._calculate_supertrend(candles, self.cfg["atr_period"], self.cfg["atr_multiplier"])
        current_price = float(candles[-1][4])

        # Anlık Fiyat Bazlı Kar/Zarar
        profit_pct = 0.0
        if side == "LONG": profit_pct = (current_price - entry_price) / entry_price
        else: profit_pct = (entry_price - current_price) / entry_price

        # --- A. ACİL DURUM STOPU (%5) ---
        if profit_pct < -0.05:
            self.log(f"{symbol}: ACİL DURUM! Zarar %5'i aştı. Kapatılıyor.")
            return True

        # =========================================================
        # --- B. KARSIZ KAPATMAMA GARANTİSİ (BREAKEVEN) ---
        # =========================================================
        # Mantık: PNL %1.5'u (Fiyat %0.3) geçtiği an, stop girişe çekilir.
        
        BREAKEVEN_TRIGGER = 0.003  # Fiyat %0.3 (5x ile %1.5 PNL)
        
        # Komisyonları (Giriş+Çıkış ~%0.1) kurtarmak için minik pay
        FEE_BUFFER = 0.0015 # %0.15 
        
        if side == "LONG":
             current_change = (current_price - entry_price) / entry_price
             # Eğer kar bir kere %1.5 PNL'i gördüyse
             if self.trailing_memory.get(f"{symbol}_be_active", False) or current_change > BREAKEVEN_TRIGGER:
                 self.trailing_memory[f"{symbol}_be_active"] = True # Breakeven aktifleşti işaretle
                 
                 # Fiyat giriş seviyesine (veya altına) düştüyse SAT
                 if current_price < entry_price * (1 + FEE_BUFFER):
                     self.log(f"{symbol}: BREAKEVEN! Fiyat girişe döndü, 0 zarar ile kaçıldı.")
                     return True

        elif side == "SHORT":
             current_change = (entry_price - current_price) / entry_price
             # Eğer kar bir kere %1.5 PNL'i gördüyse
             if self.trailing_memory.get(f"{symbol}_be_active", False) or current_change > BREAKEVEN_TRIGGER:
                 self.trailing_memory[f"{symbol}_be_active"] = True
                 
                 # Fiyat giriş seviyesine (veya üstüne) çıktıysa SAT
                 if current_price > entry_price * (1 - FEE_BUFFER):
                     self.log(f"{symbol}: BREAKEVEN! Fiyat girişe döndü, 0 zarar ile kaçıldı.")
                     return True
        # =========================================================


        # --- C. PLANC AKILLI TRAILING STOP ---
        # KADEME 1 (Standart): PNL %7.5
        ACTIVATION_STD = 0.015   
        CALLBACK_STD = 0.005     

        # KADEME 2 (Zengin Modu): PNL %10
        ACTIVATION_HIGH = 0.020  
        CALLBACK_HIGH = 0.004    

        # Hafızayı güncelle
        if symbol not in self.trailing_memory:
            self.trailing_memory[symbol] = current_price
        
        stop_price = 0.0
        should_trigger = False
        peak_profit_ratio = 0.0 

        if side == "LONG":
            if current_price > self.trailing_memory[symbol]:
                self.trailing_memory[symbol] = current_price
            
            highest_price = self.trailing_memory[symbol]
            peak_profit_ratio = (highest_price - entry_price) / entry_price

            if peak_profit_ratio >= ACTIVATION_HIGH:
                stop_price = highest_price * (1 - CALLBACK_HIGH)
                if current_price < stop_price:
                    self.log(f"{symbol}: ZENGİN STOPU! PNL %10 üstü görüldü.")
                    should_trigger = True
            elif peak_profit_ratio > ACTIVATION_STD:
                stop_price = highest_price * (1 - CALLBACK_STD)
                if current_price < stop_price:
                    self.log(f"{symbol}: STANDART STOP. Kar korundu.")
                    should_trigger = True

        elif side == "SHORT":
            if current_price < self.trailing_memory[symbol]:
                self.trailing_memory[symbol] = current_price
            
            lowest_price = self.trailing_memory[symbol]
            peak_profit_ratio = (entry_price - lowest_price) / entry_price

            if peak_profit_ratio >= ACTIVATION_HIGH:
                stop_price = lowest_price * (1 + CALLBACK_HIGH)
                if current_price > stop_price:
                    self.log(f"{symbol}: ZENGİN STOPU (SHORT)! PNL %10 üstü görüldü.")
                    should_trigger = True
            elif peak_profit_ratio > ACTIVATION_STD:
                stop_price = lowest_price * (1 + CALLBACK_STD)
                if current_price > stop_price:
                    self.log(f"{symbol}: STANDART STOP (SHORT). Kar korundu.")
                    should_trigger = True

        if should_trigger:
            return True

        # --- D. SUPERTREND ÇIKIŞI ---
        if side == "LONG" and (curr_trend == -1 or current_price < lower):
            return True
        elif side == "SHORT" and (curr_trend == 1 or current_price > upper):
            return True

        return False