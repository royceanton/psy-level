# backtest.py
from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np
from indicator.psy_levels import PsychologicalLevels
from indicator.data_loader import DataLoader
from datetime import timedelta
from config import STRATEGY_CONFIG

class PsyLevelsStrategy(Strategy):
    """
    Psychological Levels Breakout Strategy with Trailing TP,
    using a two-step approach:
      1) When price crosses the breakout threshold, trigger a pure market order.
      2) On the next bar, attach SL and TP based on the actual fill price.
    Allows multiple breakouts in the same week.
    """

    # Strategy parameters
    entry_offset = STRATEGY_CONFIG['entry_offset']
    take_profit = STRATEGY_CONFIG['take_profit']
    risk_per_trade = STRATEGY_CONFIG['risk_per_trade']
    sl_offset = STRATEGY_CONFIG['sl_offset']
    trailing_offset = STRATEGY_CONFIG['trailing_offset']

    def init(self):
        # Calculate weekly psy levels from hourly data (5m -> 1h)
        self.psy = PsychologicalLevels()
        hourly_data = self.resample_to_hourly(self.data.df)
        df_levels = self.psy.calc_psy_levels(hourly_data, psy_type='crypto')
        
        # Resample psy levels back to the 5m timeframe
        psy_hi_series = df_levels['psy_hi'].reindex(self.data.df.index).ffill()
        psy_lo_series = df_levels['psy_lo'].reindex(self.data.df.index).ffill()
        self.psy_hi = self.I(lambda: psy_hi_series, name='psy_hi')
        self.psy_lo = self.I(lambda: psy_lo_series, name='psy_lo')
        
        # State variables
        self.current_week = None
        # Block trading until 6 hours after new levels (e.g., Sunday 04:00)
        self.trade_blocked_until = None
        # Store pending bracket orders info for setting SL/TP after fill
        self.pending_sl = None
        self.pending_tp = None

    def resample_to_hourly(self, df):
        """Resample 5m data to 1h for psy level calculation."""
        return df.resample('1h').agg({
            'Open': 'first',
            'High': 'max',
            'Low':  'min',
            'Close': 'last',
            'Volume': 'sum'
        })

    def should_update_weekly_levels(self):
        """Check if new weekly psy levels need to be set (Saturday 22:00 UTC)."""
        current_time = self.data.index[-1]
        this_week = current_time.isocalendar()[1]
        is_saturday_22 = (
            current_time.weekday() == 5 and
            current_time.hour == 22 and
            current_time.minute == 0
        )
        if (is_saturday_22 or self.current_week is None) and (self.current_week != this_week):
            return True
        return False

    def price_in_range(self):
        """Return True if current price is between psy_lo and psy_hi."""
        price = self.data.Close[-1]
        return (price >= self.psy_lo[-1]) and (price <= self.psy_hi[-1])

    def next(self):
        current_time = self.data.index[-1]
        price = self.data.Close[-1]

        # Skip if psy levels are not available
        if pd.isna(self.psy_hi[-1]) or pd.isna(self.psy_lo[-1]):
            return

        # 1) Weekly level update
        if self.should_update_weekly_levels():
            print(f"\n*** New weekly levels at {current_time} ***")
            print(f"PSY High: {self.psy_hi[-1]:.2f}, PSY Low: {self.psy_lo[-1]:.2f}")
            if self.position:
                self.position.close()
            self.current_week = current_time.isocalendar()[1]
            self.trade_blocked_until = current_time + timedelta(hours=6)

        # 2) Block trading until after the blocked period
        if self.trade_blocked_until and current_time < self.trade_blocked_until:
            return

        # 3) If a position is open, update trailing TP and do nothing else
        if self.position:
            self.update_trailing_tp()
            return

        # 4) If no position, check breakouts on every bar
        self.check_breakouts(price)

    def update_trailing_tp(self):
        """If in a position, trail the TP once profit >= 1% from fill price."""
        price = self.data.Close[-1]
        t = self.trades[-1]
        entry_price = t.entry_price
        if self.position.is_long:
            if price >= entry_price * (1 + self.take_profit):
                new_tp = price * (1 + self.trailing_offset)
                if new_tp > t.tp:
                    t.tp = new_tp
                    print(f"{self.data.index[-1]} Long trailing TP updated to {new_tp:.2f}")
        elif self.position.is_short:
            if price <= entry_price * (1 - self.take_profit):
                new_tp = price * (1 - self.trailing_offset)
                if new_tp < t.tp:
                    t.tp = new_tp
                    print(f"{self.data.index[-1]} Short trailing TP updated to {new_tp:.2f}")

    def check_breakouts(self, price):
        hi = self.psy_hi[-1]
        lo = self.psy_lo[-1]
        buy_breakout = hi * (1 + self.entry_offset)
        sell_breakout = lo * (1 - self.entry_offset)
        # Debug prints for each bar
        print(f"{self.data.index[-1]} Price: {price:.2f}, Buy_breakout: {buy_breakout:.2f}, Sell_breakout: {sell_breakout:.2f}")
        if price >= buy_breakout:
            self.place_breakout_trade(direction='long', fill_price=price)
        elif price <= sell_breakout:
            self.place_breakout_trade(direction='short', fill_price=price)

    def place_breakout_trade(self, direction, fill_price):
        """
        Trigger a pure market order (with limit and stop as None)
        and store desired SL/TP to attach on the next bar.
        """
        # Calculate size based on risk
        if direction == 'long':
            sl = self.psy_lo[-1] * (1 - self.sl_offset)
            size_diff = abs(fill_price - sl)
        else:
            sl = self.psy_hi[-1] * (1 + self.sl_offset)
            size_diff = abs(sl - fill_price)
        if size_diff < 1e-8:
            return
        risk_cap = self.equity * self.risk_per_trade
        size = risk_cap / size_diff
        if size >= 1:
            size = int(round(size))
        # Calculate desired TP based on breakout level:
        if direction == 'long':
            desired_tp = fill_price * (1 + self.take_profit)
            print(f"{self.data.index[-1]} MARKET BUY triggered: Price={fill_price:.2f}")
            self.buy(size=size, limit=None, stop=None)
        else:
            desired_tp = fill_price * (1 - self.take_profit)
            print(f"{self.data.index[-1]} MARKET SELL triggered: Price={fill_price:.2f}")
            self.sell(size=size, limit=None, stop=None)
        
        # Store the desired SL/TP for the next bar
        self.pending_sl = sl
        self.pending_tp = desired_tp

    def set_sl_tp_for_new_position(self):
        """
        On the next bar after a breakout trade is triggered,
        set the SL and TP for the active trade.
        """
        if self.position and (self.pending_sl is not None or self.pending_tp is not None):
            t = self.trades[-1]
            if t.sl is None and self.pending_sl is not None:
                t.sl = self.pending_sl
            if t.tp is None and self.pending_tp is not None:
                t.tp = self.pending_tp
            # Reset pending values after applying
            self.pending_sl = None
            self.pending_tp = None

    def next(self):
        current_time = self.data.index[-1]
        price = self.data.Close[-1]
        
        # If there's a new trade (position open) but SL/TP not yet set, set them.
        self.set_sl_tp_for_new_position()
        
        # Skip if no psy levels are available
        if pd.isna(self.psy_hi[-1]) or pd.isna(self.psy_lo[-1]):
            return
        
        # Weekly level update
        if self.should_update_weekly_levels():
            print(f"\n*** New weekly levels at {current_time} ***")
            print(f"PSY High: {self.psy_hi[-1]:.2f}, PSY Low: {self.psy_lo[-1]:.2f}")
            if self.position:
                self.position.close()
            self.current_week = current_time.isocalendar()[1]
            self.trade_blocked_until = current_time + timedelta(hours=6)
        
        # Block trading until the blocked period is over
        if self.trade_blocked_until and current_time < self.trade_blocked_until:
            return
        
        # If a position is open, update trailing TP and do nothing else
        if self.position:
            self.update_trailing_tp()
            return
        
        # If no position, check breakouts every bar
        self.check_breakouts(price)
