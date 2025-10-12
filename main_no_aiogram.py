# Alternative Bot Solution - Without Aiogram

import os
import asyncio
import logging
import requests
import datetime
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask
from threading import Thread
import matplotlib
import json
matplotlib.use('Agg')  # Non-interactive backend

# Configure logging for Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Render'da file handler yerine stream handler kullan
    ]
)
logger = logging.getLogger(__name__)

# Flask server
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Crypto Signal Bot Active - Use /signal command"

@app.route('/health')
def health():
    return {"status": "healthy", "service": "memex-signal-bot"}, 200

@app.route('/_ah/health')
def health_check():
    return 'OK', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates"""
    try:
        update = request.get_json()
        if update:
            process_message(update)
        return 'OK'
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return 'ERROR', 500


# Config loading
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    logger.error("Missing TELEGRAM_TOKEN or GEMINI_API_KEY")
    raise Exception("Missing tokens in .env file!")

# Telegram Bot API functions
def send_message(chat_id, text, reply_markup=None):
    """Send message to Telegram chat"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        logger.info(f"Message sent to chat {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return False

def send_photo(chat_id, photo_path, caption=None, reply_markup=None):
    """Send photo to Telegram chat"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    try:
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': chat_id}
            if caption:
                data['caption'] = caption
                data['parse_mode'] = 'Markdown'
            if reply_markup:
                data['reply_markup'] = reply_markup
            
            response = requests.post(url, files=files, data=data, timeout=30)
            response.raise_for_status()
            logger.info(f"Photo sent to chat {chat_id}")
            return True
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")
        return False

def setup_webhook():
    """Setup webhook for Telegram bot"""
    webhook_url = f"https://memexsinyal.onrender.com/webhook"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
    data = {"url": webhook_url}
    
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("ok"):
            logger.info(f"Webhook set successfully: {webhook_url}")
            return True
        else:
            logger.error(f"Failed to set webhook: {result}")
            return False
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return False

def get_updates(offset=None):
    """Get updates from Telegram Bot API"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset + 1
    
    try:
        response = requests.get(url, params=params, timeout=35)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get updates: {e}")
        return None

# Gemini AI setup
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
    logger.info("Gemini AI initialized")
except Exception as e:
    logger.error(f"Failed to initialize Gemini AI: {e}")

# API endpoints
COINPAPRIKA_API = "https://api.coinpaprika.com/v1"

# Test API connectivity
def test_api_connectivity():
    try:
        response = requests.get(f"{COINPAPRIKA_API}/tickers", timeout=5)
        logger.info(f"CoinPaprika API status: {response.status_code}")
    except Exception as e:
        logger.error(f"CoinPaprika API unreachable: {e}")

# API request with exponential backoff
def make_api_request(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            headers = {'Accept': 'application/json'}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 429:
                logger.error(f"Rate limit exceeded, retry {attempt+1}/{retries}")
                time.sleep(2 ** attempt * 60)  # Exponential backoff
                continue
            if response.status_code != 200:
                logger.error(f"API Error: Status {response.status_code}")
                return None
            return response.json()
        except Exception as e:
            logger.error(f"API Request Error (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt * 5)
    logger.error(f"Failed to fetch data from {url} after {retries} retries")
    return None

# Coin ID cache
coin_cache = {}

# Monitoring system
monitoring_users = {}  # {chat_id: {coin: {frequency: int, last_check: datetime}}}

def get_coin_id(symbol):
    symbol = symbol.lower()
    if symbol in coin_cache:
        logger.info(f"Retrieved {symbol} from cache")
        return coin_cache[symbol]
    logger.info(f"Fetching coin ID for {symbol}")
    data = make_api_request(f"{COINPAPRIKA_API}/coins")
    if data:
        for coin in data:
            if coin.get("symbol", "").lower() == symbol:
                coin_cache[symbol] = coin["id"]
                logger.info(f"Cached coin ID for {symbol}: {coin['id']}")
                return coin["id"]
    logger.error(f"Coin {symbol} not found")
    return None

def get_price_history(coin_id, timeframe="15m"):
    logger.info(f"Fetching price history for {coin_id}, timeframe: {timeframe}")
    data = make_api_request(f"{COINPAPRIKA_API}/tickers/{coin_id}")
    if not data or not data.get("quotes", {}).get("USD"):
        logger.error(f"No price data for {coin_id}")
        return None, None
    
    quotes = data["quotes"]["USD"]
    current_price = quotes.get("price")
    if not current_price:
        logger.error(f"No price available for {coin_id}")
        return None, None
    
    now = datetime.datetime.now()
    prices = []
    
    timeframe_configs = {
        "15m": [
            (900, quotes.get("percent_change_1h", 0)/4),
            (1800, quotes.get("percent_change_1h", 0)/3),
            (2700, quotes.get("percent_change_1h", 0)/2),
            (3600, quotes.get("percent_change_1h", 0)),
            (5400, quotes.get("percent_change_1h", 0)*1.5),
            (7200, quotes.get("percent_change_1h", 0)*2)
        ],
        "24h": [
            (3600*4, quotes.get("percent_change_24h", 0)/6),
            (3600*8, quotes.get("percent_change_24h", 0)/3),
            (3600*12, quotes.get("percent_change_24h", 0)/2),
            (3600*16, quotes.get("percent_change_24h", 0)*0.75),
            (3600*20, quotes.get("percent_change_24h", 0)*0.9),
            (3600*24, quotes.get("percent_change_24h", 0))
        ],
        "48h": [
            (3600*8, quotes.get("percent_change_24h", 0)),
            (3600*16, quotes.get("percent_change_24h", 0)*1.2),
            (3600*24, quotes.get("percent_change_24h", 0)*1.5),
            (3600*32, quotes.get("percent_change_24h", 0)*1.8),
            (3600*40, quotes.get("percent_change_24h", 0)*2),
            (3600*48, quotes.get("percent_change_24h", 0)*2.5)
        ]
    }
    
    changes = timeframe_configs.get(timeframe, timeframe_configs["15m"])
    
    for seconds, change in changes:
        timestamp = int((now - datetime.timedelta(seconds=seconds)).timestamp() * 1000)
        price = current_price / (1 + change/100)
        prices.append([timestamp, price])
    
    prices.append([int(now.timestamp() * 1000), current_price])
    prices.sort(key=lambda x: x[0])
    
    if not prices or prices[-1][1] <= 0:
        logger.error(f"Invalid price data for {coin_id}")
        return None, None
    
    logger.info(f"Generated {len(prices)} price points")
    return prices, quotes

def get_market_trend():
    logger.info("Fetching market trend")
    data = make_api_request(f"{COINPAPRIKA_API}/tickers")
    if not data:
        logger.error("No market trend data")
        return "Unknown"
    
    coins = data[:100]
    up = sum(1 for c in coins if c.get("quotes", {}).get("USD", {}).get("percent_change_1h", 0) > 0)
    down = sum(1 for c in coins if c.get("quotes", {}).get("USD", {}).get("percent_change_1h", 0) < 0)
    
    trend = "Long" if up > down else "Short" if down > up else "Neutral"
    logger.info(f"Market trend: {trend}")
    return trend

def calculate_signal(prices):
    if not prices or len(prices) < 2:
        logger.error("Insufficient price data for signal")
        return None
    
    current = prices[-1][1]
    changes = [prices[i+1][1] - prices[i][1] for i in range(len(prices)-1)]
    
    if not changes:
        logger.error("No price changes")
        return None
    
    volatility = max(sum(abs(c) for c in changes) / len(changes) * 2, current * 0.005)
    trend = "LONG" if (prices[-1][1] - prices[0][1]) >= 0 else "SHORT"
    
    if trend == "LONG":
        entry = current
        target = entry + volatility * 1.5
        stop = entry - volatility
    else:
        entry = current
        target = entry - volatility * 1.5
        stop = entry + volatility
    
    decimals = (2 if current > 1000 else 3 if current > 100 else 4 if current > 10 
               else 6 if current > 1 else 8 if current > 0.1 else 10 if current > 0.001 else 12)
    
    signal = {
        "type": trend,
        "entry": round(entry, decimals),
        "target": round(target, decimals),
        "stop": round(stop, decimals),
        "decimals": decimals
    }
    logger.info(f"Calculated signal: {signal}")
    return signal

def generate_chart(prices, symbol, signal=None):
    logger.info(f"Generating chart for {symbol}")
    filename = f"{symbol}_chart.png"
    
    try:
        plt.figure(figsize=(10, 5), facecolor='white')
        ax = plt.axes()
        ax.set_facecolor('white')
        
        times = [datetime.datetime.fromtimestamp(p[0]/1000) for p in prices]
        values = [p[1] for p in prices]
        
        ohlc = []
        for i in range(len(prices)-1):
            open_price = values[i]
            close_price = values[i+1]
            high_price = max(open_price, close_price) * 1.001
            low_price = min(open_price, close_price) * 0.999
            ohlc.append([times[i], open_price, high_price, low_price, close_price])
        
        for candle in ohlc:
            t, o, h, l, c = candle
            color = '#00ff00' if c >= o else '#ff0000'
            plt.plot([t, t], [o, c], color=color, linewidth=8)
            plt.plot([t, t], [l, h], color=color, linewidth=1)
        
        if signal:
            colors = {'LONG': '#00ff00', 'SHORT': '#ff0000'}
            plt.axhline(signal['entry'], color=colors[signal['type']], linestyle='-', label='Entry')
            plt.axhline(signal['target'], color='#00ff00', linestyle='--', label='Target')
            plt.axhline(signal['stop'], color='#ff0000', linestyle='--', label='Stop')
        
        plt.title(f"{symbol.upper()} Price Chart", color='black')
        plt.xlabel("Time", color='black')
        plt.ylabel("Price (USD)", color='black')
        plt.legend()
        plt.grid(color='#cccccc')
        
        plt.savefig(filename, bbox_inches='tight')
        plt.close()
        logger.info(f"Chart saved as {filename}")
        return filename
    except Exception as e:
        logger.error(f"Chart generation failed for {symbol}: {e}")
        return None

# Inline button
def get_bonus_button():
    keyboard = {
        "inline_keyboard": [[
            {
                "text": "🎁 Free 160 USDT Futures Bonus",
                "url": "https://www.kcex.io/?inviteCode=T13UUV"
            }
        ]]
    }
    return json.dumps(keyboard)

def handle_start_command(chat_id):
    message = """
📈 **Welcome to Crypto Signal Bot!**

**Available Commands:**
• `/start` - Show this help message
• `/signal <coin> [timeframe]` - Get a trading signal
• `/monitor <coin> [minutes]` - Start monitoring (default: 5 min)
• `/stop_monitor <coin>` - Stop monitoring

**Timeframes:** 15m, 24h, 48h
**Monitoring:** 1-60 minutes (default: 5)

**Examples:**
• `/signal btc`
• `/signal eth 24h`
• `/monitor ada 10` (every 10 minutes)
• `/monitor btc` (every 5 minutes)
• `/stop_monitor ada`

Get started with /signal or /monitor! 🚀
"""
    send_message(chat_id, message)

def handle_monitor_command(chat_id, text):
    """Handle /monitor command"""
    logger.info(f"Received /monitor: {text}")
    try:
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, "❌ Usage: /monitor <coin> [minutes]\n"
                                  "📝 Example: /monitor btc 10 (every 10 minutes)")
            return
        
        symbol = parts[1].lower()
        
        # Parse minutes parameter
        minutes = 5  # default
        if len(parts) > 2:
            try:
                minutes = int(parts[2])
                if minutes < 1 or minutes > 60:
                    send_message(chat_id, "❌ Minutes must be between 1-60")
                    return
            except ValueError:
                send_message(chat_id, "❌ Invalid minutes format. Use numbers only.")
                return
        
        # Check if coin exists
        coin_id = get_coin_id(symbol)
        if not coin_id:
            send_message(chat_id, f"❌ Coin {symbol.upper()} not found")
            return
        
        # Initialize monitoring for this user if not exists
        if chat_id not in monitoring_users:
            monitoring_users[chat_id] = {}
        
        # Add coin to monitoring
        monitoring_users[chat_id][symbol] = {
            'frequency': minutes * 60,  # convert to seconds
            'last_check': datetime.datetime.now(),
            'coin_id': coin_id
        }
        
        send_message(chat_id, f"✅ Started monitoring {symbol.upper()}\n"
                              f"📊 Checking every {minutes} minutes\n"
                              f"🛑 Use /stop_monitor {symbol} to stop")
        logger.info(f"Started monitoring {symbol} for chat {chat_id} (every {minutes} minutes)")
        
    except Exception as e:
        logger.error(f"Error in /monitor: {e}")
        send_message(chat_id, "❌ An unexpected error occurred")

def handle_stop_monitor_command(chat_id, text):
    """Handle /stop_monitor command"""
    logger.info(f"Received /stop_monitor: {text}")
    try:
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, "❌ Usage: /stop_monitor <coin>")
            return
        
        symbol = parts[1].lower()
        
        if chat_id not in monitoring_users:
            send_message(chat_id, f"❌ No monitoring active for {symbol.upper()}")
            return
        
        if symbol not in monitoring_users[chat_id]:
            send_message(chat_id, f"❌ {symbol.upper()} is not being monitored")
            return
        
        # Remove from monitoring
        del monitoring_users[chat_id][symbol]
        
        # Clean up empty user entry
        if not monitoring_users[chat_id]:
            del monitoring_users[chat_id]
        
        send_message(chat_id, f"🛑 Stopped monitoring {symbol.upper()}")
        logger.info(f"Stopped monitoring {symbol} for chat {chat_id}")
        
    except Exception as e:
        logger.error(f"Error in /stop_monitor: {e}")
        send_message(chat_id, "❌ An unexpected error occurred")

def check_monitoring():
    """Check all monitored coins and send signals if needed"""
    try:
        current_time = datetime.datetime.now()
        
        for chat_id, coins in monitoring_users.items():
            for symbol, data in coins.items():
                last_check = data['last_check']
                frequency = data['frequency']
                
                # Check if enough time has passed
                if (current_time - last_check).total_seconds() >= frequency:
                    logger.info(f"Checking monitoring for {symbol} (chat {chat_id})")
                    
                    # Get fresh signal
                    coin_id = data['coin_id']
                    prices, quotes = get_price_history(coin_id, "15m")
                    
                    if prices and quotes:
                        signal = calculate_signal(prices)
                        if signal:
                            # Send signal
                            trend = get_market_trend()
                            trend_icon = "🟢" if trend == "Long" else "🔴" if trend == "Short" else "⚪"
                            
                            is_aligned = (signal['type'] == "LONG" and trend == "Long") or (signal['type'] == "SHORT" and trend == "Short")
                            alignment_msg = "✅ Trade Aligned with Market" if is_aligned else "⚠️ Trade Against Market"
                            alignment_icon = "🟢" if is_aligned else "🔴"
                            
                            current_price = quotes.get("price", 0)
                            volume_24h = quotes.get("volume_24h", 0)
                            change_24h = quotes.get("percent_change_24h", 0)
                            change_arrow = "↑" if change_24h >= 0 else "↓"
                            
                            msg = f"""
🔄 **MONITORING ALERT** | #{symbol.upper()}USDT
💰 Current Price: ${current_price:,.{signal['decimals']}f}
📈 24H Volume: ${volume_24h:,.0f}
📊 24H Change: {change_24h:.2f}% {change_arrow}
{"🟢 LONG" if signal['type'] == 'LONG' else "🔴 SHORT"} Signal
🎯 Entry: ${signal['entry']:,.{signal['decimals']}f}
🎯 Target: ${signal['target']:,.{signal['decimals']}f}
🛑 Stop: ${signal['stop']:,.{signal['decimals']}f}
📊 Market Trend: {trend} {trend_icon}
📈 Trade Alignment: {alignment_msg} {alignment_icon}
⚠️ High Risk - DYOR!
"""
                            
                            chart = generate_chart(prices, symbol, signal)
                            if chart:
                                send_photo(
                                    chat_id=chat_id,
                                    photo_path=chart,
                                    caption=msg,
                                    reply_markup=get_bonus_button()
                                )
                                os.remove(chart)
                            else:
                                send_message(chat_id, msg)
                    
                    # Update last check time
                    monitoring_users[chat_id][symbol]['last_check'] = current_time
                    
    except Exception as e:
        logger.error(f"Error in monitoring check: {e}")

def handle_signal_command(chat_id, text):
    logger.info(f"Received /signal: {text}")
    try:
        parts = text.split()
        if len(parts) < 2:
            logger.warning("Invalid /signal format")
            send_message(chat_id, "❌ Usage: /signal <coin> [timeframe: 15m/24h/48h]")
            return
        
        symbol = parts[1].lower()
        timeframe = parts[2].lower() if len(parts) > 2 else "15m"
        if timeframe not in ["15m", "24h", "48h"]:
            logger.warning(f"Invalid timeframe: {timeframe}")
            send_message(chat_id, "❌ Timeframe must be 15m, 24h, or 48h")
            return
        
        send_message(chat_id, f"🔍 Analyzing {symbol.upper()}...")
        logger.info(f"Analyzing {symbol} with timeframe {timeframe}")
        
        coin_id = get_coin_id(symbol)
        if not coin_id:
            send_message(chat_id, "❌ Coin not found")
            return
        
        prices, quotes = get_price_history(coin_id, timeframe)
        if not prices or not quotes:
            send_message(chat_id, "❌ Price data unavailable")
            return
        
        signal = calculate_signal(prices)
        if not signal:
            send_message(chat_id, "❌ Signal calculation failed")
            return
        
        chart = generate_chart(prices, symbol, signal)
        if not chart:
            send_message(chat_id, "❌ Failed to generate chart")
            return
        
        trend = get_market_trend()
        trend_icon = "🟢" if trend == "Long" else "🔴" if trend == "Short" else "⚪"
        
        is_aligned = (signal['type'] == "LONG" and trend == "Long") or (signal['type'] == "SHORT" and trend == "Short")
        alignment_msg = "✅ Trade Aligned with Market" if is_aligned else "⚠️ Trade Against Market"
        alignment_icon = "🟢" if is_aligned else "🔴"
        
        current_price = quotes.get("price", 0)
        volume_24h = quotes.get("volume_24h", 0)
        change_24h = quotes.get("percent_change_24h", 0)
        change_arrow = "↑" if change_24h >= 0 else "↓"
        
        msg = f"""
⏰ {timeframe.upper()} Timeframe | #{symbol.upper()}USDT
💰 Current Price: ${current_price:,.{signal['decimals']}f}
📈 24H Volume: ${volume_24h:,.0f}
📊 24H Change: {change_24h:.2f}% {change_arrow}
{"🟢 LONG" if signal['type'] == 'LONG' else "🔴 SHORT"} Signal
🎯 Entry: ${signal['entry']:,.{signal['decimals']}f}
🎯 Target: ${signal['target']:,.{signal['decimals']}f}
🛑 Stop: ${signal['stop']:,.{signal['decimals']}f}
📊 Market Trend: {trend} {trend_icon}
📈 Trade Alignment: {alignment_msg} {alignment_icon}
⚠️ High Risk - DYOR!
"""
        send_photo(
            chat_id=chat_id,
            photo_path=chart,
            caption=msg,
            reply_markup=get_bonus_button()
        )
        os.remove(chart)
        logger.info(f"Sent signal for {symbol}")
    except Exception as e:
        logger.error(f"Error in /signal: {e}")
        send_message(chat_id, "❌ An unexpected error occurred")

def process_message(update):
    """Process incoming message"""
    try:
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if not chat_id or not text:
            return
        
        logger.info(f"Processing message from chat {chat_id}: {text}")
        
        if text.startswith("/start"):
            handle_start_command(chat_id)
        elif text.startswith("/signal"):
            handle_signal_command(chat_id, text)
        elif text.startswith("/monitor"):
            handle_monitor_command(chat_id, text)
        elif text.startswith("/stop_monitor"):
            handle_stop_monitor_command(chat_id, text)
        else:
            send_message(chat_id, "❌ Unknown command. Use /start for help.")
            
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def main():
    logger.info("Starting MemeX Signal Bot on Render")
    test_api_connectivity()
    
    # Setup webhook
    if setup_webhook():
        logger.info("Using webhook mode - bot will receive updates via webhook")
    else:
        logger.warning("Failed to setup webhook, falling back to polling")
    
    # Start Flask server (this will handle webhook requests)
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Flask server on port {port}")
    
    try:
        # Start monitoring check in background
        import threading
        def monitoring_loop():
            while True:
                try:
                    check_monitoring()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Monitoring loop error: {e}")
                    time.sleep(60)
        
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        logger.info("Monitoring thread started")
        
        # Start Flask app
        app.run(host='0.0.0.0', port=port, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    import time
    main()
