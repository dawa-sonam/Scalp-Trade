import talib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from src.trading_bot import TradingBot

def test_ta_lib():
    """Test if TA-Lib is working correctly."""
    try:
        # Create sample data with float64 type
        close = np.array([10.0, 12.0, 15.0, 14.0, 13.0, 12.0, 11.0, 10.0, 9.0, 8.0], dtype=np.float64)
        
        # Calculate RSI
        rsi = talib.RSI(close)
        print("TA-Lib RSI test successful!")
        print(f"RSI values: {rsi}")
        return True
    except Exception as e:
        print(f"TA-Lib test failed: {str(e)}")
        return False

def main():
    print("Testing TA-Lib installation...")
    if not test_ta_lib():
        print("Please ensure TA-Lib is properly installed before proceeding.")
        return
    
    print("\nInitializing trading bot...")
    bot = TradingBot(
        symbol='SPY',
        data_source='yfinance',
        paper_trading=True
    )
    
    # Set backtest parameters (60 days in 2023)
    end_date = datetime(2023, 12, 31)
    start_date = datetime(2023, 11, 1)
    
    print(f"\nRunning backtest from {start_date} to {end_date}...")
    results = bot.run_backtest(
        start_date=start_date,
        end_date=end_date,
        timeframe='1d'
    )
    
    print("\nBacktest Results:")
    if results:
        print(f"Total Trades: {results.get('total_trades', 0)}")
        print(f"Winning Trades: {results.get('winning_trades', 0)}")
        print(f"Losing Trades: {results.get('losing_trades', 0)}")
        print(f"Win Rate: {results.get('win_rate', 0):.2%}")
        print(f"Average Win: ${results.get('average_win', 0):.2f}")
        print(f"Average Loss: ${results.get('average_loss', 0):.2f}")
        print(f"Total PnL: ${results.get('total_pnl', 0):.2f}")
        print(f"Max Drawdown: {results.get('max_drawdown', 0):.2%}")
        print(f"Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
    else:
        print("No trades were executed during the backtest period.")

if __name__ == "__main__":
    main() 