import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import pickle

class DataLoader:
    """Class to handle data loading and preprocessing for trading analysis"""
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        self.cache_dir = 'data_cache'
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
    def get_cache_filename(self, symbol, start_date, end_date, timeframe):
        """Generate a unique cache filename based on parameters"""
        return os.path.join(
            self.cache_dir,
            f"{symbol.replace('/', '_')}_{start_date}_{end_date}_{timeframe}.pkl"
        )
        
    def get_detailed_crypto_data(self, symbol='BTC/USDT', start_date=None, end_date=None, timeframe='5m'):
        """Fetch or load cached cryptocurrency data"""
        
        # Standardize dates
        if isinstance(start_date, str):
            start_date = start_date
        else:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
        if isinstance(end_date, str):
            end_date = end_date
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        cache_file = self.get_cache_filename(symbol, start_date, end_date, timeframe)
        
        # Try to load from cache first
        if os.path.exists(cache_file):
            print(f"Loading cached data from {cache_file}")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
                
        print(f"Fetching new data for {symbol} from {start_date} to {end_date}")
        df = self._fetch_detailed_crypto_data(symbol, start_date, end_date, timeframe)
        
        # Cache the data if fetch was successful
        if df is not None:
            with open(cache_file, 'wb') as f:
                pickle.dump(df, f)
                
        return df
    
    def _fetch_detailed_crypto_data(self, symbol, start_date, end_date, timeframe):
        """Internal method to fetch data from exchange"""
        try:
            # Convert dates to timestamps
            start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
            end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
            
            # Fetch data in chunks due to exchange limits
            all_candles = []
            current_ts = start_ts
            
            while current_ts < end_ts:
                print(f"Fetching data from {datetime.fromtimestamp(current_ts/1000)}")
                candles = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe=timeframe,
                    since=current_ts,
                    limit=1000  # Binance limit
                )
                
                if not candles:
                    break
                    
                all_candles.extend(candles)
                current_ts = candles[-1][0] + 1  # Next timestamp
                time.sleep(self.exchange.rateLimit / 1000)  # Respect rate limits
            
            # Convert to DataFrame with correct column capitalization
            df = pd.DataFrame(
                all_candles,
                columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df.index = df.index.tz_localize('UTC')  # Ensure UTC timezone
            
            # Remove duplicates
            df = df.loc[~df.index.duplicated(keep='first')]
            
            return df
            
        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            return None
            
    def get_crypto_data(self, symbol='BTC/USDT', start_date=None, end_date=None, interval='1h'):
        """Alias for get_detailed_crypto_data with different default interval"""
        return self.get_detailed_crypto_data(symbol, start_date, end_date, interval) 