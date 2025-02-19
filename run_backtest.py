# run_backtest.py
from strategy import PsyLevelsStrategy
from indicator.data_loader import DataLoader
from backtesting import Backtest
import pandas as pd
from config import STRATEGY_CONFIG

def run_psy_levels_backtest():
    loader = DataLoader()
    df = loader.get_detailed_crypto_data(
        symbol=STRATEGY_CONFIG['symbol'],
        start_date=STRATEGY_CONFIG['start_date'],
        end_date=STRATEGY_CONFIG['end_date'],
        timeframe=STRATEGY_CONFIG['timeframe']
    )
    
    if df is None or df.empty:
        print("Failed to load data or empty DataFrame")
        return
    
    bt = Backtest(
        df,
        PsyLevelsStrategy,
        cash=STRATEGY_CONFIG['initial_capital'],
        commission=STRATEGY_CONFIG['commission'],
        margin=1.0,
        trade_on_close=False,
        hedging=False       # Only one net position at a time
    )
    
    stats = bt.run()
    bt.plot(filename='backtest_results.html', resample=False, open_browser=False)
    
    print("\nBacktest Results:")
    print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
    print(f"Profit Factor: {stats['Profit Factor']:.2f}")
    print(f"Total Trades: {stats['# Trades']}")
    
    return stats

if __name__ == "__main__":
    stats = run_psy_levels_backtest()
    print("\nBacktest Results:")
    print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate: {stats['Win Rate [%]']:.2f}%")
    print(f"Profit Factor: {stats['Profit Factor']:.2f}")
    print(f"Total Trades: {stats['# Trades']}")
