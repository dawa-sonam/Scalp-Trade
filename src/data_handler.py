import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import yfinance as yf
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import logging

class DataHandler:
    def __init__(
        self,
        symbol: str = 'SPY',
        data_source: str = 'yfinance',  # 'yfinance' or 'alpaca'
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        self.symbol = symbol
        self.data_source = data_source
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger(__name__)
        
        if data_source == 'alpaca' and (not api_key or not api_secret):
            raise ValueError("API key and secret required for Alpaca data source")
            
        if data_source == 'alpaca':
            self.client = StockHistoricalDataClient(api_key, api_secret)
    
    def get_historical_data(
        self,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = '1m'
    ) -> pd.DataFrame:
        """Fetch historical price data."""
        if self.data_source == 'yfinance':
            return self._get_yfinance_data(start_date, end_date, timeframe)
        else:
            return self._get_alpaca_data(start_date, end_date, timeframe)
    
    def _get_yfinance_data(
        self,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> pd.DataFrame:
        """Fetch data from Yahoo Finance."""
        ticker = yf.Ticker(self.symbol)
        
        # Convert timeframe to yfinance format
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '1d': '1d'
        }
        
        interval = interval_map.get(timeframe, '1m')
        
        # Check if the date range is too large for the interval
        if interval == '1m' and (end_date - start_date).days > 7:
            self.logger.warning("Date range too large for 1-minute data. Limiting to last 7 days.")
            start_date = end_date - timedelta(days=7)
        elif interval == '5m' and (end_date - start_date).days > 60:
            self.logger.warning("Date range too large for 5-minute data. Limiting to last 60 days.")
            start_date = end_date - timedelta(days=60)
            
        try:
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval
            )
            
            if len(df) == 0:
                self.logger.warning("No data retrieved")
                return pd.DataFrame()
                
            self.logger.info(f"Retrieved {len(df)} rows of data")
            self.logger.info(f"First date: {df.index[0]}")
            self.logger.info(f"Last date: {df.index[-1]}")
            self.logger.info(f"Columns: {df.columns.tolist()}")
            self.logger.info(f"Sample data:\n{df.head()}")
            
            return self._process_dataframe(df)
            
        except Exception as e:
            self.logger.error(f"Error fetching data from Yahoo Finance: {str(e)}")
            return pd.DataFrame()
    
    def _get_alpaca_data(
        self,
        start_date: datetime,
        end_date: datetime,
        timeframe: str
    ) -> pd.DataFrame:
        """Fetch data from Alpaca."""
        # Convert timeframe to Alpaca format
        timeframe_map = {
            '1m': TimeFrame.Minute,
            '5m': TimeFrame.Minute,
            '15m': TimeFrame.Minute,
            '1h': TimeFrame.Hour,
            '1d': TimeFrame.Day
        }
        
        request_params = StockBarsRequest(
            symbol_or_symbols=self.symbol,
            timeframe=timeframe_map[timeframe],
            start=start_date,
            end=end_date
        )
        
        bars = self.client.get_stock_bars(request_params)
        df = bars.df
        
        return self._process_dataframe(df)
    
    def _process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process and clean the dataframe."""
        # Convert column names to lowercase if they exist in uppercase
        column_map = {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        df = df.rename(columns=column_map)
        
        # Ensure required columns exist
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Clean data
        df = df.dropna()
        df = df[df['volume'] > 0]  # Remove zero-volume bars
        
        # Calculate additional features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close']).diff()
        
        return df
    
    def get_latest_data(self, lookback: int = 100) -> pd.DataFrame:
        """Get the most recent data points."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback)
        
        return self.get_historical_data(start_date, end_date, '1m')
    
    def get_intraday_data(self, date: datetime) -> pd.DataFrame:
        """Get intraday data for a specific date."""
        start_date = date.replace(hour=9, minute=30, second=0)
        end_date = date.replace(hour=16, minute=0, second=0)
        
        return self.get_historical_data(start_date, end_date, '1m') 