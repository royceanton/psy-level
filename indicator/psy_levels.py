import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

class PsychologicalLevels:
    def __init__(self):
        # Default colors
        self.colors = {
            'red_vector': '#FF0000',
            'green_vector': '#00FF00', 
            'violet_vector': '#FF00FF',
            'blue_vector': '#0000FF',
            'regular_up': '#999999',
            'regular_down': '#4D4D4D',
            'psy_hi': '#FFA500',
            'psy_lo': '#FFA500'
        }
        
        # Constants
        self.ONE_WEEK_MILLIS = 7 * 24 * 60 * 60 * 1000
        
    def calc_dst(self, date):
        """Calculate DST status for NY, UK and Sydney"""
        month = date.month
        day = date.day
        previous_sunday = day - date.weekday() + 1
        
        ny_dst = False
        uk_dst = False 
        syd_dst = False
        
        if month < 3 or month > 11:
            ny_dst = False
            uk_dst = False 
            syd_dst = True
        elif month > 4 and month < 10:
            ny_dst = True
            uk_dst = True
            syd_dst = False
        elif month == 3:
            ny_dst = previous_sunday >= 8
            uk_dst = previous_sunday >= 24
            syd_dst = True
        elif month == 4:
            ny_dst = True
            uk_dst = True
            syd_dst = previous_sunday <= 0
        elif month == 10:
            ny_dst = True
            uk_dst = previous_sunday <= 24
            syd_dst = previous_sunday >= 0
        else:  # month == 11
            ny_dst = previous_sunday <= 0
            uk_dst = False
            syd_dst = True
            
        return ny_dst, uk_dst, syd_dst



    def calc_psy_levels(self, df, psy_type='crypto'):
        """
        For each Saturday 22:00 UTC (for crypto):
          1) Take the high/low of the previous hour (21:00–22:00).
          2) Take the next 6 hourly candles (22:00–03:00).
          3) The highest high among those 7 hours is psy_hi, the lowest low is psy_lo.
          4) Plot those levels for the rest of the week (until next Saturday 22:00).
        """
        # Ensure index is a proper UTC DateTimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')

        # Create columns for psy levels
        df['psy_hi'] = np.nan
        df['psy_lo'] = np.nan
        
        if psy_type == 'crypto':
            # 1) Identify all Saturdays at exactly 22:00 UTC in your data
            session_starts = df.index[
                (df.index.weekday == 5) & (df.index.hour == 22) & (df.index.minute == 0)
            ].sort_values()
        else:  # forex
            # For forex, use Monday 00:00 UTC
            session_starts = df.index[
                (df.index.weekday == 0) & (df.index.hour == 0) & (df.index.minute == 0)
            ].sort_values()

        # 2) Loop over each found session start, do the calc for that upcoming week
        for i, start_time in enumerate(session_starts):
            # Define an end_time for this "week" (either next session_start or +7 days if at the end)
            if i < len(session_starts) - 1:
                end_time = session_starts[i + 1]
            else:
                end_time = df.index[-1]  # just go to the end of the data

            # Prepare arrays for collecting the 7 candles' highs/lows
            highs = []
            lows = []

            # 2a) The hour before session start
            init_start = start_time - pd.Timedelta(hours=1)
            init_end = start_time
            init_mask = (df.index >= init_start) & (df.index < init_end)
            if init_mask.any():
                init_data = df.loc[init_mask]
                highs.append(init_data['High'].max())
                lows.append(init_data['Low'].min())

            # 2b) Next 6 hours after session start
            for h in range(6):
                hour_start = start_time + pd.Timedelta(hours=h)
                hour_end = hour_start + pd.Timedelta(hours=1)
                mask = (df.index >= hour_start) & (df.index < hour_end)
                if mask.any():
                    hour_data = df.loc[mask]
                    highs.append(hour_data['High'].max())
                    lows.append(hour_data['Low'].min())

            # 3) If we have any valid data from those 7 candles, set psy_hi/psy_lo
            if highs and lows:
                psy_hi = max(highs)
                psy_lo = min(lows)

                # 4) Apply these levels from start_time until next session start
                week_mask = (df.index >= start_time) & (df.index < end_time)
                df.loc[week_mask, 'psy_hi'] = psy_hi
                df.loc[week_mask, 'psy_lo'] = psy_lo

        return df


    def generate_alerts(self, df):
        """Generate trading alerts based on price crosses of psychological levels"""
        alerts = []
        
        # Calculate crosses
        price_crosses_hi = (df['close'] > df['psy_hi']).astype(int).diff()
        price_crosses_lo = (df['close'] > df['psy_lo']).astype(int).diff()
        
        # Crossover alerts (price crosses above level)
        crossover_hi = df.index[price_crosses_hi == 1]
        crossover_lo = df.index[price_crosses_lo == 1]
        
        # Crossunder alerts (price crosses below level)
        crossunder_hi = df.index[price_crosses_hi == -1]
        crossunder_lo = df.index[price_crosses_lo == -1]
        
        # Generate alert messages
        for timestamp in crossover_hi:
            alerts.append({
                'timestamp': timestamp,
                'message': 'PA crossed over Psy Hi',
                'level': df.loc[timestamp, 'psy_hi']
            })
            
        for timestamp in crossover_lo:
            alerts.append({
                'timestamp': timestamp,
                'message': 'PA crossed over Psy Lo',
                'level': df.loc[timestamp, 'psy_lo']
            })
            
        for timestamp in crossunder_hi:
            alerts.append({
                'timestamp': timestamp,
                'message': 'PA crossed under Psy Hi',
                'level': df.loc[timestamp, 'psy_hi']
            })
            
        for timestamp in crossunder_lo:
            alerts.append({
                'timestamp': timestamp,
                'message': 'PA crossed under Psy Lo',
                'level': df.loc[timestamp, 'psy_lo']
            })
            
        return pd.DataFrame(alerts) 
