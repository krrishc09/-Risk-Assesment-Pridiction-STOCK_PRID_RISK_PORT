# data_stream.py
"""
Real-time data streaming service with WebSocket support
Supports multiple brokers: Upstox, Zerodha, Breeze, and yfinance fallback
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Callable, Any, Optional
import yfinance as yf
from threading import Thread
import time

from config_platform import (
    BROKER, REALTIME_UPDATE_INTERVAL, is_market_open,
    MARKET_TIMEZONE, get_broker_config
)
from database import db_manager, StockPrice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== BASE DATA STREAMER ====================

class DataStreamer:
    """Base class for data streaming"""
    
    def __init__(self):
        self.subscribed_symbols: Set[str] = set()
        self.callbacks: List[Callable] = []
        self.is_running = False
        self.price_cache: Dict[str, Dict[str, Any]] = {}
        
    def subscribe(self, symbols: List[str]):
        """Subscribe to symbols for real-time updates"""
        self.subscribed_symbols.update(symbols)
        logger.info(f"Subscribed to symbols: {symbols}")
    
    def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from symbols"""
        self.subscribed_symbols.difference_update(symbols)
        logger.info(f"Unsubscribed from symbols: {symbols}")
    
    def add_callback(self, callback: Callable):
        """Add callback function for price updates"""
        self.callbacks.append(callback)
    
    def notify_callbacks(self, symbol: str, data: Dict[str, Any]):
        """Notify all callbacks with new data"""
        for callback in self.callbacks:
            try:
                callback(symbol, data)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached price for a symbol"""
        return self.price_cache.get(symbol)
    
    def update_cache(self, symbol: str, data: Dict[str, Any]):
        """Update price cache"""
        self.price_cache[symbol] = {
            **data,
            "timestamp": datetime.now(),
            "symbol": symbol
        }
    
    async def start(self):
        """Start streaming (to be implemented by subclasses)"""
        raise NotImplementedError
    
    async def stop(self):
        """Stop streaming"""
        self.is_running = False
        logger.info("Data streaming stopped")


# ==================== YFINANCE STREAMER (FALLBACK) ====================

class YFinanceStreamer(DataStreamer):
    """Real-time data streaming using yfinance (polling-based)"""
    
    def __init__(self, update_interval: int = REALTIME_UPDATE_INTERVAL):
        super().__init__()
        self.update_interval = update_interval
        self.last_prices: Dict[str, float] = {}
    
    async def fetch_prices(self):
        """Fetch current prices for all subscribed symbols"""
        if not self.subscribed_symbols:
            return
        
        try:
            # Create a copy to avoid "Set changed size during iteration" error
            symbols_list = list(self.subscribed_symbols)
            if not symbols_list:
                return
            
            # Fetch data for all symbols at once
            symbols_str = " ".join(symbols_list)
            tickers = yf.Tickers(symbols_str)
            
            for symbol in symbols_list:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    hist = ticker.history(period="2d", interval="1d")
                    
                    if hist.empty:
                        continue
                    
                    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
                    if not current_price and not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                    
                    if current_price:
                        prev_close = info.get("previousClose", current_price)
                        change = current_price - prev_close
                        change_percent = (change / prev_close * 100) if prev_close else 0
                        
                        data = {
                            "symbol": symbol,
                            "ltp": float(current_price),
                            "open": float(info.get("open", current_price)),
                            "high": float(info.get("dayHigh", current_price)),
                            "low": float(info.get("dayLow", current_price)),
                            "close": float(current_price),
                            "volume": float(info.get("volume", 0)),
                            "change": float(change),
                            "change_percent": float(change_percent),
                            "timestamp": datetime.now(),
                        }
                        
                        # Update cache
                        self.update_cache(symbol, data)
                        
                        # Notify callbacks if price changed
                        if symbol not in self.last_prices or self.last_prices[symbol] != current_price:
                            self.last_prices[symbol] = current_price
                            self.notify_callbacks(symbol, data)
                            
                            # Save to database every minute
                            if int(time.time()) % 60 == 0:
                                db_manager.save_stock_price(symbol, data)
                
                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {e}")
        
        except Exception as e:
            logger.error(f"Error in fetch_prices: {e}")
    
    async def start(self):
        """Start streaming prices"""
        self.is_running = True
        logger.info(f"YFinance streamer started (interval: {self.update_interval}s)")
        
        while self.is_running:
            if is_market_open() or True:  # Always fetch for demo purposes
                await self.fetch_prices()
            await asyncio.sleep(self.update_interval)
    
    def start_background(self):
        """Start streaming in background thread"""
        def run():
            asyncio.run(self.start())
        
        thread = Thread(target=run, daemon=True)
        thread.start()
        logger.info("YFinance streamer started in background")


# ==================== UPSTOX STREAMER ====================

class UpstoxStreamer(DataStreamer):
    """Real-time data streaming using Upstox WebSocket API"""
    
    def __init__(self):
        super().__init__()
        self.config = get_broker_config()
        self.ws = None
        self.access_token = None
    
    async def connect(self):
        """Connect to Upstox WebSocket"""
        try:
            # Import upstox client
            from upstox_client import WebSocket
            
            # Initialize WebSocket
            self.ws = WebSocket(self.access_token)
            self.ws.on_message = self.on_message
            self.ws.on_error = self.on_error
            self.ws.on_close = self.on_close
            
            # Connect
            await self.ws.connect()
            logger.info("Connected to Upstox WebSocket")
            
        except ImportError:
            logger.error("Upstox client not installed. Install: pip install upstox-python-sdk")
        except Exception as e:
            logger.error(f"Upstox connection error: {e}")
    
    def on_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            symbol = data.get("symbol")
            
            if symbol in self.subscribed_symbols:
                price_data = {
                    "symbol": symbol,
                    "ltp": data.get("ltp"),
                    "open": data.get("open"),
                    "high": data.get("high"),
                    "low": data.get("low"),
                    "close": data.get("close"),
                    "volume": data.get("volume"),
                    "change_percent": data.get("change_percent"),
                    "timestamp": datetime.now(),
                }
                
                self.update_cache(symbol, price_data)
                self.notify_callbacks(symbol, price_data)
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def on_error(self, error):
        """Handle WebSocket errors"""
        logger.error(f"Upstox WebSocket error: {error}")
    
    def on_close(self):
        """Handle WebSocket close"""
        logger.info("Upstox WebSocket closed")
    
    async def start(self):
        """Start streaming"""
        self.is_running = True
        await self.connect()
        
        # Subscribe to symbols
        if self.ws and self.subscribed_symbols:
            await self.ws.subscribe(list(self.subscribed_symbols))


# ==================== ZERODHA KITE STREAMER ====================

class ZerodhaStreamer(DataStreamer):
    """Real-time data streaming using Zerodha Kite WebSocket API"""
    
    def __init__(self):
        super().__init__()
        self.config = get_broker_config()
        self.kws = None
        self.access_token = None
    
    async def connect(self):
        """Connect to Kite WebSocket"""
        try:
            from kiteconnect import KiteTicker
            
            api_key = self.config.get("api_key")
            self.kws = KiteTicker(api_key, self.access_token)
            
            self.kws.on_ticks = self.on_ticks
            self.kws.on_connect = self.on_connect
            self.kws.on_close = self.on_close
            self.kws.on_error = self.on_error
            
            self.kws.connect(threaded=True)
            logger.info("Connected to Zerodha Kite WebSocket")
            
        except ImportError:
            logger.error("Kite Connect not installed. Install: pip install kiteconnect")
        except Exception as e:
            logger.error(f"Kite connection error: {e}")
    
    def on_ticks(self, ws, ticks):
        """Handle incoming ticks"""
        for tick in ticks:
            symbol = tick.get("instrument_token")  # Convert to symbol
            
            price_data = {
                "symbol": symbol,
                "ltp": tick.get("last_price"),
                "open": tick.get("ohlc", {}).get("open"),
                "high": tick.get("ohlc", {}).get("high"),
                "low": tick.get("ohlc", {}).get("low"),
                "close": tick.get("ohlc", {}).get("close"),
                "volume": tick.get("volume"),
                "change_percent": tick.get("change"),
                "timestamp": datetime.now(),
            }
            
            self.update_cache(symbol, price_data)
            self.notify_callbacks(symbol, price_data)
    
    def on_connect(self, ws, response):
        """Handle connection"""
        logger.info("Kite WebSocket connected")
        # Subscribe to symbols
        if self.subscribed_symbols:
            ws.subscribe(list(self.subscribed_symbols))
            ws.set_mode(ws.MODE_FULL, list(self.subscribed_symbols))
    
    def on_close(self, ws, code, reason):
        """Handle close"""
        logger.info(f"Kite WebSocket closed: {code} - {reason}")
    
    def on_error(self, ws, code, reason):
        """Handle error"""
        logger.error(f"Kite WebSocket error: {code} - {reason}")
    
    async def start(self):
        """Start streaming"""
        self.is_running = True
        await self.connect()


# ==================== STREAMER FACTORY ====================

def create_streamer(broker: str = BROKER) -> DataStreamer:
    """Factory function to create appropriate streamer"""
    streamers = {
        "yfinance": YFinanceStreamer,
        "upstox": UpstoxStreamer,
        "zerodha": ZerodhaStreamer,
    }
    
    streamer_class = streamers.get(broker, YFinanceStreamer)
    logger.info(f"Creating {broker} streamer")
    return streamer_class()


# ==================== GLOBAL STREAMER INSTANCE ====================

# Global streamer instance
streamer = create_streamer()


# ==================== HELPER FUNCTIONS ====================

def subscribe_to_symbols(symbols: List[str]):
    """Subscribe to symbols for real-time updates"""
    streamer.subscribe(symbols)


def get_live_price(symbol: str) -> Optional[Dict[str, Any]]:
    """Get live price for a symbol"""
    return streamer.get_cached_price(symbol)


def start_streaming():
    """Start the data streaming service"""
    if isinstance(streamer, YFinanceStreamer):
        streamer.start_background()
    else:
        asyncio.run(streamer.start())


# ==================== HISTORICAL DATA FETCHER ====================

def fetch_historical_data(symbol: str, period: str = "1y", interval: str = "1d") -> List[Dict[str, Any]]:
    """Fetch historical OHLC data"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return []
        
        data = []
        for index, row in hist.iterrows():
            data.append({
                "symbol": symbol,
                "timestamp": index.to_pydatetime(),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": float(row['Volume']),
                "ltp": float(row['Close']),
            })
        
        return data
    
    except Exception as e:
        logger.error(f"Error fetching historical data for {symbol}: {e}")
        return []


def fetch_and_store_historical_data(symbol: str, period: str = "1y"):
    """Fetch and store historical data in database"""
    try:
        data = fetch_historical_data(symbol, period)
        
        for price_data in data:
            db_manager.save_stock_price(symbol, price_data)
        
        logger.info(f"Stored {len(data)} historical records for {symbol}")
        return len(data)
    
    except Exception as e:
        logger.error(f"Error storing historical data: {e}")
        return 0
