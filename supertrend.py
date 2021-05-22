import ccxt
import pandas as pd
pd.set_option('display.max_rows', None)

exchange = ccxt.binanceus()

bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='1d', limit=365)

df = pd.DataFrame(bars[:-1], columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit = 'ms')

def tr(df):
    df['previous_close'] = df['close'].shift(1)
    df['high-low'] = abs(df['high'] - df['low'])
    df['high-pc'] = abs(df['high'] -df['previous_close'])
    df['low-pc'] = abs(df['low'] - df['previous_close'])

    tr = df[['high-low', 'high-pc', 'low-pc']].max(axis=1)
    return tr


def atr(df, period):
    df['tr'] = tr(df)
    print("calculate average true range")
    atr = df['tr'].rolling(period).mean()

    return atr

def supertrend(df, period=7, atr_multiplier=3):
    # basic upper band = (high +low /2) + (multiplier *atr)
    # basic lower band = (high +low /2) - (multiplier *atr)
    df['atr'] = atr(df, period)
    df['upperband'] = ((df['high'] + df['low'])/2) + (atr_multiplier * df['atr'])
    df['lowerband'] = ((df['high'] + df['low'])/2) - (atr_multiplier * df['atr'])
    df['in_uptrend']  = True

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

    print(df)



supertrend(df)
