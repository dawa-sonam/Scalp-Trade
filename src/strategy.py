import numpy as np
import pandas as pd
import talib
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

@dataclass
class TradeSignal:
    timestamp: pd.Timestamp
    symbol: str
    direction: str  # 'LONG' or 'SHORT'
    confidence: float
    price: float
    stop_loss: float
    take_profit: float

class ScalpStrategy:
    def __init__(
        self,
        bb_period: int = 10,  # Shorter period for Bollinger Bands
        bb_std: float = 1.5,  # Less deviation for tighter bands
        rsi_period: int = 7,  # Shorter period for RSI
        rsi_oversold: float = 40.0,  # More relaxed oversold level
        rsi_overbought: float = 60.0,  # More relaxed overbought level
        min_volatility: float = 0.0001,  # Lower minimum volatility requirement
        max_holding_time: int = 30  # minutes
    ):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.min_volatility = min_volatility
        self.max_holding_time = max_holding_time
        self.logger = logging.getLogger(__name__)
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for the strategy."""
        # Make a copy of the DataFrame to avoid SettingWithCopyWarning
        df = df.copy()
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'],
            timeperiod=self.bb_period,
            nbdevup=self.bb_std,
            nbdevdn=self.bb_std
        )
        
        # RSI
        df['rsi'] = talib.RSI(df['close'], timeperiod=self.rsi_period)
        
        # Volatility (standard deviation of returns)
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=self.bb_period).std()
        
        self.logger.info(f"Calculated indicators for {len(df)} data points")
        self.logger.info(f"Latest RSI: {df['rsi'].iloc[-1]:.2f}")
        self.logger.info(f"Latest volatility: {df['volatility'].iloc[-1]:.6f}")
        self.logger.info(f"BB width: {(df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1]) / df['bb_middle'].iloc[-1]:.4f}")
        
        return df
    
    def is_bb_squeeze(self, df: pd.DataFrame) -> bool:
        """Detect Bollinger Band squeeze."""
        if len(df) < self.bb_period:
            return False
            
        bb_width = (df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1]) / df['bb_middle'].iloc[-1]
        avg_bb_width = (df['bb_upper'].rolling(window=self.bb_period).mean() - 
                       df['bb_lower'].rolling(window=self.bb_period).mean()) / df['bb_middle'].rolling(window=self.bb_period).mean()
        
        # Consider it a squeeze if the current width is less than 98% of the average width
        is_squeeze = bb_width < avg_bb_width.iloc[-1] * 0.98
        self.logger.info(f"BB squeeze check: {is_squeeze} (current: {bb_width:.4f}, avg: {avg_bb_width.iloc[-1]:.4f})")
        return is_squeeze
    
    def generate_signals(self, df: pd.DataFrame) -> Optional[TradeSignal]:
        """Generate trading signals based on strategy rules."""
        if len(df) < self.bb_period:
            self.logger.info(f"Not enough data points: {len(df)} < {self.bb_period}")
            return None
            
        df = self.calculate_indicators(df)
        
        # Check for valid volatility
        current_volatility = df['volatility'].iloc[-1]
        if current_volatility < self.min_volatility:
            self.logger.info(f"Volatility too low: {current_volatility:.6f} < {self.min_volatility:.6f}")
            return None
            
        # Check for Bollinger Band squeeze
        if not self.is_bb_squeeze(df):
            self.logger.info("No Bollinger Band squeeze detected")
            return None
            
        current_price = df['close'].iloc[-1]
        current_rsi = df['rsi'].iloc[-1]
        
        self.logger.info(f"Current price: {current_price:.2f}")
        self.logger.info(f"Current RSI: {current_rsi:.2f}")
        self.logger.info(f"BB Upper: {df['bb_upper'].iloc[-1]:.2f}")
        self.logger.info(f"BB Lower: {df['bb_lower'].iloc[-1]:.2f}")
        
        # Generate long signal
        if current_rsi < self.rsi_oversold:
            stop_loss = current_price * 0.995  # 0.5% stop loss
            take_profit = current_price * 1.01  # 1% take profit
            self.logger.info("Generated LONG signal")
            return TradeSignal(
                timestamp=df.index[-1],
                symbol='SPY',
                direction='LONG',
                confidence=0.8,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
        # Generate short signal
        elif current_rsi > self.rsi_overbought:
            stop_loss = current_price * 1.005  # 0.5% stop loss
            take_profit = current_price * 0.99  # 1% take profit
            self.logger.info("Generated SHORT signal")
            return TradeSignal(
                timestamp=df.index[-1],
                symbol='SPY',
                direction='SHORT',
                confidence=0.8,
                price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
        return None 