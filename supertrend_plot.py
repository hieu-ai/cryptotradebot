import ccxt
import schedule
import time
import pandas as pd
import matplotlib.pyplot as plt
pd.set_option('display.max_rows', None)

import warnings
warnings.filterwarnings('ignore')
import numpy as np

from datetime import datetime
exchange = ccxt.binanceus()
def tr(df):
    df['previous_close'] = df['close'].shift(1)
    df['high-low'] = abs(df['high'] - df['low'])
    df['high-pc'] = abs(df['high'] -df['previous_close'])
    df['low-pc'] = abs(df['low'] - df['previous_close'])

    tr = df[['high-low', 'high-pc', 'low-pc']].max(axis=1)
    return tr


def atr(df, period):
    df['tr'] = tr(df)
    #print("calculate average true range")
    atr = df['tr'].rolling(period).mean()

    return atr

def supertrend(df, period=10, atr_multiplier=3):
    # basic upper band = (high +low /2) + (multiplier *atr)
    # basic lower band = (high +low /2) - (multiplier *atr)
    df['atr'] = atr(df, period)
    df['upperband'] = ((df['high'] + df['low'])/2) + (atr_multiplier * df['atr'])
    df['lowerband'] = ((df['high'] + df['low'])/2) - (atr_multiplier * df['atr'])
    df['in_uptrend']  = True
    #print (len(df.index))
    for current in range(1,len(df.index)):
        previous = current - 1
        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] =True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False

        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]
            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]

    return df

in_position = False
def check_buy_sell_signals(df):
    global in_position
    print("checking for buys and sell")
    print(df.tail(5))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1


    #print (last_row_index)
    # print(previous_row_index)
    """
    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("changed to uptrend, buy")
        if not in_position:
            order = exchange.create_market_buy_order('ETH/USD',0.04)
            print(order)
            in_position = True
        else:
            print("already in prosition, nothing to do")
        

    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        print("changed to uptrend, sell")
        if in_position:
            order = exchange.create_market_sell_order('ETH/USD',0.039)
            print(order)
            in_position = False
        else:
            print("You aren't in position")
    """

def fetch_bars():
    print(f"Fetching new bars for {datetime.now().isoformat()}")

    try:
        bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='1m', limit=100)
    except ccxt.NetworkError as e:
        print(exchange.id, 'fetch_ohlcv failed due to a network error:', str(e))
        # retry or whatever
        # ...
    except ccxt.ExchangeError as e:
        print(exchange.id, 'fetch_ohlcv failed due to exchange error:', str(e))
        # retry or whatever
        # ...
    except Exception as e:
        print(exchange.id, 'fetch_ohlcv failed with:', str(e))
        # retry or whatever
        # ...
    
    df = pd.DataFrame(bars[:], columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit = 'ms')

    supertrend_data = supertrend(df)

    """
    plt.plot(df['timestamp'],df['close'])
    plt.xlabel('Times')
    plt.ylabel('prices')
    plt.title('Supertrend graph')
    plt.figure().show()
    """

    check_buy_sell_signals(supertrend_data)
    #print(supertrend_data)

schedule.every(60).seconds.do(fetch_bars)
#supertrend(df)
while True:
    schedule.run_pending()
    time.sleep(1)