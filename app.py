from flask import Flask, render_template, jsonify, request
from src.trading_bot import TradingBot
from datetime import datetime, timedelta
import pandas as pd
import json
import sys
from waitress import serve
import yfinance as yf
import numpy as np

app = Flask(__name__)

def run_backtest(data, strategy='scalping'):
    """
    Run a backtest on the provided SPY data using the specified strategy.
    
    Args:
        data (list): List of dictionaries containing OHLCV data for SPY
        strategy (str): Strategy to use for backtesting
        
    Returns:
        dict: Backtest results including trades and performance metrics
    """
    if not data:
        return {
            'error': 'No SPY data available for backtesting',
            'trades': [],
            'performance': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_pnl': 0
            }
        }
    
    # Convert data to pandas DataFrame for easier manipulation
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Initialize variables for tracking trades
    trades = []
    position = None
    entry_price = None
    entry_time = None
    
    # SPY scalping strategy parameters
    stop_loss_pct = 0.05  # 0.05% stop loss
    take_profit_pct = 0.10  # 0.10% take profit - higher than stop loss for better risk/reward
    
    # Simple scalping strategy optimized for SPY
    if strategy == 'scalping':
        for i in range(1, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Entry conditions
            if position is None:
                # Long entry: Price breaks above previous high with volume confirmation
                if current['high'] > prev['high'] and current['volume'] > prev['volume']:
                    position = 'long'
                    entry_price = current['open']
                    entry_time = current.name
                    stop_loss = entry_price * (1 - stop_loss_pct)
                    take_profit = entry_price * (1 + take_profit_pct)
                    
                # Short entry: Price breaks below previous low with volume confirmation
                elif current['low'] < prev['low'] and current['volume'] > prev['volume']:
                    position = 'short'
                    entry_price = current['open']
                    entry_time = current.name
                    stop_loss = entry_price * (1 + stop_loss_pct)
                    take_profit = entry_price * (1 - take_profit_pct)
            
            # Exit conditions
            elif position == 'long':
                if current['low'] <= stop_loss:
                    # Stop loss hit
                    exit_price = stop_loss
                    exit_time = current.name
                    pnl = (exit_price - entry_price) / entry_price * 100
                    trades.append({
                        'entry_time': entry_time.isoformat(),
                        'exit_time': exit_time.isoformat(),
                        'direction': 'long',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'exit_reason': 'stop_loss'
                    })
                    position = None
                elif current['high'] >= take_profit:
                    # Take profit hit
                    exit_price = take_profit
                    exit_time = current.name
                    pnl = (exit_price - entry_price) / entry_price * 100
                    trades.append({
                        'entry_time': entry_time.isoformat(),
                        'exit_time': exit_time.isoformat(),
                        'direction': 'long',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'exit_reason': 'take_profit'
                    })
                    position = None
            
            elif position == 'short':
                if current['high'] >= stop_loss:
                    # Stop loss hit
                    exit_price = stop_loss
                    exit_time = current.name
                    pnl = (entry_price - exit_price) / entry_price * 100
                    trades.append({
                        'entry_time': entry_time.isoformat(),
                        'exit_time': exit_time.isoformat(),
                        'direction': 'short',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'exit_reason': 'stop_loss'
                    })
                    position = None
                elif current['low'] <= take_profit:
                    # Take profit hit
                    exit_price = take_profit
                    exit_time = current.name
                    pnl = (entry_price - exit_price) / entry_price * 100
                    trades.append({
                        'entry_time': entry_time.isoformat(),
                        'exit_time': exit_time.isoformat(),
                        'direction': 'short',
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'exit_reason': 'take_profit'
                    })
                    position = None
    
    # Calculate performance metrics
    if trades:
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades * 100
        total_pnl = sum(t['pnl'] for t in trades)
        avg_pnl = total_pnl / total_trades
        
        # Calculate additional metrics
        profit_factor = abs(sum(t['pnl'] for t in trades if t['pnl'] > 0)) / abs(sum(t['pnl'] for t in trades if t['pnl'] < 0)) if losing_trades > 0 else float('inf')
        avg_win = sum(t['pnl'] for t in trades if t['pnl'] > 0) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(t['pnl'] for t in trades if t['pnl'] < 0) / losing_trades if losing_trades > 0 else 0
    else:
        total_trades = winning_trades = losing_trades = 0
        win_rate = total_pnl = avg_pnl = profit_factor = avg_win = avg_loss = 0
    
    return {
        'trades': trades,
        'performance': {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss
        }
    }

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/backtest', methods=['POST'])
def backtest():
    try:
        data = request.json
        ticker = data.get('ticker', 'SPY')
        timeframe = data.get('timeframe', '1m')
        period = int(data.get('period', 1))
        strategy = data.get('strategy', 'scalping')
        
        # Get current time
        now = datetime.now()
        
        # Find the most recent business day
        end_date = now
        while end_date.weekday() > 4:  # 5 is Saturday, 6 is Sunday
            end_date = end_date - timedelta(days=1)
            
        # For minute-level data, handle market hours
        if timeframe in ['1m', '5m']:
            # Set to previous market close if current time is outside market hours
            market_open = end_date.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
            
            if now < market_open or now > market_close:
                # If before market open or after market close, use previous business day
                end_date = end_date - timedelta(days=1)
                while end_date.weekday() > 4:  # Skip weekends
                    end_date = end_date - timedelta(days=1)
                end_date = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
            else:
                # During market hours, use current time
                end_date = now.replace(second=0, microsecond=0)
            
            # Calculate start date
            if timeframe == '1m':
                period = min(period, 7)  # Limit to 7 days for 1-minute data
            else:  # 5m
                period = min(period, 60)  # Limit to 60 days for 5-minute data
            
            # Find start date by counting back the required number of business days
            start_date = end_date
            business_days = 0
            while business_days < period:
                start_date = start_date - timedelta(days=1)
                if start_date.weekday() < 5:  # Only count business days
                    business_days += 1
            
            # Set start date to market open
            start_date = start_date.replace(hour=9, minute=30, second=0, microsecond=0)
        else:
            # For daily data, count back business days
            end_date = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
            start_date = end_date
            business_days = 0
            while business_days < period:
                start_date = start_date - timedelta(days=1)
                if start_date.weekday() < 5:  # Only count business days
                    business_days += 1
            start_date = start_date.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # Log the date range
        print(f"Backtesting {ticker} from {start_date} to {end_date} (timeframe: {timeframe}, period: {period} business days)")
        
        # Fetch data from yfinance
        data = yf.download(ticker, start=start_date, end=end_date, interval=timeframe)
        
        if data.empty:
            error_msg = f"No data available for {ticker} from {start_date} to {end_date} (timeframe: {timeframe}, period: {period} business days)"
            print(error_msg)
            return jsonify({
                'error': error_msg,
                'timeframe': timeframe,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }), 404
            
        # Convert data to list of dictionaries
        data_list = []
        for index, row in data.iterrows():
            # Only include data from business days
            if index.weekday() < 5:  # Monday to Friday
                data_list.append({
                    'date': index.isoformat(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
        # Run backtest
        results = run_backtest(data_list, strategy)
        
        return jsonify({
            'results': results,
            'timeframe': timeframe,
            'period': period,
            'period_days': period
        })
        
    except Exception as e:
        print(f"Error running backtest: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-data')
def get_market_data():
    try:
        ticker = request.args.get('ticker', 'SPY')
        timeframe = request.args.get('timeframe', '1m')
        period = int(request.args.get('period', 1))
        
        # Get current time
        now = datetime.now()
        
        # Find the most recent business day
        end_date = now
        while end_date.weekday() > 4:  # 5 is Saturday, 6 is Sunday
            end_date = end_date - timedelta(days=1)
            
        # For minute-level data, handle market hours
        if timeframe in ['1m', '5m']:
            # Set to previous market close if current time is outside market hours
            market_open = end_date.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
            
            if now < market_open or now > market_close:
                # If before market open or after market close, use previous business day
                end_date = end_date - timedelta(days=1)
                while end_date.weekday() > 4:  # Skip weekends
                    end_date = end_date - timedelta(days=1)
                end_date = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
            else:
                # During market hours, use current time
                end_date = now.replace(second=0, microsecond=0)
            
            # Calculate start date
            if timeframe == '1m':
                period = min(period, 7)  # Limit to 7 days for 1-minute data
            else:  # 5m
                period = min(period, 60)  # Limit to 60 days for 5-minute data
            
            # Find start date by counting back the required number of business days
            start_date = end_date
            business_days = 0
            while business_days < period:
                start_date = start_date - timedelta(days=1)
                if start_date.weekday() < 5:  # Only count business days
                    business_days += 1
            
            # Set start date to market open
            start_date = start_date.replace(hour=9, minute=30, second=0, microsecond=0)
        else:
            # For daily data, count back business days
            end_date = end_date.replace(hour=16, minute=0, second=0, microsecond=0)
            start_date = end_date
            business_days = 0
            while business_days < period:
                start_date = start_date - timedelta(days=1)
                if start_date.weekday() < 5:  # Only count business days
                    business_days += 1
            start_date = start_date.replace(hour=9, minute=30, second=0, microsecond=0)
            
        # Log the date range
        print(f"Fetching data for {ticker} from {start_date} to {end_date} (timeframe: {timeframe}, period: {period} business days)")
        
        # Fetch data from yfinance
        data = yf.download(ticker, start=start_date, end=end_date, interval=timeframe)
        
        if data.empty:
            error_msg = f"No data available for {ticker} from {start_date} to {end_date} (timeframe: {timeframe}, period: {period} business days)"
            print(error_msg)
            return jsonify({
                'error': error_msg,
                'timeframe': timeframe,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }), 404
            
        # Convert data to list of dictionaries
        data_list = []
        for index, row in data.iterrows():
            # Only include data from business days
            if index.weekday() < 5:  # Monday to Friday
                data_list.append({
                    'date': index.isoformat(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
        return jsonify({
            'data': data_list,
            'timeframe': timeframe,
            'period': period,
            'period_info': f"Showing {period} business days of {timeframe} data"
        })
        
    except Exception as e:
        print(f"Error fetching market data: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        print("Starting server on http://localhost:8080")
        serve(app, host='0.0.0.0', port=8080)
    except Exception as e:
        print(f"Error starting server: {str(e)}", file=sys.stderr)
        sys.exit(1) 