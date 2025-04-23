# High-Frequency Options Trading Bot

A high-frequency trading bot designed to capitalize on theta decay in short-dated SPX/SPY contracts (0DTE) using Bollinger Bands, RSI, and volatility-based signals.

## Features

- 🔍 Signal Generation: Combines Bollinger Bands, RSI, and volatility filters
- 📊 Backtest Engine: Historical testing with PnL tracking
- 🧠 Modular Strategy Logic: Easy to extend with new indicators
- 🛠️ Live Data Ready: Supports Alpaca and Interactive Brokers
- 📉 Risk-Controlled: Stop-loss and take-profit management
- 📁 Clean Architecture: Well-organized codebase

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/scalp-trade.git
cd scalp-trade
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install TA-Lib:
- Windows: Download and install from [TA-Lib website](http://ta-lib.org/)
- Linux: `sudo apt-get install ta-lib`
- macOS: `brew install ta-lib`

## Usage

### Backtesting

Run a backtest using the example script:
```bash
python examples/run_backtest.py
```

### Live Trading

To run the bot in live mode:
```python
from src.trading_bot import TradingBot

bot = TradingBot(
    symbol='SPY',
    data_source='alpaca',  # or 'yfinance'
    api_key='your_api_key',
    api_secret='your_api_secret',
    paper_trading=True
)

bot.run_live()
```

## Project Structure

```
scalp-trade/
├── src/
│   ├── strategy.py      # Trading strategy implementation
│   ├── data_handler.py  # Market data handling
│   ├── backtest.py      # Backtesting engine
│   └── trading_bot.py   # Main trading bot
├── examples/
│   └── run_backtest.py  # Example backtest script
├── data/                # Historical data storage
├── backtests/          # Backtest results
├── logs/               # Trading logs
├── requirements.txt    # Project dependencies
└── README.md          # Documentation
```

## Strategy Logic

The bot uses the following indicators and rules:

1. Bollinger Band Squeeze
   - Detects periods of low volatility
   - Signals potential breakout opportunities

2. RSI Oversold/Overbought
   - Identifies extreme price movements
   - Used for entry and exit signals

3. Volatility Filters
   - Ensures sufficient market movement
   - Prevents trading in choppy conditions

## Risk Management

- Stop-loss: 1% from entry
- Take-profit: 2% from entry
- Maximum holding time: 20 minutes
- Position sizing: 10% of capital per trade

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS. 