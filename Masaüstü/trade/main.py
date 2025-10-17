import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from datetime import datetime
import json
import os
import requests
import math
from decimal import Decimal, ROUND_DOWN
# i18n
try:
    from locales.langs import LANGS, TRANSLATIONS, get_text
except Exception:
    LANGS, TRANSLATIONS = [], {}
    def get_text(lang, key):
        return key
# license verify
try:
    from licenses.verify import verify_license, PUBLIC_KEY_B64
except Exception:
    verify_license = None
    PUBLIC_KEY_B64 = ""

# updater
try:
    from updater import SoftwareUpdater, UpdateDialog
except Exception:
    SoftwareUpdater = None
    UpdateDialog = None

class BinanceFuturesBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Binance Futures Trading Bot")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1e1e1e")
        
        # API Client
        self.client = None
        self.api_key = ""
        self.api_secret = ""
        
        # Trading variables
        self.current_symbol = "BTCUSDT"
        self.current_price = 0.0
        self.balance = 0.0
        self.positions = {}
        self.price_history = []
        self.time_history = []
        
        # Environment and mode
        self.env_var = tk.StringVar(value="Test")  # Test veya Gerçek
        self.trading_mode_var = tk.StringVar(value="Manuel")  # Manuel veya Otomatik
        self.market_interval_var = tk.StringVar(value="60")  # saniye
        # Language
        default_lang = 'tr'
        self.lang_var = tk.StringVar(value=default_lang)
        # License
        self.license_var = tk.StringVar(value="")
        self.license_valid = False
        
        # Market breadth tracking (CoinPaprika + Binance)
        self.market_thread = None
        self.market_thread_running = False
        self.prev_rising_count = None
        self.prev_symbol_change = None
        self.top100_symbols = []
        self.top100_last_fetch = 0  # epoch seconds
        self.market_interval_seconds = 60
        
        # Update notification
        self.update_available = False
        self.update_warning_label = None
        
        # Auto trade control
        self.auto_trade_enabled = False
        self.last_auto_action_time = 0
        self.target_pnl_var = tk.StringVar(value="0")
        self.neutral_close_pct_var = tk.StringVar(value="2")
        self.auto_percent_var = tk.StringVar(value="0")
        
        # Market trend latch (3-coin rule)
        self.market_up_latched = False
        self.market_up_baseline = 0
        # Symmetric state: 'up' | 'down' | None
        self.market_trend_state = None
        
        # Price update thread
        self.price_thread = None
        self.price_thread_running = False
        
        self.setup_ui()
        self.load_config()
        # Settings file
        self.settings_path = "ayarlar.txt"
        self.last_saved_settings = {}
        self.load_settings_file()
        # Interval sayısal cache'i güncelle
        try:
            self.market_interval_seconds = int(self.market_interval_var.get())
        except Exception:
            self.market_interval_seconds = 60
        # Start market monitor always for status updates
        self.start_market_monitor()
        # İlk sembol listesini yükle
        self.update_symbol_list()
        # Otomatik güncelleme kontrolü (program yüklendikten sonra)
        self.auto_check_updates_on_startup()
        
    def setup_ui(self):
        # Ana stil konfigürasyonu
        style = ttk.Style()
        style.theme_use('clam')
        # Dark palette
        style.configure('Dark.TFrame', background='#111827')
        style.configure('Dark.TLabelframe', background='#111827', foreground='#e5e7eb')
        style.configure('Dark.TLabelframe.Label', background='#111827', foreground='#9ca3af', font=('Segoe UI', 10, 'bold'))
        style.configure('TLabel', background='#111827', foreground='#e5e7eb', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=8)
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), padding=10, foreground='#ffffff', background='#2563eb')
        style.map('Accent.TButton', background=[('active', '#1d4ed8')])
        # Auto trade on/off styles
        style.configure('AutoOn.TButton', font=('Segoe UI', 10, 'bold'), padding=10, foreground='#111827', background='#22c55e')
        style.map('AutoOn.TButton', background=[('active', '#16a34a')])
        style.configure('AutoOff.TButton', font=('Segoe UI', 10, 'bold'), padding=10, foreground='#ffffff', background='#ef4444')
        style.map('AutoOff.TButton', background=[('active', '#dc2626')])
        style.configure('TEntry', font=('Segoe UI', 10))
        style.configure('TCombobox', fieldbackground='#1f2937', background='#1f2937', foreground='#e5e7eb')
        # Light combobox for system light dropdowns
        style.configure('Light.TCombobox', fieldbackground='#f3f4f6', background='#f3f4f6', foreground='#111827')
        style.map('Light.TCombobox', fieldbackground=[('readonly', '#f3f4f6'), ('!disabled', '#f3f4f6')],
                                      foreground=[('readonly', '#111827'), ('!disabled', '#111827')])
        # Modern black theme
        style.theme_use('clam')
        BG = '#0a0a0a'
        CARD = '#101214'
        SUBTLE = '#0e0f11'
        FG = '#e5e7eb'
        MUTED = '#9ca3af'
        ACCENT = '#10b981'
        DANGER = '#ef4444'
        
        style.configure('.', background=BG, foreground=FG, fieldbackground=SUBTLE)
        
        # Treeview
        style.configure('Dark.Treeview', background=SUBTLE, fieldbackground=SUBTLE, foreground=FG, rowheight=26, borderwidth=0)
        style.configure('Treeview.Heading', background=CARD, foreground=MUTED, relief='flat', padding=8)
        style.map('Treeview.Heading', background=[('active', SUBTLE)])
        style.map('Dark.Treeview', background=[('selected', '#1f2937')], foreground=[('selected', '#ffffff')])
        
        # Cards
        style.configure('Card.TLabelframe', background=CARD, foreground=FG, borderwidth=0, padding=10)
        style.configure('Card.TLabelframe.Label', background=CARD, foreground=MUTED, font=('Segoe UI', 10, 'bold'))
        
        # Inputs
        style.configure('TEntry', fieldbackground=SUBTLE, foreground=FG, insertcolor=FG, borderwidth=0)
        style.configure('TCombobox', fieldbackground=SUBTLE, foreground=FG, arrowcolor=MUTED, borderwidth=0)
        
        # Buttons
        style.configure('TButton', background='#18181b', foreground=FG, padding=10, borderwidth=0)
        style.map('TButton', background=[('active', '#202024'), ('pressed', '#27272a')])
        style.configure('Accent.TButton', background=ACCENT, foreground=BG, padding=10, borderwidth=0, font=('Segoe UI Semibold', 10))
        style.map('Accent.TButton', background=[('active', '#059669'), ('pressed', '#047857')])
        style.configure('Danger.TButton', background=DANGER, foreground='#ffffff', padding=10, borderwidth=0, font=('Segoe UI Semibold', 10))
        style.map('Danger.TButton', background=[('active', '#dc2626'), ('pressed', '#b91c1c')])
        style.configure('Secondary.TButton', background='#26272b', foreground=FG, padding=10, borderwidth=0)
        style.map('Secondary.TButton', background=[('active', '#2e3035')])
        
        # Badges
        style.configure('Badge.Green.TLabel', background=ACCENT, foreground=BG, padding=8, font=('Segoe UI Semibold', 12))
        style.configure('Badge.Red.TLabel', background=DANGER, foreground='#ffffff', padding=8, font=('Segoe UI Semibold', 12))
        style.configure('Badge.Neutral.TLabel', background='#1f2937', foreground=FG, padding=8, font=('Segoe UI Semibold', 12))
        
        # Scrollbars
        style.configure('Vertical.TScrollbar', background=CARD, troughcolor=SUBTLE, arrowcolor=MUTED, bordercolor=CARD)
        style.configure('Horizontal.TScrollbar', background=CARD, troughcolor=SUBTLE, arrowcolor=MUTED, bordercolor=CARD)
        
        # Banner label defaults
        style.configure('Banner.Title.TLabel', background=BG, foreground=FG, font=('Segoe UI', 14, 'bold'))
        
        # Header styles
        style.configure('Header.TFrame', background=BG)
        style.configure('Header.TLabel', background=BG, foreground=FG, font=('Segoe UI Semibold', 12))
        style.configure('Header.TButton', font=('Segoe UI', 10), padding=6)
        self.root.configure(bg=BG)
        
        # Ana container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sol panel - API ve Hesap Bilgileri (scrollable)
        left_container = ttk.Frame(main_frame, style='Dark.TFrame')
        left_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_canvas = tk.Canvas(left_container, background='#111827', highlightthickness=0, width=260)
        left_scroll = ttk.Scrollbar(left_container, orient=tk.VERTICAL, command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scroll.set)
        left_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=False)
        left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        left_frame = ttk.Frame(left_canvas, style='Dark.TFrame')
        left_window = left_canvas.create_window((0, 0), window=left_frame, anchor='nw')
        # Resize and scrollregion bindings
        def _on_frame_config(event):
            left_canvas.configure(scrollregion=left_canvas.bbox('all'))
        left_frame.bind('<Configure>', _on_frame_config)
        def _on_canvas_config(event):
            left_canvas.itemconfigure(left_window, width=event.width)
        left_canvas.bind('<Configure>', _on_canvas_config)
        # Mouse wheel scroll (Windows)
        def _on_mousewheel(event):
            left_canvas.yview_scroll(-int(event.delta/120), 'units')
        left_canvas.bind_all('<MouseWheel>', _on_mousewheel)
        
        # API Ayarları
        api_frame = ttk.LabelFrame(left_frame, text="🔑 API", padding=10, style='Dark.TLabelframe')
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.env_label_lbl = ttk.Label(api_frame, text=f"🌐 {self.tr('env_label')}")
        self.env_label_lbl.pack(anchor=tk.W)
        env_combo = ttk.Combobox(api_frame, textvariable=self.env_var, values=["Test", "Gerçek"], state="readonly", style='Light.TCombobox')
        env_combo.pack(fill=tk.X, pady=(0, 5))
        env_combo.bind('<<ComboboxSelected>>', self.on_env_change)
        
        # Dil / Language
        ttk.Label(api_frame, text="🌍 Dil / Language:").pack(anchor=tk.W)
        lang_values = [f"{code} - {name}" for code, name in getattr(self, 'langs_list', getattr(__import__('builtins'), 'list', list))(LANGS) ] if LANGS else ["tr - Turkish", "en - English"]
        self.lang_combo = ttk.Combobox(api_frame, textvariable=self.lang_var, values=lang_values, state="readonly", style='Light.TCombobox')
        self.lang_combo.pack(fill=tk.X, pady=(0, 5))
        self.lang_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        
        self.api_key_lbl = ttk.Label(api_frame, text=f"🗝️ {self.tr('api_key')}")
        self.api_key_lbl.pack(anchor=tk.W)
        self.api_key_entry = ttk.Entry(api_frame, width=30, show="*")
        self.api_key_entry.pack(fill=tk.X, pady=(0, 5))
        
        self.api_secret_lbl = ttk.Label(api_frame, text=f"🔒 {self.tr('api_secret')}")
        self.api_secret_lbl.pack(anchor=tk.W)
        self.api_secret_entry = ttk.Entry(api_frame, width=30, show="*")
        self.api_secret_entry.pack(fill=tk.X, pady=(0, 10))
        
        # License area
        lic_frame = ttk.LabelFrame(left_frame, text=f"🔐 {self.tr('license')}", padding=10, style='Dark.TLabelframe')
        lic_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(lic_frame, text=self.tr('license_code')).pack(anchor=tk.W)
        self.license_entry = ttk.Entry(lic_frame, textvariable=self.license_var, show='*')
        self.license_entry.pack(fill=tk.X, pady=(0, 6))
        self.license_status_lbl = ttk.Label(lic_frame, text=self.tr('license_status_unlicensed'), foreground="#f87171")
        self.license_status_lbl.pack(anchor=tk.W)
        btns = ttk.Frame(lic_frame)
        btns.pack(fill=tk.X, pady=(6,0))
        self.activate_btn = ttk.Button(btns, text=f"✔ {self.tr('activate')}", command=self.activate_license, style='Accent.TButton')
        self.activate_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,4))
        go_lbl = tk.Label(btns, text=self.tr('get_license'), fg="#60a5fa", cursor="hand2", bg="#111827")
        go_lbl.pack(side=tk.LEFT, padx=(4,0))
        go_lbl.bind("<Button-1>", lambda e: self.open_license_site())
        
        self.connect_btn = ttk.Button(api_frame, text="🔗 Bağlan", command=self.connect_api, style='Accent.TButton')
        self.connect_btn.pack(fill=tk.X)
        
        # Hesap Bilgileri
        account_frame = ttk.LabelFrame(left_frame, text=f"💼 {self.tr('account_info')}", padding=10, style='Dark.TLabelframe')
        account_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.balance_label = ttk.Label(account_frame, text=f"{self.tr('balance')} $0.00")
        self.balance_label.pack(anchor=tk.W)
        
        self.connection_label = ttk.Label(account_frame, text=f"{self.tr('connection_status')} {self.tr('not_connected')}", foreground="red")
        self.connection_label.pack(anchor=tk.W)
        
        # Symbol seçimi
        symbol_frame = ttk.LabelFrame(left_frame, text=f"🔁 {self.tr('symbol_label')}", padding=10, style='Dark.TLabelframe')
        symbol_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.symbol_var = tk.StringVar(value="BTCUSDT")
        self.symbol_combo = ttk.Combobox(symbol_frame, textvariable=self.symbol_var, values=[], state="readonly", style='Light.TCombobox')
        self.symbol_combo.configure(foreground='#000000')
        self.symbol_combo.pack(fill=tk.X)
        self.symbol_combo.bind('<<ComboboxSelected>>', self.on_symbol_change)
        self.refresh_list_btn = ttk.Button(symbol_frame, text="⟳ Listeyi Yenile", command=self.update_symbol_list, style='Secondary.TButton')
        self.refresh_list_btn.pack(fill=tk.X, pady=(6,0))
        
        # Fiyat Bilgisi
        price_frame = ttk.LabelFrame(left_frame, text=f"📊 {self.tr('selected_coin_info')}", padding=10, style='Dark.TLabelframe')
        price_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.price_label = ttk.Label(price_frame, text=f"{self.tr('price')} $0.00", font=('Segoe UI', 12, 'bold'))
        self.price_label.pack(anchor=tk.W)
        self.change_label = ttk.Label(price_frame, text=f"{self.tr('change_24h')} 0.00%", font=('Segoe UI', 11))
        self.change_label.pack(anchor=tk.W, pady=(4,0))
        
        # Trading Panel
        trading_frame = ttk.LabelFrame(left_frame, text=f"🛠️ {self.tr('trading')}", padding=10, style='Dark.TLabelframe')
        trading_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Mod seçimi
        self.trading_mode_lbl = ttk.Label(trading_frame, text=f"⚙️ {self.tr('trading_mode')}")
        self.trading_mode_lbl.pack(anchor=tk.W)
        mode_combo = ttk.Combobox(trading_frame, textvariable=self.trading_mode_var, values=["Manuel", "Otomatik"], state="readonly", style='Light.TCombobox')
        mode_combo.pack(fill=tk.X, pady=(0, 5))
        mode_combo.bind('<<ComboboxSelected>>', self.on_mode_change)
        
        # Position Size
        self.pos_size_lbl = ttk.Label(trading_frame, text=f"💵 {self.tr('position_size_usdt')}")
        self.pos_size_lbl.pack(anchor=tk.W)
        self.position_size_var = tk.StringVar(value="10")
        ttk.Entry(trading_frame, textvariable=self.position_size_var).pack(fill=tk.X, pady=(0, 5))
        
        # Leverage
        self.lev_lbl = ttk.Label(trading_frame, text=f"📈 {self.tr('leverage_label')}")
        self.lev_lbl.pack(anchor=tk.W)
        self.leverage_var = tk.StringVar(value="1")
        leverage_combo = ttk.Combobox(trading_frame, textvariable=self.leverage_var,
                                     values=["1", "2", "3", "5", "10", "20"], state="readonly", style='Light.TCombobox')
        leverage_combo.pack(fill=tk.X, pady=(0, 10))
        leverage_combo.bind('<<ComboboxSelected>>', self.on_leverage_change)
        
        # Otomatik kontrol süresi
        self.market_int_lbl = ttk.Label(trading_frame, text=f"⏱️ {self.tr('market_interval_sec')}")
        self.market_int_lbl.pack(anchor=tk.W)
        self.interval_entry = ttk.Entry(trading_frame, textvariable=self.market_interval_var)
        self.interval_entry.pack(fill=tk.X, pady=(0, 10))
        self.interval_entry.bind('<FocusOut>', self.on_interval_change)
        self.interval_entry.bind('<Return>', self.on_interval_change)
        
        # Hedef PNL ve Nötr Kapat (%)
        target_frame = ttk.Frame(trading_frame)
        target_frame.pack(fill=tk.X, pady=(0, 8))
        self.target_lbl = ttk.Label(target_frame, text=f"🎯 {self.tr('target_pnl')}")
        self.target_lbl.pack(anchor=tk.W)
        self.target_entry = ttk.Entry(target_frame, textvariable=self.target_pnl_var)
        self.target_entry.pack(fill=tk.X)
        self.target_entry.bind('<FocusOut>', self.on_target_change)
        self.target_entry.bind('<Return>', self.on_target_change)
        
        self.neutral_lbl = ttk.Label(target_frame, text=f"⛔ {self.tr('neutral_close_pct_label')}")
        self.neutral_lbl.pack(anchor=tk.W)
        self.neutral_entry = ttk.Entry(target_frame, textvariable=self.neutral_close_pct_var)
        self.neutral_entry.pack(fill=tk.X)
        self.neutral_entry.bind('<FocusOut>', self.on_target_change)
        self.neutral_entry.bind('<Return>', self.on_target_change)
        
        self.auto_bal_lbl = ttk.Label(target_frame, text=f"💰 {self.tr('auto_balance_pct')}")
        self.auto_bal_lbl.pack(anchor=tk.W)
        self.auto_percent_entry = ttk.Entry(target_frame, textvariable=self.auto_percent_var)
        self.auto_percent_entry.pack(fill=tk.X)
        self.auto_percent_entry.bind('<FocusOut>', self.on_target_change)
        self.auto_percent_entry.bind('<Return>', self.on_target_change)
        
        # Oto trade durum etiketi
        self.auto_status_label = ttk.Label(trading_frame, text=self.tr('auto_off'))
        self.auto_status_label.pack(anchor=tk.W, pady=(6,6))
        
        # Trading buttons
        button_frame = ttk.Frame(trading_frame)
        button_frame.pack(fill=tk.X)
        
        self.long_btn = ttk.Button(button_frame, text="LONG", command=self.open_long_position, style='Accent.TButton')
        self.long_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        self.short_btn = ttk.Button(button_frame, text="SHORT", command=self.open_short_position, style='Danger.TButton')
        self.short_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        ttk.Button(trading_frame, text="Tüm Pozisyonları Kapat", 
                  command=self.close_all_positions, style='Danger.TButton').pack(fill=tk.X, pady=(10, 0))
        
        # Reklam Alanı
        ad_frame = ttk.LabelFrame(left_frame, text="📢 Sponsor", padding=10, style='Dark.TLabelframe')
        ad_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Reklam görseli için container
        self.ad_container = tk.Frame(ad_frame, bg='#111827', width=240, height=240)
        self.ad_container.pack(anchor=tk.CENTER)
        self.ad_container.pack_propagate(False)
        
        # Reklam label'ı (resim yüklenene kadar placeholder)
        self.ad_label = tk.Label(self.ad_container, text="Loading...", bg='#111827', fg='#9ca3af')
        self.ad_label.pack(expand=True)
        
        # Reklam görselini yükle
        self._init_advertisement()
        
        # Sağ panel - Grafik ve Pozisyonlar
        right_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Durum Banner'ı (geniş alan, siyah zemin, logo ve oklar)
        self.status_banner = tk.Frame(right_frame, bg='#0a0a0a')
        self.status_banner.pack(fill=tk.X, pady=(0, 8))
        self._banner_inner = tk.Frame(self.status_banner, bg=self.status_banner['bg'])
        self._banner_inner.pack(fill=tk.X, padx=12, pady=12)
        # Logo
        self.logo_label = tk.Label(self._banner_inner, bg=self.status_banner['bg'])
        self.logo_label.pack(side=tk.LEFT, padx=(0, 12))
        # Ortalanmış merkez grup
        self._banner_center = tk.Frame(self._banner_inner, bg=self.status_banner['bg'])
        self._banner_center.pack(anchor='center')
        # Oklar ve rozetler (merkezde)
        self.left_arrow = tk.Label(self._banner_center, text='', font=('Segoe UI Symbol', 18, 'bold'), bg=self.status_banner['bg'], fg='#9ca3af')
        self.left_arrow.pack(side=tk.LEFT, padx=(0, 12))
        self.market_status_label = tk.Label(self._banner_center, text="Piyasa durumu: -", font=('Segoe UI', 14, 'bold'), bg='#111111', fg='white', padx=14, pady=10, width=18)
        self.market_status_label.pack(side=tk.LEFT, padx=(0, 12))
        self.symbol_status_label = tk.Label(self._banner_center, text="Seçili sembol: -", font=('Segoe UI', 14, 'bold'), bg='#111111', fg='white', padx=14, pady=10, width=18)
        self.symbol_status_label.pack(side=tk.LEFT)
        self.right_arrow = tk.Label(self._banner_center, text='', font=('Segoe UI Symbol', 18, 'bold'), bg=self.status_banner['bg'], fg='#9ca3af')
        self.right_arrow.pack(side=tk.LEFT, padx=(12, 0))
        # Logo yükle
        self._init_banner_logo()
        
        # PNL Paneli (Shadow + Card)
        chart_shadow = tk.Frame(right_frame, bg='#050505')
        chart_shadow.pack(fill=tk.X, expand=False, pady=(0, 10))
        # Sol renk şeridi
        tk.Frame(chart_shadow, bg='#10b981', width=4, height=1).pack(side=tk.LEFT, fill=tk.Y)
        chart_frame = ttk.LabelFrame(chart_shadow, text="📈 Açık İşlemler PNL", padding=10, style='Card.TLabelframe')
        self.chart_frame = chart_frame
        chart_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1, pady=1)
        
        self.setup_pnl_panel(chart_frame)
        
        # Özet PNL (Shadow + Card)
        summary_shadow = tk.Frame(right_frame, bg='#050505')
        summary_shadow.pack(fill=tk.X, expand=False, pady=(0, 10))
        tk.Frame(summary_shadow, bg='#3b82f6', width=4, height=1).pack(side=tk.LEFT, fill=tk.Y)
        summary_frame = ttk.LabelFrame(summary_shadow, text="📊 Özet", padding=10, style='Card.TLabelframe')
        self.summary_frame = summary_frame
        summary_frame.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=1, pady=1)
        self.total_pnl_label = ttk.Label(summary_frame, text="Toplam PNL: 0.00 (U:0.00 | R:0.00)")
        self.total_pnl_label.pack(anchor=tk.W)
        self.cum_pnl_label = ttk.Label(summary_frame, text="Kümülatif PNL: 0.00")
        self.cum_pnl_label.pack(anchor=tk.W, pady=(4,0))
        
        # Pozisyonlar listesi (Shadow + Card)
        positions_shadow = tk.Frame(right_frame, bg='#050505')
        positions_shadow.pack(fill=tk.BOTH, expand=True)
        tk.Frame(positions_shadow, bg='#8b5cf6', width=4, height=1).pack(side=tk.LEFT, fill=tk.Y)
        positions_frame = ttk.LabelFrame(positions_shadow, text="📂 Açık Pozisyonlar", padding=10, style='Card.TLabelframe')
        self.positions_frame = positions_frame
        positions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Toolbar for actions
        pos_toolbar = ttk.Frame(positions_frame, style='Dark.TFrame')
        pos_toolbar.pack(fill=tk.X, pady=(0,6))
        # Buttons near 'Tümünü Kapat' (centered)
        center_bar = ttk.Frame(pos_toolbar, style='Dark.TFrame')
        center_bar.pack(anchor='center')
        self.btn_close_all = ttk.Button(center_bar, text="✖ Tümünü Kapat", command=self.close_all_positions, style='Danger.TButton')
        self.btn_close_all.pack(side=tk.LEFT, padx=(4,4))
        self.close_selected_btn = ttk.Button(center_bar, text="□ Seçiliyi Kapat", command=self.close_selected_position, style='Danger.TButton')
        self.close_selected_btn.pack(side=tk.LEFT, padx=(4,4))
        self.auto_btn = ttk.Button(center_bar, text="▶ Oto Trade", command=self.toggle_auto_trade, style='AutoOff.TButton')
        self.auto_btn.pack(side=tk.LEFT, padx=(4,4))
        self.save_settings_btn = ttk.Button(center_bar, text="💾 Ayarları Kaydet", command=self.manual_save_settings, style='Secondary.TButton')
        self.save_settings_btn.pack(side=tk.LEFT, padx=(4,4))
        self.refresh_btn = ttk.Button(center_bar, text="⟳ Yenile", command=self.update_symbol_list, style='Secondary.TButton')
        self.refresh_btn.pack(side=tk.LEFT, padx=(4,4))
        self.update_btn = ttk.Button(center_bar, text="📦 Güncelle", command=self.check_for_updates, style='Secondary.TButton')
        self.update_btn.pack(side=tk.LEFT, padx=(4,4))
        
        # Güncelleme uyarı metni (başlangıçta gizli)
        self.update_warning_label = tk.Label(center_bar, text="", 
                                           bg='#0a0a0a', fg='#ef4444', 
                                           font=('Segoe UI', 10, 'bold'))
        self.update_warning_label.pack(side=tk.LEFT, padx=(8,4))
        
        # Treeview for positions
        columns = ("Symbol", "Side", "Size", "Entry Price", "PNL")
        self.positions_tree = ttk.Treeview(positions_frame, columns=columns, show="headings", height=8, style='Dark.Treeview')
        # Zebra ve hover
        self.positions_tree.tag_configure('even', background='#111827')
        self.positions_tree.tag_configure('odd', background='#0f172a')
        self.positions_tree.tag_configure('hover', background='#1f2937')
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=110)
        self.positions_tree.pack(fill=tk.BOTH, expand=True)
        # Hover state holders
        self._pos_row_tags = {}
        self._pos_hover_item = None
        self.positions_tree.bind('<Motion>', self._on_positions_tree_motion)
        self.positions_tree.bind('<Leave>', self._on_positions_tree_leave)
        # Sıralama
        self._init_treeview_sort(self.positions_tree, columns)
        
        # Geçmiş işlemler (Shadow + Card)
        history_shadow = tk.Frame(right_frame, bg='#050505')
        history_shadow.pack(fill=tk.BOTH, expand=True, pady=(10,10))
        tk.Frame(history_shadow, bg='#f59e0b', width=4, height=1).pack(side=tk.LEFT, fill=tk.Y)
        history_frame = ttk.LabelFrame(history_shadow, text="📜 Geçmiş İşlemler (Realized)", padding=10, style='Card.TLabelframe')
        self.history_frame = history_frame
        history_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.history_tree = ttk.Treeview(history_frame, columns=("Time","Symbol","PNL","Type"), show="headings", height=6, style='Dark.Treeview')
        self.history_tree.tag_configure('hover', background='#1f2937')
        for hcol in ("Time","Symbol","PNL","Type"):
            self.history_tree.heading(hcol, text=hcol)
            self.history_tree.column(hcol, width=120)
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        # Hover state holders for history
        self._hist_row_tags = {}
        self._hist_hover_item = None
        self.history_tree.bind('<Motion>', self._on_history_tree_motion)
        self.history_tree.bind('<Leave>', self._on_history_tree_leave)
        # Sıralama
        self._init_treeview_sort(self.history_tree, ("Time","Symbol","PNL","Type"))
        
        # Log alanı (Shadow + Card)
        log_shadow = tk.Frame(self.root, bg='#050505')
        log_shadow.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Frame(log_shadow, bg='#6b7280', width=4, height=1).pack(side=tk.LEFT, fill=tk.Y)
        log_frame = ttk.LabelFrame(log_shadow, text="🧾 Log", padding=10, style='Card.TLabelframe')
        self.log_frame = log_frame
        log_frame.pack(side=tk.LEFT, fill=tk.X, padx=1, pady=1, expand=True)
        
        self.log_text = tk.Text(log_frame, height=6, bg="#0b0f16", fg="#e5e7eb")
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
        
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=100)
        
        self.positions_tree.pack(fill=tk.X)
        
        # Log alanı
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10, style='Dark.TLabelframe')
        log_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(log_frame, height=6, bg="#2d2d2d", fg="white")
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_pnl_panel(self, parent):
        self.pnl_text = tk.Text(parent, height=6, bg="#0b0f16", fg="#e5e7eb")
        self.pnl_text.configure(state=tk.DISABLED)
        self.pnl_text.pack(fill=tk.X, expand=False)
        
    def update_pnl_panel(self, positions):
        try:
            self.pnl_text.configure(state=tk.NORMAL)
            self.pnl_text.delete('1.0', tk.END)
            if not positions:
                self.pnl_text.insert(tk.END, "Açık pozisyon yok.\n")
            else:
                for pos in positions:
                    if float(pos.get('positionAmt', 0)) != 0:
                        symbol = pos.get('symbol')
                        pnl = float(pos.get('unRealizedProfit', pos.get('unrealizedProfit', 0)))
                        line = f"{symbol}: {pnl:.2f} USDT\n"
                        self.pnl_text.insert(tk.END, line)
            self.pnl_text.configure(state=tk.DISABLED)
        except Exception as e:
            self.log_message(f"PNL panel güncelleme hatası: {e}")
    
    def log_message(self, message):
        # Thread-safe log
        if threading.current_thread() is not threading.main_thread():
            try:
                self.root.after(0, lambda m=message: self.log_message(m))
                return
            except Exception:
                print(message)
                return
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        print(log_entry.strip())
    
    def save_config(self):
        config = {
            "api_key": self.api_key,
            "api_secret": self.api_secret
        }
        try:
            with open("config.json", "w") as f:
                json.dump(config, f)
        except Exception as e:
            self.log_message(f"Config kaydetme hatası: {e}")
    
    def load_config(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    self.api_key_entry.insert(0, config.get("api_key", ""))
                    self.api_secret_entry.insert(0, config.get("api_secret", ""))
        except Exception as e:
            self.log_message(f"Config yükleme hatası: {e}")
    
    def connect_api(self):
        self.api_key = self.api_key_entry.get().strip()
        self.api_secret = self.api_secret_entry.get().strip()
        
        if not self.api_key or not self.api_secret:
            messagebox.showerror("Hata", "API Key ve Secret gerekli!")
            return
        
        try:
            use_testnet = (self.env_var.get() == "Test")
            self.client = Client(self.api_key, self.api_secret, testnet=use_testnet)
            
            # Futures testnet URL ayarı
            if use_testnet:
                # python-binance futures testnet desteklemesi için URL override
                self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi/v1'
            
            # Test connection
            account_info = self.client.futures_account()
            self.balance = float([asset for asset in account_info['assets'] if asset['asset'] == 'USDT'][0]['walletBalance'])
            
            self.connection_label.config(text=f"Durum: Bağlandı ✓ ({'Test' if use_testnet else 'Gerçek'})", foreground="green")
            self.balance_label.config(text=f"Balance: ${self.balance:.2f}")
            
            self.log_message("Binance Futures API'ye başarıyla bağlandı!")
            self.save_config()
            
            # Start price updates
            self.start_price_updates()
            
        except Exception as e:
            messagebox.showerror("API Hata", f"Bağlantı hatası: {str(e)}")
            self.log_message(f"API bağlantı hatası: {e}")
    
    def start_price_updates(self):
        if self.price_thread and self.price_thread_running:
            return
            
        self.price_thread_running = True
        self.price_thread = threading.Thread(target=self.price_update_loop)
        self.price_thread.daemon = True
        self.price_thread.start()
    
    def price_update_loop(self):
        while self.price_thread_running and self.client:
            try:
                # Get current price
                ticker = self.client.futures_symbol_ticker(symbol=self.current_symbol)
                self.current_price = float(ticker['price'])
                
                # Update price history for chart
                current_time = datetime.now()
                self.price_history.append(self.current_price)
                self.time_history.append(current_time)
                
                # Keep only last 50 points
                if len(self.price_history) > 50:
                    self.price_history.pop(0)
                    self.time_history.pop(0)
                
                # Update UI in main thread
                self.root.after(0, self.update_ui)
                
                # Update positions
                self.root.after(0, self.update_positions)
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                self.log_message(f"Fiyat güncelleme hatası: {e}")
                time.sleep(5)
    
    def update_ui(self):
        # Update price label
        self.price_label.config(text=f"Fiyat: ${self.current_price:.4f}")
        # Update change label
        try:
            base = self.get_base_symbol_from_binance(self.current_symbol)
            sym = base + 'USDT'
            if hasattr(self, 'latest_changes') and self.latest_changes and sym in self.latest_changes:
                ch = float(self.latest_changes[sym])
                ch_color = 'green' if ch >= 0 else 'red'
                self.change_label.config(text=f"Değişim (24h): {ch:.2f}%", foreground=ch_color)
        except Exception:
            pass
        
        # Grafik kaldırıldı
        
    def on_symbol_change(self, event=None):
        self.current_symbol = self.symbol_var.get()
        self.price_history.clear()
        self.time_history.clear()
        self.log_message(f"Symbol değiştirildi: {self.current_symbol}")
        self.save_settings_file()
        # Sembol durumu anında güncelle
        self.update_symbol_status_once()
        # Trend karşılaştırmalarında başlangıç değerlerini seçili sembolden başlat
        try:
            symbols = self.get_top100_symbols_any()
            changes = self.fetch_binance_futures_24h_changes()
            if symbols and changes:
                base = self.get_base_symbol_from_binance(self.current_symbol)
                usdt_syms = [s + 'USDT' for s in symbols]
                rising_now = sum(1 for sym in usdt_syms if sym in changes and changes[sym] > 0)
                self.prev_rising_count = rising_now
                # reset latch/state on symbol change
                self.market_up_latched = False
                self.market_up_baseline = 0
                self.market_trend_state = None
                sym_full = base + 'USDT'
                if sym_full in changes:
                    self.prev_symbol_change = changes[sym_full]
                self.log_message(f"Baz değerler güncellendi: rising_prev={self.prev_rising_count}, {base} prev_change={self.prev_symbol_change}")
        except Exception:
            pass
    
    def on_mode_change(self, event=None):
        mode = self.trading_mode_var.get()
        self.save_settings_file()
        # Otomatik mod sadece bilgi amaçlı, izleme her zaman açık
        self.log_message(f"Trading modu: {mode}")
    
    def toggle_auto_trade(self):
        if not self.client:
            messagebox.showerror("Hata", "Önce API'ye bağlanın!")
            return
        self.auto_trade_enabled = not self.auto_trade_enabled
        if self.auto_trade_enabled:
            self.auto_btn.config(style='AutoOn.TButton')
            self.auto_status_label.config(text=self.tr('auto_on'))
            self.log_message("Oto trade başlatıldı.")
            self.save_settings_file()
            # Hemen tek seferlik karar ver
            self.trigger_auto_trade_once()
        else:
            self.auto_btn.config(style='AutoOff.TButton')
            self.auto_status_label.config(text=self.tr('auto_off'))
            self.log_message("Oto trade durduruldu.")
            self.save_settings_file()
    
    def trigger_auto_trade_once(self):
        try:
            symbols = self.get_top100_symbols_any()
            changes = self.fetch_binance_futures_24h_changes()
            if not (symbols and changes):
                self.log_message("Oto trade için veri alınamadı.")
                return
            base0 = self.get_base_symbol_from_binance(self.current_symbol)
            # seçili sembolden başlasın (list rotate); yoksa öne ekle
            us = [s + 'USDT' for s in symbols]
            if base0 in symbols:
                idx = symbols.index(base0)
                rot = symbols[idx:] + symbols[:idx]
                usdt_syms = [s + 'USDT' for s in rot]
            else:
                usdt_syms = [base0 + 'USDT'] + us
            rising_now = sum(1 for sym in usdt_syms if sym in changes and changes[sym] > 0)
            falling_now = max(0, len(usdt_syms) - rising_now)
            # Piyasa durumu - 3-coin simetrik latch kuralı
            prev = self.prev_rising_count
            market_up = market_down = False
            state = getattr(self, 'market_trend_state', None)
            if prev is not None:
                diff = rising_now - prev
                if state == 'up':
                    market_up = True
                    if diff <= -3:
                        state = 'down'
                        market_up = False
                        market_down = True
                elif state == 'down':
                    market_down = True
                    if diff >= 3:
                        state = 'up'
                        market_down = False
                        market_up = True
                else:
                    if diff >= 3:
                        state = 'up'
                        market_up = True
                    elif diff <= -3:
                        state = 'down'
                        market_down = True
                self.log_message(f"[Snapshot] Yükselen={rising_now} Düşen={falling_now} Toplam={len(usdt_syms)} Diff={diff} State={state if state else 'neutral'}")
            else:
                self.log_message(f"[Snapshot] İlk ölçüm: Yükselen={rising_now} Düşen={falling_now} Toplam={len(usdt_syms)}")
            self.market_trend_state = state
            # Sembol durumu
            base = self.get_base_symbol_from_binance(self.current_symbol)
            sym_full = base + 'USDT'
            symbol_up = symbol_down = False
            if sym_full in changes:
                cur = changes[sym_full]
                prev = self.prev_symbol_change
                if prev is not None:
                    symbol_up = cur > prev
                    symbol_down = cur < prev
                self.log_message(f"Momentum (tek sefer) {base}: cur={cur:.2f}% prev={prev if prev is not None else 'None'}")
                self.prev_symbol_change = cur
            self.prev_rising_count = rising_now
            self.auto_trade_decision(market_up, market_down, symbol_up, symbol_down)
        except Exception as e:
            self.log_message(f"Oto trade tetikleme hatası: {e}")
    
    def open_long_position(self):
        self.open_position("BUY")
    
    def open_short_position(self):
        self.open_position("SELL")
    
    def open_position(self, side):
        if not self.client:
            messagebox.showerror("Hata", "Önce API'ye bağlanın!")
            return
        
        try:
            position_size = float(self.position_size_var.get())
            leverage = int(self.leverage_var.get())
            
            if position_size <= 0:
                messagebox.showerror("Hata", "Pozisyon büyüklüğü 0'dan büyük olmalı!")
                return
            
            # Margin type: ISOLATED
            self.ensure_isolated_margin(self.current_symbol)
            # Set leverage
            self.client.futures_change_leverage(symbol=self.current_symbol, leverage=leverage)
            
            # Calculate quantity with lot size step
            raw_qty = position_size / max(1e-8, self.current_price)
            qty_float, qty_str = self.round_and_format_qty(self.current_symbol, raw_qty, price_hint=self.current_price)
            
            if qty_float <= 0:
                messagebox.showerror("Hata", "Hesaplanan miktar geçersiz (çok küçük). Position Size'i artırın.")
                return
            
            # Place market order
            # Try with retries utility
            order = self.place_market_order_with_retries(self.current_symbol, side, raw_qty, price_hint=self.current_price)
            self.log_message(f"Emir gönderildi: {side} {self.current_symbol} qty={qty_str}")
            
            side_text = "LONG" if side == "BUY" else "SHORT"
            self.log_message(f"{side_text} pozisyon açıldı - {self.current_symbol}: {qty_str} @ ${self.current_price:.4f}")
            
            messagebox.showinfo("Başarılı", f"{side_text} pozisyon açıldı!")
            
        except BinanceAPIException as e:
            error_msg = f"API Hatası: {e.message}"
            messagebox.showerror("Hata", error_msg)
            self.log_message(error_msg)
        except Exception as e:
            error_msg = f"Pozisyon açma hatası: {str(e)}"
            messagebox.showerror("Hata", error_msg)
            self.log_message(error_msg)
    
    def update_positions(self):
        if not self.client:
            return
        
        try:
            positions = self.client.futures_position_information()
            
            # Clear existing items
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            # reset hover cache for positions
            self._pos_row_tags = {}
            self._pos_hover_item = None
            
            any_pos = False
            unrealized_sum = 0.0
            # Add current positions
            row_i = 0
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    any_pos = True
                    symbol = pos['symbol']
                    size = float(pos['positionAmt'])
                    entry_price = float(pos['entryPrice'])
                    unrealized_pnl = float(pos.get('unRealizedProfit', pos.get('unrealizedProfit', 0)))
                    unrealized_sum += unrealized_pnl
                    side = "LONG" if size > 0 else "SHORT"
                    tag = 'odd' if (row_i % 2) else 'even'
                    row_i += 1
                    # Insert into tree
                    self.positions_tree.insert("", "end", values=(
                        symbol, side, f"{abs(size):.6f}", 
                        f"${entry_price:.4f}", f"${unrealized_pnl:.2f}"
                    ), tags=(tag,))
            # Update PNL panel
            self.update_pnl_panel(positions if any_pos else [])
            
            # Hedef PNL kontrolü (seçili sembol için)
            try:
                target = float(self.target_pnl_var.get())
            except Exception:
                target = 0.0
            if self.auto_trade_enabled and target > 0:
                sym_unreal = 0.0
                for pos in positions:
                    if pos.get('symbol') == self.current_symbol:
                        sym_unreal += float(pos.get('unRealizedProfit', pos.get('unrealizedProfit', 0)))
                if sym_unreal >= target:
                    self.log_message(f"Hedef PNL {target:.2f} ulaşıldı, pozisyon kapatılıyor: {self.current_symbol}")
                    self.close_symbol_positions(self.current_symbol)
            
            # Update income history & totals throttled
            now_ts = time.time()
            if not hasattr(self, 'last_income_fetch_ts'):
                self.last_income_fetch_ts = 0
            if now_ts - self.last_income_fetch_ts > 60:  # her 60 sn
                self.update_income_history()
                self.last_income_fetch_ts = now_ts
            # Update totals label
            realized_sum = getattr(self, 'realized_pnl_sum', 0.0)
            total = realized_sum + unrealized_sum
            self.total_pnl_label.config(text=f"Toplam PNL: {total:.2f} (U:{unrealized_sum:.2f} | R:{realized_sum:.2f})")
                    
        except Exception as e:
            self.log_message(f"Pozisyon güncelleme hatası: {str(e)}")
    
    # ------------------ Market Monitor (CoinPaprika) ------------------
    def start_market_monitor(self):
        if self.market_thread_running:
            return
        self.market_thread_running = True
        self.market_thread = threading.Thread(target=self.market_monitor_loop)
        self.market_thread.daemon = True
        self.market_thread.start()
        self.log_message("Piyasa izleme (CoinPaprika) başlatıldı.")
    
    def stop_market_monitor(self):
        self.market_thread_running = False
    
    def round_step(self, value, step):
        try:
            dval = Decimal(str(value))
            dstep = Decimal(str(step))
            # Quantize down to step precision
            q = dval.quantize(dstep, rounding=ROUND_DOWN)
            # Avoid negative zero
            if q == 0:
                return 0.0
            return float(q)
        except Exception:
            return value
    
    def get_symbol_lot_step(self, symbol):
        # Geriye: (step, min_qty) float (geriye dönük uyumluluk)
        try:
            step_str, min_qty_str, _ = self.get_symbol_lot_info(symbol)
            return (float(step_str), float(min_qty_str))
        except Exception:
            return (0.000001, 0.0)

    def get_symbol_lot_info(self, symbol):
        # Döner: (step_str, min_qty_str, decimals, notional_min, qty_precision)
        try:
            if not hasattr(self, '_exchange_cache'):
                self._exchange_cache = {'ts': 0, 'data': None}
            now = time.time()
            if not self._exchange_cache['data'] or now - self._exchange_cache['ts'] > 600:
                resp = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=20)
                if resp.status_code == 200:
                    self._exchange_cache['data'] = resp.json()
                    self._exchange_cache['ts'] = now
            data = self._exchange_cache['data'] or {}
            for s in data.get('symbols', []):
                if s.get('symbol') == symbol:
                    # Varsayılanlar
                    lot_step = None
                    lot_min = None
                    market_step = None
                    market_min = None
                    notional_min = 0.0
                    qty_prec = s.get('quantityPrecision', None)
                    for f in s.get('filters', []):
                        ftype = f.get('filterType')
                        if ftype == 'LOT_SIZE':
                            lot_step = f.get('stepSize')
                            lot_min = f.get('minQty')
                        elif ftype == 'MARKET_LOT_SIZE':
                            market_step = f.get('stepSize')
                            market_min = f.get('minQty')
                        elif ftype in ('MIN_NOTIONAL', 'NOTIONAL'):
                            notional_min = float(f.get('notional', notional_min))
                    # Öncelik: LOT_SIZE
                    step_str = lot_step or market_step or '0.000001'
                    min_qty_str = lot_min or market_min or '0.0'
                    # Ondalık sayısı step'ten
                    dec = 0
                    if '.' in step_str:
                        dec = len(step_str.split('.')[1].rstrip('0'))
                    if isinstance(qty_prec, int):
                        dec = min(dec, max(qty_prec, 0))
                    return (step_str, min_qty_str, dec, notional_min, qty_prec if isinstance(qty_prec, int) else dec)
            return ('0.000001', '0.0', 6, 0.0, 6)
        except Exception:
            return ('0.000001', '0.0', 6, 0.0, 6)

    def ceil_to_step(self, value, step_str):
        try:
            dval = Decimal(str(value))
            dstep = Decimal(step_str)
            n = (dval / dstep).to_integral_value(rounding=ROUND_DOWN)
            if n * dstep < dval:
                n = n + 1
            return n * dstep
        except Exception:
            return Decimal(str(value))

    def round_and_format_qty(self, symbol, qty, price_hint=None, force_step=None, force_decimals=None):
        # qty: float quantity; returns (qty_float, qty_str) formatted to step and meeting notional
        try:
            step_str, min_qty_str, dec, notional_min, qty_prec = self.get_symbol_lot_info(symbol)
            if force_step:
                step_str = force_step
            # min qty
            dval = Decimal(str(max(qty, float(min_qty_str))))
            dstep = Decimal(step_str)
            q = dval.quantize(dstep, rounding=ROUND_DOWN)
            if q <= 0:
                q = Decimal(min_qty_str)
            # notional kontrolü
            if notional_min and price_hint and float(q) * float(price_hint) < notional_min:
                need = self.ceil_to_step(Decimal(str(notional_min)) / Decimal(str(price_hint)), step_str)
                q = need
            # precision uygula
            dec_use = max(dec, qty_prec if isinstance(qty_prec, int) else dec)
            if force_decimals is not None:
                dec_use = force_decimals
            qty_str = f"{q:.{dec_use}f}" if dec_use > 0 else f"{int(q)}"
            return float(q), qty_str
        except Exception:
            q = max(qty, 0.0)
            return q, str(q)

    def place_market_order_with_retries(self, symbol, side, qty_raw, price_hint=None):
        # Çoklu strateji ile -1111 precision hatasına karşı dene
        strategies = []
        # 1) Varsayılan (LOT_SIZE/MARKET_LOT_SIZE)
        step_str, min_qty_str, dec, notional_min, qprec = self.get_symbol_lot_info(symbol)
        strategies.append((step_str, dec))
        # 2) 0.1 adımı dene
        strategies.append(('0.1', 1))
        # 3) 1 adımı dene
        strategies.append(('1', 0))
        last_err = None
        for step, decimals in strategies:
            qf, qs = self.round_and_format_qty(symbol, qty_raw, price_hint=price_hint, force_step=step, force_decimals=decimals)
            try:
                self.log_message(f"OrderTry {symbol} step={step} dec={decimals} -> qty={qs}")
                return self.client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=qs)
            except BinanceAPIException as e:
                last_err = e
                if e.code != -1111:
                    raise
                continue
        # son hata
        if last_err:
            raise last_err

    def get_current_position(self, symbol):
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            if positions:
                pos = positions[0]
                amt = float(pos['positionAmt'])
                entry = float(pos['entryPrice'])
                return amt, entry
        except Exception:
            pass
        return 0.0, 0.0

    def ensure_isolated_margin(self, symbol):
        try:
            self.client.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
            self.log_message(f"Margin tipi ISOLATED ayarlandı: {symbol}")
        except BinanceAPIException as e:
            # -4046: No need to change margin type or already isolated
            try:
                code = getattr(e, 'code', None)
                msg = getattr(e, 'message', '')
            except Exception:
                code = None
                msg = ''
            if code in (-4046, 4046) or 'No need to change' in str(msg) or 'margin type is same' in str(msg).lower():
                self.log_message(f"Margin tipi zaten ISOLATED: {symbol}")
                return
            else:
                self.log_message(f"Margin tipi değiştirilemedi: {symbol} - {e}")
                raise
        except Exception as ex:
            self.log_message(f"Margin tipi hata: {symbol} - {ex}")
            # Devam et (bazı durumlarda mevcut pozisyon varken değiştirilemez)
    
    def log_trade(self, symbol, qty, entry_price, exit_price, pnl):
        try:
            row = {
                'time': datetime.now().strftime('%m-%d %H:%M'),
                'symbol': symbol,
                'qty': qty,
                'entry': entry_price,
                'exit': exit_price,
                'pnl': pnl
            }
            line = f"{row['time']},{row['symbol']},{row['qty']},{row['entry']},{row['exit']},{row['pnl']}\n"
            with open('trades_history.csv', 'a', encoding='utf-8') as f:
                f.write(line)
        except Exception as e:
            self.log_message(f"Trade log yazılamadı: {e}")
    
    def read_local_trades(self, max_rows: int = 200):
        items = []
        try:
            if not os.path.exists('trades_history.csv'):
                return items
            with open('trades_history.csv', 'r', encoding='utf-8') as f:
                lines = f.readlines()[-max_rows:]
            for ln in lines:
                try:
                    t, sym, qty, entry, exitp, pnl = ln.strip().split(',')
                    items.append({'time': t, 'symbol': sym, 'pnl': float(pnl)})
                except Exception:
                    continue
        except Exception:
            pass
        return items
    
    def update_cumulative_pnl_label(self):
        try:
            local = sum(r['pnl'] for r in self.read_local_trades(max_rows=100000))
            self.cum_pnl_label.config(text=f"Kümülatif PNL: {local:.2f}")
            # Ayrıca dosyaya toplam PNL anlık özetini yaz
            self.local_total_pnl = local
            self.write_totals_snapshot()
        except Exception:
            pass

    def ensure_csv_header(self, path, header_line):
        try:
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(header_line + "\n")
        except Exception:
            pass

    def write_totals_snapshot(self):
        try:
            totals_path = 'totals_history.csv'
            self.ensure_csv_header(totals_path, 'time,local_total,binance_realized,total')
            local_total = getattr(self, 'local_total_pnl', 0.0)
            binance_realized = getattr(self, 'binance_realized_total', 0.0)
            total = float(local_total) + float(binance_realized)
            line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},{local_total:.2f},{binance_realized:.2f},{total:.2f}\n"
            with open(totals_path, 'a', encoding='utf-8') as f:
                f.write(line)
            self.log_message("Toplam PNL kaydedildi: totals_history.csv")
        except Exception as e:
            self.log_message(f"Toplam PNL yazılamadı: {e}")
    
    def check_for_updates(self):
        """Güncelleme kontrolü yap ve diyaloğu göster"""
        try:
            if not SoftwareUpdater or not UpdateDialog:
                messagebox.showinfo("Bilgi", "Güncelleme modülü yüklenemedi.")
                return
            
            self.log_message("Güncelleme kontrol ediliyor...")
            
            def check_updates_thread():
                try:
                    updater = SoftwareUpdater()
                    has_update, message = updater.check_for_updates()
                    
                    # Ana thread'de UI'yi güncelle
                    self.root.after(0, lambda: self.show_update_dialog(updater, has_update, message))
                    
                except Exception as e:
                    error_msg = f"Güncelleme kontrolü hatası: {e}"
                    self.root.after(0, lambda: messagebox.showerror("Hata", error_msg))
            
            # Thread'de kontrol et (UI bloke olmasın)
            threading.Thread(target=check_updates_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Güncelleme kontrolü başlatılamadı: {e}")
    
    def show_update_dialog(self, updater, has_update, message):
        """Güncelleme diyaloğunu göster"""
        try:
            dialog = UpdateDialog(self.root, updater)
            dialog.show_update_dialog(has_update, message)
            
            if has_update:
                self.log_message("Yeni güncelleme mevcut!")
                self.show_update_warning(True)
            else:
                self.log_message("Yazılım güncel.")
                self.show_update_warning(False)
                
        except Exception as e:
            messagebox.showerror("Hata", f"Güncelleme diyaloğu gösterilemedi: {e}")
    
    def show_update_warning(self, show):
        """Güncelleme uyarısını göster/gizle"""
        try:
            if not self.update_warning_label:
                return
                
            if show:
                warning_text = self.tr('update_available')
                self.update_warning_label.config(text=warning_text)
                self.update_available = True
            else:
                self.update_warning_label.config(text="")
                self.update_available = False
                
        except Exception as e:
            print(f"Güncelleme uyarısı gösterme hatası: {e}")
    
    def auto_check_updates_on_startup(self):
        """Program başlangıcında otomatik güncelleme kontrolü"""
        try:
            if not SoftwareUpdater or not UpdateDialog:
                return
            
            def auto_check():
                try:
                    # 3 saniye bekle (program tam yüklensin)
                    time.sleep(3)
                    
                    updater = SoftwareUpdater()
                    has_update, message = updater.check_for_updates()
                    
                    if has_update:
                        # Güncelleme uyarısını göster
                        self.root.after(0, lambda: self.show_update_warning(True))
                        
                        # Güncelleme varsa kullanıcıya sor
                        def ask_user():
                            result = messagebox.askyesno(
                                "Güncelleme Mevcut", 
                                f"{message}\n\nGüncellemeyi şimdi yüklemek istiyor musunuz?",
                                parent=self.root
                            )
                            if result:
                                self.show_update_dialog(updater, has_update, message)
                        
                        self.root.after(0, ask_user)
                    else:
                        # Güncelleme uyarısını gizle
                        self.root.after(0, lambda: self.show_update_warning(False))
                        
                except Exception as e:
                    print(f"Otomatik güncelleme kontrolü hatası: {e}")
            
            # Thread'de otomatik kontrol et
            threading.Thread(target=auto_check, daemon=True).start()
            
        except Exception as e:
            print(f"Otomatik güncelleme kontrolü başlatılamadı: {e}")
    
    def update_symbol_list(self):
        try:
            symbols = self.get_top100_symbols_any()
            avail_set = self.get_binance_usdt_perp_set()
            allowed = [s + 'USDT' for s in symbols if (s + 'USDT') in avail_set]
            if not allowed:
                return
            current_values = list(self.symbol_combo.cget('values'))
            if current_values != allowed:
                self.symbol_combo['values'] = allowed
            if self.symbol_var.get() not in allowed:
                self.symbol_var.set(allowed[0])
                self.on_symbol_change()
        except Exception as e:
            self.log_message(f"Sembol listesi güncellenemedi: {e}")
    
    def get_binance_usdt_perp_set(self):
        try:
            if not hasattr(self, '_perp_cache'):
                self._perp_cache = {'ts': 0, 'set': set()}
            now = time.time()
            if not self._perp_cache['set'] or now - self._perp_cache['ts'] > 600:
                ex = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=20)
                sset = set()
                if ex.status_code == 200:
                    info = ex.json()
                    for s in info.get('symbols', []):
                        try:
                            if s.get('contractType') == 'PERPETUAL' and s.get('quoteAsset') == 'USDT' and s.get('status') == 'TRADING':
                                sset.add(s.get('symbol'))
                        except Exception:
                            continue
                self._perp_cache['set'] = sset
                self._perp_cache['ts'] = now
            return self._perp_cache['set']
        except Exception:
            return set()
    
    def get_available_usdt(self):
        try:
            bals = self.client.futures_account_balance()
            for b in bals:
                if b.get('asset') == 'USDT':
                    return float(b.get('availableBalance', b.get('balance', 0.0)))
        except Exception:
            pass
        return max(0.0, self.balance)
    
    def calc_auto_usdt_amount(self):
        try:
            perc = float(self.auto_percent_var.get())
        except Exception:
            perc = 0.0
        if perc > 0:
            avail = self.get_available_usdt()
            return max(0.0, avail * perc / 100.0)
        # fallback manual position size
        try:
            return max(0.0, float(self.position_size_var.get()))
        except Exception:
            return 0.0
    
    def ensure_long_position(self, symbol_ctx=None):
        # Yalnızca seçili sembol için çalış
        if symbol_ctx and symbol_ctx != self.current_symbol:
            return
        amt, entry = self.get_current_position(self.current_symbol)
        if amt > 0:
            self.log_message("Zaten LONG pozisyon var, koru")
            return
        # ensure isolated margin and set leverage
        try:
            self.ensure_isolated_margin(self.current_symbol)
        except Exception:
            pass
        try:
            lev = int(self.leverage_var.get())
            self.client.futures_change_leverage(symbol=self.current_symbol, leverage=lev)
        except Exception:
            pass
        if amt < 0:
            # close short
            try:
                t = self.client.futures_symbol_ticker(symbol=self.current_symbol)
                exit_price = float(t.get('price', 0))
            except Exception:
                exit_price = self.current_price
            pnl = (entry - exit_price) * abs(amt)  # short close pnl
            self.client.futures_create_order(symbol=self.current_symbol, side='BUY', type='MARKET', quantity=abs(amt))
            self.log_trade(self.current_symbol, abs(amt), entry, exit_price, pnl)
            self.root.after(0, self.update_cumulative_pnl_label)
            self.root.after(0, self.write_totals_snapshot)
        usdt_amount = self.calc_auto_usdt_amount()
        raw = max(1e-8, usdt_amount) / max(1e-8, self.current_price)
        qty_float, qty_str = self.round_and_format_qty(self.current_symbol, raw, price_hint=self.current_price)
        step_str, min_qty_str, dec, notional_min, qprec = self.get_symbol_lot_info(self.current_symbol)
        self.log_message(f"OrderCheck {self.current_symbol} step={step_str} minQty={min_qty_str} notionalMin={notional_min} qPrec={qprec} raw={raw:.8f} price={self.current_price:.4f} -> qty={qty_str}")
        self.place_market_order_with_retries(self.current_symbol, 'BUY', raw, price_hint=self.current_price)
        self.log_message(f"Otomatik LONG açıldı qty={qty_float}")
    
    def get_selected_symbol(self):
        try:
            sel = self.positions_tree.selection()
            if not sel:
                return None
            vals = self.positions_tree.item(sel[0], 'values')
            return vals[0] if vals else None
        except Exception:
            return None

    def close_selected_position(self):
        sym = self.get_selected_symbol()
        if not sym:
            messagebox.showinfo("Bilgi", "Lütfen tablodan bir pozisyon seçin.")
            return
        self.close_symbol_positions(sym)

    def open_settings_dialog(self):
        try:
            info = (
                f"Ortam: {self.env_var.get()}\n"
                f"Trading Modu: {self.trading_mode_var.get()}\n"
                f"Interval(sn): {self.market_interval_var.get()}\n"
                f"Hedef PNL: {self.target_pnl_var.get()}\n"
                f"Nötr Kapat(%): {self.neutral_close_pct_var.get()}\n"
            )
            messagebox.showinfo("Ayarlar", info)
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def close_symbol_positions(self, symbol):
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            if not positions:
                return
            pos = positions[0]
            amt = float(pos.get('positionAmt', 0))
            entry = float(pos.get('entryPrice', 0))
            if amt == 0:
                return
            # Exit price from ticker
            try:
                t = self.client.futures_symbol_ticker(symbol=symbol)
                exit_price = float(t.get('price', 0))
            except Exception:
                exit_price = self.current_price if symbol == self.current_symbol else entry
            side = 'SELL' if amt > 0 else 'BUY'
            self.client.futures_create_order(symbol=symbol, side=side, type='MARKET', quantity=abs(amt))
            # Approx realized pnl
            pnl = (exit_price - entry) * amt  # amt signed
            self.log_trade(symbol, abs(amt), entry, exit_price, pnl)
            self.log_message(f"Pozisyon kapatıldı: {symbol}")
            self.root.after(0, self.update_cumulative_pnl_label)
            self.root.after(0, self.write_totals_snapshot)
        except Exception as e:
            self.log_message(f"Sembol kapatma hatası: {e}")
    
    def ensure_short_position(self, symbol_ctx=None):
        # Yalnızca seçili sembol için çalış
        if symbol_ctx and symbol_ctx != self.current_symbol:
            return
        amt, entry = self.get_current_position(self.current_symbol)
        if amt < 0:
            self.log_message("Zaten SHORT pozisyon var, koru")
            return
        # set leverage
        try:
            lev = int(self.leverage_var.get())
            self.client.futures_change_leverage(symbol=self.current_symbol, leverage=lev)
        except Exception:
            pass
        if amt > 0:
            # close long
            try:
                t = self.client.futures_symbol_ticker(symbol=self.current_symbol)
                exit_price = float(t.get('price', 0))
            except Exception:
                exit_price = self.current_price
            pnl = (exit_price - entry) * abs(amt)  # long close pnl
            self.client.futures_create_order(symbol=self.current_symbol, side='SELL', type='MARKET', quantity=abs(amt))
            self.log_trade(self.current_symbol, abs(amt), entry, exit_price, pnl)
            self.root.after(0, self.update_cumulative_pnl_label)
            self.root.after(0, self.write_totals_snapshot)
        # open short with lot step
        usdt_amount = self.calc_auto_usdt_amount()
        raw = max(1e-8, usdt_amount) / max(1e-8, self.current_price)
        qty_float, qty_str = self.round_and_format_qty(self.current_symbol, raw, price_hint=self.current_price)
        # Debug log
        step_str, min_qty_str, dec, notional_min, qprec = self.get_symbol_lot_info(self.current_symbol)
        self.log_message(f"OrderCheck {self.current_symbol} step={step_str} minQty={min_qty_str} notionalMin={notional_min} qPrec={qprec} raw={raw:.8f} price={self.current_price:.4f} -> qty={qty_str}")
        self.place_market_order_with_retries(self.current_symbol, 'SELL', raw, price_hint=self.current_price)
        self.log_message(f"Otomatik SHORT açıldı qty={qty_float}")
    
    def auto_trade_decision(self, market_up, market_down, symbol_up, symbol_down):
        try:
            now = time.time()
            cooldown = max(10, self.market_interval_seconds)
            if now - self.last_auto_action_time < cooldown:
                return
            self.log_message(f"Seçili sembol: {self.current_symbol}")
            self.log_message(f"Oto karar: market_up={market_up}, market_down={market_down}, symbol_up={symbol_up}, symbol_down={symbol_down}")
            if market_up and symbol_up:
                self.log_message("Koşul sağlandı (LONG) -> emir gönderiliyor")
                self.ensure_long_position()
                self.last_auto_action_time = now
            elif market_down and symbol_down:
                self.log_message("Koşul sağlandı (SHORT) -> emir gönderiliyor")
                self.ensure_short_position()
                self.last_auto_action_time = now
            else:
                self.log_message("Oto trade: nötr, bekleniyor")
        except Exception as e:
            self.log_message(f"Otomatik işlem hatası: {e}")
    
    def market_monitor_loop(self):
        while self.market_thread_running:
            try:
                interval = self.market_interval_seconds
                # Saat başı top100 (Paprika veya Binance fallback)
                symbols = self.get_top100_symbols_any()
                # Binance'ten 24h değişim yüzdelerini çek
                changes = self.fetch_binance_futures_24h_changes()
                # expose latest changes for UI
                self.latest_changes = changes
                # Sembol listesini GUI'de güncelle
                self.root.after(0, self.update_symbol_list)
                if changes and symbols:
                    base0 = self.get_base_symbol_from_binance(self.current_symbol)
                    # seçili sembolden başlasın (list rotate); yoksa öne ekle
                    us = [s + 'USDT' for s in symbols]
                    if base0 in symbols:
                        idx = symbols.index(base0)
                        rot = symbols[idx:] + symbols[:idx]
                        usdt_syms = [s + 'USDT' for s in rot]
                    else:
                        usdt_syms = [base0 + 'USDT'] + us
                    # Mevcut rising sayısı (pozitif 24h değişim)
                    rising_now = sum(1 for sym in usdt_syms if sym in changes and changes[sym] > 0)
                    falling_now = max(0, len(usdt_syms) - rising_now)
                    # 3-coin simetrik latch kuralı (durum koruma)
                    prev = self.prev_rising_count
                    market_up_now = False
                    market_down_now = False
                    state = getattr(self, 'market_trend_state', None)
                    if prev is not None:
                        diff = rising_now - prev
                        if state == 'up':
                            market_up_now = True
                            if diff <= -3:
                                state = 'down'
                                market_up_now = False
                                market_down_now = True
                        elif state == 'down':
                            market_down_now = True
                            if diff >= 3:
                                state = 'up'
                                market_down_now = False
                                market_up_now = True
                        else:
                            if diff >= 3:
                                state = 'up'
                                market_up_now = True
                            elif diff <= -3:
                                state = 'down'
                                market_down_now = True
                        self.log_message(f"[Piyasa] Yükselen={rising_now} Düşen={falling_now} Toplam={len(usdt_syms)} Diff={diff} State={state if state else 'neutral'}")
                    else:
                        self.log_message(f"[Piyasa] İlk ölçüm: Yükselen={rising_now} Düşen={falling_now} Toplam={len(usdt_syms)}")
                    if market_up_now:
                        self.root.after(0, lambda: self.set_market_status(self.tr('market_up'), 'green'))
                    elif market_down_now:
                        self.root.after(0, lambda: self.set_market_status(self.tr('market_down'), 'red'))
                    else:
                        self.root.after(0, lambda: self.set_market_status(self.tr('market_neutral'), '#444444'))
                    self.prev_rising_count = rising_now
                    self.market_trend_state = state
                    # Seçili sembol durumu
                    base = self.get_base_symbol_from_binance(self.current_symbol)
                    sym_full = base + 'USDT'
                    coin_up = coin_down = False
                    if sym_full in changes:
                        cur = changes[sym_full]
                        prev = self.prev_symbol_change
                        coin_up = (prev is not None) and (cur > prev)
                        coin_down = (prev is not None) and (cur < prev)
                        self.log_message(f"Momentum {base}: cur={cur:.2f}% prev={prev if prev is not None else 'None'}")
                        self.prev_symbol_change = cur
                        if coin_up:
                            self.root.after(0, lambda b=base: self.set_symbol_status(f"{b} {self.tr('symbol_up_suffix')}", 'green'))
                        elif coin_down:
                            self.root.after(0, lambda b=base: self.set_symbol_status(f"{b} {self.tr('symbol_down_suffix')}", 'red'))
                        else:
                            self.root.after(0, lambda b=base: self.set_symbol_status(f"{b} {self.tr('symbol_neutral_suffix')}", '#444444'))
                    
                    # Otomatik işlem kararı
                    if self.auto_trade_enabled and self.client:
                        if market_up_now and coin_up:
                            self.log_message(f"[Seçili: {self.current_symbol}] Koşul sağlandı (LONG) -> planlanıyor")
                            self.root.after(0, lambda sc=self.current_symbol: self.ensure_long_position(symbol_ctx=sc))
                        elif market_down_now and coin_down:
                            self.log_message(f"[Seçili: {self.current_symbol}] Koşul sağlandı (SHORT) -> planlanıyor")
                            self.root.after(0, lambda sc=self.current_symbol: self.ensure_short_position(symbol_ctx=sc))
                        else:
                            # piyasa nötr -> eşik kontrolü ile kapat
                            try:
                                thr = float(self.neutral_close_pct_var.get())
                            except Exception:
                                thr = 2.0
                            if not market_up_now and not market_down_now and sym_full in changes:
                                if abs(changes[sym_full]) >= thr:
                                    self.root.after(0, lambda s=self.current_symbol: self.close_symbol_positions(s))
                time.sleep(max(5, interval))
            except Exception as e:
                self.log_message(f"Piyasa izleme hatası: {e}")
                time.sleep(10)
    
    def get_top100_symbols_paprika(self):
        # Saatte 1 kez günceller ve coin100.txt'ye yazar
        try:
            now = time.time()
            if self.top100_symbols and now - self.top100_last_fetch < 3600:
                return self.top100_symbols
            url = "https://api.coinpaprika.com/v1/tickers"
            params = {"quotes": "USD"}
            headers = {"User-Agent": "BinanceFuturesGUI/1.0 (+contact: contact@example.com)"}
            resp = requests.get(url, params=params, headers=headers, timeout=20)
            if resp.status_code != 200:
                # fallback kullanılacak
                return self.top100_symbols
            data = resp.json()
            try:
                data_sorted = sorted(data, key=lambda x: int(x.get('rank', 999999)))[:100]
            except Exception:
                data_sorted = data[:100]
            syms = []
            for item in data_sorted:
                sym = item.get('symbol')
                if sym and sym.isalpha():
                    syms.append(sym.upper())
            self.top100_symbols = syms
            self.top100_last_fetch = now
            # Dosyaya yaz
            self.write_top100_file(syms)
            return self.top100_symbols
        except Exception:
            return self.top100_symbols
    
    def get_top100_symbols_from_binance(self):
        # Binance Futures USDT perpetual en yüksek hacimli 100 sembol
        try:
            now = time.time()
            if self.top100_symbols and now - self.top100_last_fetch < 3600:
                return self.top100_symbols
            # Tüm 24h ticker verisi
            tick = requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr", timeout=20)
            if tick.status_code != 200:
                return self.top100_symbols
            tickers = {t['symbol']: t for t in tick.json() if 'symbol' in t}
            # Perpetual USDT sembollerini filtrele
            ex = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=20)
            if ex.status_code != 200:
                return self.top100_symbols
            info = ex.json()
            syms_meta = []
            for s in info.get('symbols', []):
                try:
                    if s.get('contractType') == 'PERPETUAL' and s.get('quoteAsset') == 'USDT' and s.get('status') == 'TRADING':
                        sym = s.get('symbol')
                        if sym in tickers:
                            qv = float(tickers[sym].get('quoteVolume', 0.0))
                            syms_meta.append((sym, qv))
                except Exception:
                    continue
            syms_meta.sort(key=lambda x: x[1], reverse=True)
            top = [sym[:-4] for sym, _ in syms_meta[:100] if sym.endswith('USDT')]
            if top:
                self.top100_symbols = top
                self.top100_last_fetch = now
                self.write_top100_file(top)
            return self.top100_symbols
        except Exception:
            return self.top100_symbols
    
    def get_top100_symbols_any(self):
        # Önce CoinPaprika, olmazsa Binance fallback
        syms = self.get_top100_symbols_paprika()
        if not syms or len(syms) < 50:
            syms = self.get_top100_symbols_from_binance()
        return syms
    
    def write_top100_file(self, syms):
        try:
            with open("coin100.txt", "w", encoding="utf-8") as f:
                for s in syms:
                    f.write(f"{s}\n")
            self.log_message("Top100 coin listesi coin100.txt dosyasına yazıldı.")
        except Exception as e:
            self.log_message(f"coin100.txt yazılamadı: {e}")
    
    def fetch_binance_futures_24h_changes(self):
        try:
            url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
            resp = requests.get(url, timeout=20)
            if resp.status_code != 200:
                self.log_message(f"Binance 24h ticker hata: {resp.status_code}")
                return None
            data = resp.json()
            changes = {}
            for item in data:
                sym = item.get('symbol')
                p = item.get('priceChangePercent')
                try:
                    changes[sym] = float(p)
                except Exception:
                    continue
            return changes
        except Exception as e:
            self.log_message(f"Binance değişimleri alınamadı: {e}")
            return None
    
    def update_income_history(self):
        try:
            # Son 7 gün realized PNL (Binance)
            end_ms = int(time.time() * 1000)
            start_ms = end_ms - 7*24*60*60*1000
            incomes = []
            try:
                incomes = self.client.futures_income_history(startTime=start_ms, endTime=end_ms, limit=1000)
            except Exception:
                incomes = []
            # Clear history tree
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            # reset hover cache for history
            self._hist_row_tags = {}
            self._hist_hover_item = None
            realized_sum = 0.0
            # Zebra tag'leri
            self.history_tree.tag_configure('even', background='#111827')
            self.history_tree.tag_configure('odd', background='#0f172a')
            r = 0
            # Binance incomes
            for inc in incomes:
                ts = int(inc.get('time', inc.get('T', 0)))
                tstr = datetime.fromtimestamp(ts/1000).strftime('%m-%d %H:%M') if ts else ''
                sym = inc.get('symbol', '')
                pnl = float(inc.get('income', 0.0))
                itype = inc.get('incomeType', '')
                # Sadece realized ve benzeri kalemleri topla
                if itype in ('REALIZED_PNL', 'COMMISSION', 'FUNDING_FEE'):
                    realized_sum += pnl
                tag = 'odd' if (r % 2) else 'even'
                r += 1
                self.history_tree.insert('', 'end', values=(tstr, sym, f"{pnl:.2f}", itype), tags=(tag,))
            # Lokal kapanış günlüğü (fallback)
            local_sum = 0.0
            for row in self.read_local_trades():
                tag = 'odd' if (r % 2) else 'even'
                r += 1
                self.history_tree.insert('', 'end', values=(row['time'], row['symbol'], f"{row['pnl']:.2f}", 'LOCAL'), tags=(tag,))
                local_sum += row['pnl']
            self.binance_realized_total = realized_sum
            self.realized_pnl_sum = realized_sum + local_sum
            # Kümülatif PNL (lokal log tabanlı)
            self.update_cumulative_pnl_label()
        except Exception as e:
            self.log_message(f"Gelir geçmişi alınamadı: {e}")
    
    def _get_assets_dir(self):
        import os
        d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
        os.makedirs(d, exist_ok=True)
        return d

    def _init_banner_logo(self):
        try:
            import os, io, requests
            from PIL import Image, ImageTk, ImageDraw
            url = 'https://pbs.twimg.com/profile_images/1973360241547837441/zmewfn7J_400x400.jpg'
            assets = self._get_assets_dir()
            cache_path = os.path.join(assets, 'banner_logo.jpg')
            try:
                resp = requests.get(url, timeout=10)
                if resp.ok:
                    with open(cache_path, 'wb') as f:
                        f.write(resp.content)
                elif not os.path.exists(cache_path):
                    return
            except Exception:
                if not os.path.exists(cache_path):
                    return
            img = Image.open(cache_path).convert('RGBA').resize((48, 48), Image.LANCZOS)
            mask = Image.new('L', (48, 48), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 48, 48), fill=255)
            img.putalpha(mask)
            self.banner_logo_imgtk = ImageTk.PhotoImage(img)
            if hasattr(self, 'logo_label'):
                self.logo_label.config(image=self.banner_logo_imgtk)
        except Exception as e:
            try:
                self.log(f'Banner logo load failed: {e}')
            except Exception:
                pass
    
    def _init_advertisement(self):
        try:
            import os, requests
            from PIL import Image, ImageTk
            import webbrowser
            
            ad_url = 'https://apricot-rational-booby-281.mypinata.cloud/ipfs/bafybeib5xnpuwznl34pmdbt2iarfifinykrv5hbijhhwrdm5xdqppboble'
            target_url = 'https://memexsol.memextoken.org'
            
            assets = self._get_assets_dir()
            ad_cache_path = os.path.join(assets, 'advertisement.jpg')
            
            # Reklam görselini indir
            try:
                resp = requests.get(ad_url, timeout=15)
                if resp.ok:
                    with open(ad_cache_path, 'wb') as f:
                        f.write(resp.content)
                elif not os.path.exists(ad_cache_path):
                    return
            except Exception:
                if not os.path.exists(ad_cache_path):
                    return
            
            # Görsel yükle ve boyutlandır
            img = Image.open(ad_cache_path).convert('RGBA').resize((240, 240), Image.LANCZOS)
            self.ad_imgtk = ImageTk.PhotoImage(img)
            
            # Label'ı güncelle ve tıklanabilir yap
            if hasattr(self, 'ad_label'):
                self.ad_label.config(image=self.ad_imgtk, text="", cursor="hand2")
                self.ad_label.bind("<Button-1>", lambda e: webbrowser.open(target_url))
                self.log_message("Reklam görseli yüklendi.")
            
        except Exception as e:
            try:
                self.log_message(f'Reklam yükleme hatası: {e}')
            except Exception:
                pass

    def _restore_prev_hover(self, tree, hover_attr, map_attr):
        prev = getattr(self, hover_attr, None)
        if prev and prev in getattr(self, map_attr, {}):
            try:
                orig = getattr(self, map_attr)[prev]
                tree.item(prev, tags=orig)
            except Exception:
                pass
        setattr(self, hover_attr, None)

    def _on_positions_tree_motion(self, event):
        self._tree_hover_generic(self.positions_tree, event, '_pos_hover_item', '_pos_row_tags')

    def _on_positions_tree_leave(self, event):
        self._restore_prev_hover(self.positions_tree, '_pos_hover_item', '_pos_row_tags')

    def _on_history_tree_motion(self, event):
        self._tree_hover_generic(self.history_tree, event, '_hist_hover_item', '_hist_row_tags')

    def _on_history_tree_leave(self, event):
        self._restore_prev_hover(self.history_tree, '_hist_hover_item', '_hist_row_tags')

    def _tree_hover_generic(self, tree, event, hover_attr, map_attr):
        row_id = tree.identify_row(event.y)
        if not row_id:
            self._restore_prev_hover(tree, hover_attr, map_attr)
            return
        current = getattr(self, hover_attr, None)
        if row_id == current:
            return
        # restore previous
        self._restore_prev_hover(tree, hover_attr, map_attr)
        # apply hover
        try:
            orig_tags = tree.item(row_id, 'tags') or ()
            getattr(self, map_attr)[row_id] = orig_tags
            tree.item(row_id, tags=('hover',))
            setattr(self, hover_attr, row_id)
        except Exception:
            pass

    def _init_treeview_sort(self, tree, columns):
        if not hasattr(self, '_tree_sort_state'):
            self._tree_sort_state = {}
        for col in columns:
            tree.heading(col, text=col, command=lambda c=col, t=tree: self._treeview_sort_by(t, c))

    def _treeview_sort_by(self, tree, col):
        # Determine state
        key = str(tree)
        state = self._tree_sort_state.get(key, {'col': None, 'asc': True})
        asc = not state['asc'] if state['col'] == col else True
        # Collect data
        items = []
        for iid in tree.get_children(''):
            val = tree.set(iid, col)
            try:
                v = float(val.replace('%','').replace('$','').replace(',',''))
            except Exception:
                v = val
            items.append((v, iid))
        items.sort(reverse=not asc)
        # Reorder and re-zebra
        for i, (_, iid) in enumerate(items):
            tree.move(iid, '', i)
            tag = 'odd' if (i % 2) else 'even'
            try:
                # keep hover if this is current hovered row
                current_hover = getattr(self, '_pos_hover_item', None)
                if tree is getattr(self, 'positions_tree', None) and iid == current_hover:
                    tree.item(iid, tags=('hover',))
                else:
                    tree.item(iid, tags=(tag,))
            except Exception:
                pass
        # Update heading arrows
        cols = tree['columns']
        for c in cols:
            label = c
            if c == col:
                label += ' ' + ('▲' if asc else '▼')
            tree.heading(c, text=label, command=lambda cc=c, t=tree: self._treeview_sort_by(t, cc))
        self._tree_sort_state[key] = {'col': col, 'asc': asc}

    def _update_banner_bg(self, mood_color: str):
        bg = '#0a0a0a'
        arrow_fg = '#9ca3af'
        if mood_color == 'green':
            bg = '#0b1f16'
            arrow_fg = '#34d399'
        elif mood_color == 'red':
            bg = '#1f0b0b'
            arrow_fg = '#f87171'
        # Update frame and inner backgrounds
        self.status_banner.config(bg=bg)
        self._banner_inner.config(bg=bg)
        if hasattr(self, '_banner_center'):
            self._banner_center.config(bg=bg)
        self.left_arrow.config(bg=bg, fg=arrow_fg)
        self.right_arrow.config(bg=bg, fg=arrow_fg)
        if hasattr(self, 'logo_label'):
            self.logo_label.config(bg=bg)
    
    def set_market_status(self, text, color):
        # Update banner background and arrows
        self._update_banner_bg(color)
        arrows = '↔ ↔ ↔'
        if color == 'green':
            arrows = '▲ ▲ ▲'
            self.market_status_label.config(bg='#22c55e', fg='#111827')
        elif color == 'red':
            arrows = '▼ ▼ ▼'
            self.market_status_label.config(bg='#ef4444', fg='#ffffff')
        else:
            self.market_status_label.config(bg='#374151', fg='#e5e7eb')
        self.left_arrow.config(text=arrows)
        self.right_arrow.config(text=arrows)
        self.market_status_label.config(text=text)
        self.save_settings_file()
    
    def set_symbol_status(self, text, color):
        if color == 'green':
            self.symbol_status_label.config(bg='#22c55e', fg='#111827')
        elif color == 'red':
            self.symbol_status_label.config(bg='#ef4444', fg='#ffffff')
        else:
            self.symbol_status_label.config(bg='#374151', fg='#e5e7eb')
        self.symbol_status_label.config(text=text)
        self.save_settings_file()
    
    def get_base_symbol_from_binance(self, symbol):
        # BTCUSDT -> BTC, ETHUSDT -> ETH, etc.
        bases = ["USDT", "BUSD", "USD", "TUSD", "USDC"]
        for b in bases:
            if symbol.endswith(b):
                return symbol[:-len(b)]
        return symbol
    
    def update_symbol_status_once(self):
        try:
            changes = self.fetch_binance_futures_24h_changes()
            base = self.get_base_symbol_from_binance(self.current_symbol)
            sym = base + 'USDT'
            if changes and sym in changes:
                cur = changes[sym]
                if self.prev_symbol_change is not None:
                    if cur > self.prev_symbol_change:
                        self.set_symbol_status(f"{base} {self.tr('symbol_up_suffix')}", 'green')
                    elif cur < self.prev_symbol_change:
                        self.set_symbol_status(f"{base} {self.tr('symbol_down_suffix')}", 'red')
                    else:
                        self.set_symbol_status(f"{base} {self.tr('symbol_neutral_suffix')}", '#444444')
                self.prev_symbol_change = cur
        except Exception as e:
            self.log_message(f"Sembol durumu güncelleme hatası: {e}")
    
    def on_env_change(self, event=None):
        self.save_settings_file()

    def on_language_change(self, event=None):
        # lang string like 'tr - Turkish'
        try:
            sel = self.lang_var.get().split(' - ')[0]
            if sel:
                self.lang_var.set(sel)
        except Exception:
            pass
        self.apply_language()
        self.save_settings_file()
    
    def on_interval_change(self, event=None):
        # sadece doğrulama ve kayıt
        try:
            val = int(self.market_interval_var.get())
            if val < 5:
                val = 5
                self.market_interval_var.set("5")
            self.market_interval_seconds = val
        except Exception:
            self.market_interval_var.set("60")
            self.market_interval_seconds = 60
        self.save_settings_file()

    def on_leverage_change(self, event=None):
        try:
            lev = int(self.leverage_var.get())
        except Exception:
            lev = 1
        if not self.license_valid and lev > 3:
            self.leverage_var.set("3")
            self.warn_license_required()
            return
        self.save_settings_file()
    
    def on_target_change(self, event=None):
        # hedef pnl, neutral close ve auto percent değiştiğinde kaydet
        try:
            float(self.target_pnl_var.get())
        except Exception:
            self.target_pnl_var.set("0")
        try:
            v = float(self.neutral_close_pct_var.get())
            if v < 0:
                self.neutral_close_pct_var.set("2")
        except Exception:
            self.neutral_close_pct_var.set("2")
        try:
            p = float(self.auto_percent_var.get())
            if p < 0:
                self.auto_percent_var.set("0")
        except Exception:
            self.auto_percent_var.set("0")
        self.save_settings_file()
    
    def load_settings_file(self):
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if '=' in line:
                            k, v = line.strip().split('=', 1)
                            if k == 'env':
                                self.env_var.set(v)
                            elif k == 'mode':
                                self.trading_mode_var.set(v)
                            elif k == 'interval':
                                self.market_interval_var.set(v)
                            elif k == 'symbol':
                                self.symbol_var.set(v)
                            elif k == 'auto_trade':
                                # Ayarlarda aktif yazsa bile başlangıçta pasif kalsın
                                self._auto_trade_saved = (v == '1')
                            elif k == 'target_pnl':
                                self.target_pnl_var.set(v)
                            elif k == 'neutral_close_pct':
                                self.neutral_close_pct_var.set(v)
                            elif k == 'auto_percent':
                                self.auto_percent_var.set(v)
                            elif k == 'lang':
                                self.lang_var.set(v)
                            elif k == 'license':
                                self.license_var.set(v)
            # Lisans otomatik etkinleştir (varsa)
            try:
                if (self.license_var.get() or '').strip():
                    self.activate_license()
            except Exception:
                pass
            # Başlangıçta oto trade DAİMA kapalı
            self.auto_trade_enabled = False
            # UI yansıtma
            try:
                self.auto_btn.config(style='AutoOff.TButton')
                self.auto_status_label.config(text=self.tr('auto_off'))
            except Exception:
                pass
            self.apply_language()
            self.update_idletasks_safe()
        except Exception as e:
            self.log_message(f"Ayarlar yüklenemedi: {e}")
    
    def save_settings_file(self):
        try:
            settings = {
                'env': self.env_var.get(),
                'mode': self.trading_mode_var.get(),
                'interval': self.market_interval_var.get(),
                'symbol': self.symbol_var.get(),
                'auto_trade': '1' if self.auto_trade_enabled else '0',
                'target_pnl': self.target_pnl_var.get(),
                'neutral_close_pct': self.neutral_close_pct_var.get(),
                'auto_percent': self.auto_percent_var.get(),
                'position_size': self.position_size_var.get(),
                'leverage': self.leverage_var.get(),
                'market_status': self.market_status_label.cget('text'),
                'symbol_status': self.symbol_status_label.cget('text'),
                'lang': self.lang_var.get(),
                'license': self.license_var.get()
            }
            # değişiklik yoksa yazma
            if settings == self.last_saved_settings:
                return
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                for k, v in settings.items():
                    f.write(f"{k}={v}\n")
            self.last_saved_settings = settings
        except Exception as e:
            self.log_message(f"Ayarlar kaydedilemedi: {e}")
    
    def manual_save_settings(self):
        self.save_settings_file()
        messagebox.showinfo("Bilgi", "Ayarlar kaydedildi.")

    def open_license_site(self):
        try:
            import webbrowser
            webbrowser.open('https://lisans.planc.space')
        except Exception:
            pass

    def get_machine_id(self) -> str:
        try:
            # Prefer Windows MachineGuid
            import sys
            if sys.platform.startswith('win'):
                try:
                    import winreg
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Cryptography") as k:
                        v, _ = winreg.QueryValueEx(k, "MachineGuid")
                        if v:
                            return str(v)
                except Exception:
                    pass
            # Fallback to MAC-based UUID
            import uuid
            mac = uuid.getnode()
            return f"MAC-{mac:012x}"
        except Exception:
            return "UNKNOWN"

    def validate_license(self, token: str) -> bool:
        try:
            token = (token or '').strip()
            tl = token.lower()
            # Özel kural: sadece 'planc.space' ile başlayan anahtarlar kabul edilir
            if not tl.startswith('planc.space'):
                return False
            # 'planc.space' önekinden sonra bir '.' varsa kalan kısım Ed25519 imzası olarak doğrulanır
            # Örn: planc.space.<payload>.<sig>
            rest = token[len('planc.space'):].lstrip()
            # Eğer Ed25519 parçası yoksa (örn. planc.space4 gibi), yine de lisansı etkin say
            if rest and rest.startswith('.') and verify_license and PUBLIC_KEY_B64:
                signed = rest[1:]
                ok, payload_or_err = verify_license(signed, PUBLIC_KEY_B64)
                if not ok:
                    # İmza geçersizse yine de önek kuralına göre etkinleştir (isteminiz doğrultusunda)
                    self.log_message(f"Uyarı: İmza geçersiz ({payload_or_err}), önek kuralıyla etkinleştirildi")
                    self.license_info = {'issuer': 'planc.space', 'note': 'prefix-only'}
                    return True
                payload = payload_or_err
                # payload controls: machine and expiry
                mid = payload.get('machine')
                exp = float(payload.get('exp', 0))
                now_ts = time.time()
                if mid and mid != self.get_machine_id():
                    self.log_message("Lisans makine eşleşmedi")
                    return False
                if exp and now_ts > exp:
                    self.log_message("Lisans süresi dolmuş")
                    return False
                self.license_info = payload
                return True
            else:
                # Ed25519 bölümü yok; yalnızca önek ile etkinleştir
                self.license_info = {'issuer': 'planc.space', 'note': 'prefix-only'}
                return True
        except Exception as e:
            self.log_message(f"Lisans doğrulama hatası: {e}")
            return False

    def activate_license(self):
        key = self.license_var.get()
        self.license_valid = self.validate_license(key)
        if self.license_valid:
            self.license_status_lbl.config(text="Durum: Lisans Aktif", foreground="#10b981")
            try:
                if hasattr(self, 'activate_btn'):
                    self.activate_btn.config(text=f"✔ {self.tr('license_active_btn')}")
            except Exception:
                pass
            self.save_settings_file()
        else:
            self.license_status_lbl.config(text="Durum: Geçersiz Lisans", foreground="#f87171")
            try:
                if hasattr(self, 'activate_btn'):
                    self.activate_btn.config(text=f"✔ {self.tr('activate')}")
            except Exception:
                pass

    def warn_license_required(self):
        msg = f"{self.tr('license_required')}\n{self.tr('click_to_buy')}"
        res = messagebox.showwarning(self.tr('license'), msg)
        # Keep a clickable label in license box already

    def tr(self, key):
        lang = self.lang_var.get() or 'en'
        try:
            return get_text(lang, key)
        except Exception:
            return key

    def apply_language(self):
        try:
            # Buttons
            if hasattr(self, 'connect_btn'):
                self.connect_btn.config(text=self.tr('connect'))
            if hasattr(self, 'refresh_list_btn'):
                self.refresh_list_btn.config(text=self.tr('refresh_list'))
            if hasattr(self, 'long_btn'):
                self.long_btn.config(text=self.tr('long'))
            if hasattr(self, 'short_btn'):
                self.short_btn.config(text=self.tr('short'))
            if hasattr(self, 'btn_close_all'):
                self.btn_close_all.config(text=self.tr('close_all'))
            if hasattr(self, 'close_selected_btn'):
                self.close_selected_btn.config(text=self.tr('close_selected'))
            if hasattr(self, 'auto_btn'):
                self.auto_btn.config(text=self.tr('auto_trade'))
            if hasattr(self, 'save_settings_btn'):
                self.save_settings_btn.config(text=self.tr('save_settings'))
            if hasattr(self, 'refresh_btn'):
                self.refresh_btn.config(text=self.tr('refresh'))
            if hasattr(self, 'activate_btn'):
                self.activate_btn.config(text=(f"✔ {self.tr('license_active_btn')}" if self.license_valid else f"✔ {self.tr('activate')}"))
            # Frames titles
            if hasattr(self, 'chart_frame'):
                self.chart_frame.configure(text=f"📈 {self.tr('pnl_panel')}")
            # Status strings will be translated on next update via tr() usage
            # Left-pane labels
            if hasattr(self, 'env_label_lbl'):
                self.env_label_lbl.config(text=f"🌐 {self.tr('env_label')}")
            if hasattr(self, 'api_key_lbl'):
                self.api_key_lbl.config(text=f"🗝️ {self.tr('api_key')}")
            if hasattr(self, 'api_secret_lbl'):
                self.api_secret_lbl.config(text=f"🔒 {self.tr('api_secret')}")
            if hasattr(self, 'auto_status_label'):
                self.auto_status_label.config(text=self.tr('auto_on') if self.auto_trade_enabled else self.tr('auto_off'))
            if hasattr(self, 'lev_lbl'):
                self.lev_lbl.config(text=f"📈 {self.tr('leverage_label')}")
            if hasattr(self, 'trading_mode_lbl'):
                self.trading_mode_lbl.config(text=f"⚙️ {self.tr('trading_mode')}")
            if hasattr(self, 'pos_size_lbl'):
                self.pos_size_lbl.config(text=f"💵 {self.tr('position_size_usdt')}")
            if hasattr(self, 'market_int_lbl'):
                self.market_int_lbl.config(text=f"⏱️ {self.tr('market_interval_sec')}")
            if hasattr(self, 'target_lbl'):
                self.target_lbl.config(text=f"🎯 {self.tr('target_pnl')}")
            if hasattr(self, 'neutral_lbl'):
                self.neutral_lbl.config(text=f"⛔ {self.tr('neutral_close_pct_label')}")
            if hasattr(self, 'auto_bal_lbl'):
                self.auto_bal_lbl.config(text=f"💰 {self.tr('auto_balance_pct')}")
            if hasattr(self, 'summary_frame'):
                self.summary_frame.configure(text=f"📊 {self.tr('summary')}")
            if hasattr(self, 'positions_frame'):
                self.positions_frame.configure(text=f"📂 {self.tr('positions')}")
            if hasattr(self, 'history_frame'):
                self.history_frame.configure(text=f"📜 {self.tr('history')}")
            if hasattr(self, 'log_frame'):
                self.log_frame.configure(text=f"🧾 {self.tr('log')}")
        except Exception:
            pass
    
    def update_idletasks_safe(self):
        try:
            self.root.update_idletasks()
        except Exception:
            pass
    
    def close_all_positions(self):
        if not self.client:
            messagebox.showerror("Hata", "Önce API'ye bağlanın!")
            return
        
        try:
            positions = self.client.futures_position_information()
            closed_count = 0
            
            for pos in positions:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    symbol = pos['symbol']
                    side = "SELL" if position_amt > 0 else "BUY"
                    quantity = abs(position_amt)
                    
                    # Close position
                    self.client.futures_create_order(
                        symbol=symbol,
                        side=side,
                        type="MARKET",
                        quantity=quantity
                    )
                    closed_count += 1
                    self.log_message(f"Pozisyon kapatıldı: {symbol}")
            
            if closed_count > 0:
                messagebox.showinfo("Başarılı", f"{closed_count} pozisyon kapatıldı!")
            else:
                messagebox.showinfo("Bilgi", "Kapatılacak pozisyon yok.")
                
        except Exception as e:
            error_msg = f"Pozisyon kapatma hatası: {str(e)}"
            messagebox.showerror("Hata", error_msg)
            self.log_message(error_msg)
    
    def on_closing(self):
        self.price_thread_running = False
        self.stop_market_monitor()
        if self.price_thread:
            self.price_thread.join(timeout=1)
        if self.market_thread:
            self.market_thread.join(timeout=1)
        self.root.destroy()

def main():
    root = tk.Tk()
    app = BinanceFuturesBot(root)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()