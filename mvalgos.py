import pandas as pd
import yfinance as yf
import numpy as np
import requests
import mvdata as mvD

# Ideally these algos are borrowing from methods in engineering applications so methods from thermodynamics
# or other disciplines to determine actions in a time series is what users look for

class TrendFollowing:
    def __init__(self):
        pass

    def method1(self):
        pass

class MeanReversion:
    def __init__(self):
        pass

    def method1(self):
        pass

# This needs a lot of reworking and also we will have to add the backtesting code into the repository
def tail_action(tickers: list):
    tick_str = ""

    for tick in tickers:
        tick_str += (tick + " ")

    df = mvD.TickerData(tick_str).get_historical_data()
    window = 50

    rolling_mean = df.rolling(window=window).mean()
    rolling_std = df.rolling(window=window).std()

    buy_signal = df < rolling_mean - (2 * rolling_std)
    sell_signal = df >= rolling_mean + (2 * rolling_std)

    ticker_action = pd.DataFrame(df.index)

    for tick in tickers:
        ticker_action[tick + "_Signal"] = mvD.AlgoStats(tick).action_tickers(buy_signal,sell_signal)

    date = ticker_action.pop("Date")
    ticker_action = ticker_action.set_index(date)

    return pd.concat([df,ticker_action],axis=1)