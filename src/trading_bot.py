import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Optional
from .strategy import ScalpStrategy
from .data_handler import DataHandler
from .backtest import BacktestEngine

class TradingBot:
    def __init__(
        self,
        symbol: str = 'SPY',
        data_source: str = 'yfinance',
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        paper_trading: bool = True
    ):
        # Initialize components
        self.data_handler = DataHandler(symbol, data_source, api_key, api_secret)
        self.strategy = ScalpStrategy()
        self.backtest_engine = BacktestEngine(self.strategy)
        
        # Setup logging
        self.setup_logging()
        
        # Trading parameters
        self.paper_trading = paper_trading
        self.current_position = None
        self.last_signal_time = None
        
    def setup_logging(self):
        """Configure logging for the trading bot."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = '1m'
    ) -> dict:
        """Run a backtest on historical data."""
        self.logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Get historical data
        data = self.data_handler.get_historical_data(start_date, end_date, timeframe)
        
        # Run backtest
        results = self.backtest_engine.run(data)
        
        self.logger.info("Backtest completed")
        self.logger.info(f"Results: {results}")
        
        return results
    
    def run_live(self):
        """Run the trading bot in live mode."""
        self.logger.info("Starting live trading bot")
        
        while True:
            try:
                # Get latest data
                data = self.data_handler.get_latest_data(lookback=100)
                
                # Check for exit conditions if in position
                if self.current_position:
                    if self._should_exit_position(data):
                        self._close_position(data)
                
                # Generate new signals if not in position
                if not self.current_position:
                    signal = self.strategy.generate_signals(data)
                    if signal and self._is_valid_signal(signal):
                        self._open_position(signal, data)
                
                # Sleep for a short period before next iteration
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in live trading: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def _should_exit_position(self, data: pd.DataFrame) -> bool:
        """Check if current position should be closed."""
        if not self.current_position:
            return False
            
        current_price = data['close'].iloc[-1]
        
        # Check stop loss
        if self.current_position['direction'] == 'LONG' and current_price <= self.current_position['stop_loss']:
            self.logger.info("Stop loss triggered for long position")
            return True
        elif self.current_position['direction'] == 'SHORT' and current_price >= self.current_position['stop_loss']:
            self.logger.info("Stop loss triggered for short position")
            return True
            
        # Check take profit
        if self.current_position['direction'] == 'LONG' and current_price >= self.current_position['take_profit']:
            self.logger.info("Take profit triggered for long position")
            return True
        elif self.current_position['direction'] == 'SHORT' and current_price <= self.current_position['take_profit']:
            self.logger.info("Take profit triggered for short position")
            return True
            
        # Check max holding time
        holding_time = datetime.now() - self.current_position['entry_time']
        if holding_time >= timedelta(minutes=self.strategy.max_holding_time):
            self.logger.info("Max holding time reached")
            return True
            
        return False
    
    def _is_valid_signal(self, signal) -> bool:
        """Check if a trading signal is valid."""
        # Prevent rapid re-entry
        if self.last_signal_time and (datetime.now() - self.last_signal_time) < timedelta(minutes=5):
            return False
            
        # Additional validation logic can be added here
        return True
    
    def _open_position(self, signal, data: pd.DataFrame):
        """Open a new trading position."""
        if self.paper_trading:
            self.logger.info(f"Paper trading: Opening {signal.direction} position at {signal.price}")
        else:
            self.logger.info(f"Live trading: Opening {signal.direction} position at {signal.price}")
            # Implement actual order execution here
        
        self.current_position = {
            'entry_time': datetime.now(),
            'direction': signal.direction,
            'entry_price': signal.price,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'size': 1  # Adjust based on position sizing logic
        }
        
        self.last_signal_time = datetime.now()
    
    def _close_position(self, data: pd.DataFrame):
        """Close the current trading position."""
        if not self.current_position:
            return
            
        current_price = data['close'].iloc[-1]
        pnl = (current_price - self.current_position['entry_price']) * self.current_position['size']
        if self.current_position['direction'] == 'SHORT':
            pnl = -pnl
            
        if self.paper_trading:
            self.logger.info(f"Paper trading: Closing position at {current_price}, PnL: {pnl}")
        else:
            self.logger.info(f"Live trading: Closing position at {current_price}, PnL: {pnl}")
            # Implement actual order execution here
        
        self.current_position = None 