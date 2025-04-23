import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime, timedelta
from .strategy import ScalpStrategy, TradeSignal

class BacktestEngine:
    def __init__(
        self,
        strategy: ScalpStrategy,
        initial_capital: float = 100000.0,
        commission: float = 0.0,
        slippage: float = 0.0
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.positions: List[Dict] = []
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []
        
    def run(self, data: pd.DataFrame) -> Dict:
        """Run backtest on historical data."""
        current_capital = self.initial_capital
        current_position = None
        
        for i in range(len(data)):
            current_time = data.index[i]
            current_data = data.iloc[:i+1]
            
            # Check for exit conditions if in position
            if current_position:
                exit_signal = self._check_exit_conditions(current_position, current_data)
                if exit_signal:
                    current_capital = self._close_position(current_position, current_data, current_capital)
                    current_position = None
            
            # Generate new signals if not in position
            if not current_position:
                signal = self.strategy.generate_signals(current_data)
                if signal:
                    current_position = self._open_position(signal, current_data, current_capital)
                    if current_position:
                        current_capital -= current_position['entry_price'] * current_position['size']
            
            # Update equity curve
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': current_capital
            })
        
        return self._generate_performance_metrics()
    
    def _open_position(self, signal: TradeSignal, data: pd.DataFrame, capital: float) -> Dict:
        """Open a new position based on signal."""
        position_size = int(capital * 0.1 / signal.price)  # 10% of capital
        if position_size < 1:
            return None
            
        position = {
            'entry_time': signal.timestamp,
            'direction': signal.direction,
            'entry_price': signal.price * (1 + self.slippage),
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'size': position_size
        }
        
        self.positions.append(position)
        return position
    
    def _close_position(self, position: Dict, data: pd.DataFrame, capital: float) -> float:
        """Close an existing position."""
        current_price = data['close'].iloc[-1]
        exit_price = current_price * (1 - self.slippage if position['direction'] == 'LONG' else 1 + self.slippage)
        
        pnl = (exit_price - position['entry_price']) * position['size']
        if position['direction'] == 'SHORT':
            pnl = -pnl
            
        pnl -= self.commission * 2  # Entry and exit commission
        
        trade = {
            'entry_time': position['entry_time'],
            'exit_time': data.index[-1],
            'direction': position['direction'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'size': position['size'],
            'pnl': pnl
        }
        
        self.trades.append(trade)
        return capital + pnl
    
    def _check_exit_conditions(self, position: Dict, data: pd.DataFrame) -> bool:
        """Check if position should be closed."""
        current_price = data['close'].iloc[-1]
        
        # Check stop loss
        if position['direction'] == 'LONG' and current_price <= position['stop_loss']:
            return True
        elif position['direction'] == 'SHORT' and current_price >= position['stop_loss']:
            return True
            
        # Check take profit
        if position['direction'] == 'LONG' and current_price >= position['take_profit']:
            return True
        elif position['direction'] == 'SHORT' and current_price <= position['take_profit']:
            return True
            
        # Check max holding time
        holding_time = data.index[-1] - position['entry_time']
        if holding_time >= timedelta(minutes=self.strategy.max_holding_time):
            return True
            
        return False
    
    def _generate_performance_metrics(self) -> Dict:
        """Calculate performance metrics from backtest results."""
        if not self.trades:
            return {}
            
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)
        
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum()
        max_drawdown = (equity_df['equity'].max() - equity_df['equity'].min()) / equity_df['equity'].max()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'average_win': avg_win,
            'average_loss': avg_loss,
            'total_pnl': total_pnl,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': self._calculate_sharpe_ratio(equity_df)
        }
    
    def _calculate_sharpe_ratio(self, equity_df: pd.DataFrame) -> float:
        """Calculate Sharpe ratio from equity curve."""
        returns = equity_df['equity'].pct_change().dropna()
        if len(returns) < 2:
            return 0.0
            
        risk_free_rate = 0.02  # 2% annual risk-free rate
        daily_rf = (1 + risk_free_rate) ** (1/252) - 1
        
        excess_returns = returns - daily_rf
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std() if excess_returns.std() != 0 else 0 