from datetime import datetime, timedelta
from src.trading_bot import TradingBot

def main():
    # Initialize trading bot
    bot = TradingBot(
        symbol='SPY',
        data_source='yfinance',  # Use yfinance for backtesting
        paper_trading=True
    )
    
    # Set backtest parameters
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # 30-day backtest
    
    # Run backtest
    results = bot.run_backtest(
        start_date=start_date,
        end_date=end_date,
        timeframe='1m'
    )
    
    # Print results
    print("\nBacktest Results:")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Winning Trades: {results['winning_trades']}")
    print(f"Losing Trades: {results['losing_trades']}")
    print(f"Win Rate: {results['win_rate']:.2%}")
    print(f"Average Win: ${results['average_win']:.2f}")
    print(f"Average Loss: ${results['average_loss']:.2f}")
    print(f"Total PnL: ${results['total_pnl']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")

if __name__ == "__main__":
    main() 