# Strategy Parameters
STRATEGY_CONFIG = {
    'symbol': 'BTC/USDT',
    'timeframe': '5m',
    'initial_capital': 1_000_000,
    'commission': 0.002,
    
    # PsyLevels Parameters
    'entry_offset': 0.0001,
    'take_profit': 0.01,
    'risk_per_trade': 0.01,
    'sl_offset': 0.0001,
    'trailing_offset': 0.005,
    
    # Backtest Period
    'start_date': '2024-01-01',
    'end_date': '2024-02-16',
    
    # Data Settings
    'cache_data': True,
    'refresh_data': False
} 