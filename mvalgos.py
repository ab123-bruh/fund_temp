import pandas as pd
import yfinance as yf
import numpy as np
import requests
from mvdata import TickerData

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

# Need to add the Kalman Filter method after some more reading and use bt to show performance better or worse
def tail_action(tickers: list, start_date: str):
    tick_str = ""

    for tick in tickers:
        tick_str += (tick + " ")

    df = TickerData(tick_str).get_historical_data(start_date=start_date)
    window = 50

    rolling_mean = df.rolling(window=window).mean()
    rolling_std = df.rolling(window=window).std()

    buy_signal = df < rolling_mean - (2 * rolling_std)
    sell_signal = df >= rolling_mean + (2 * rolling_std)

    ticker_action = pd.DataFrame(df.index)

    for tick in tickers:
        ticker_action[tick + "_Signal"] = TickerData(tick).action_tickers(buy_signal,sell_signal)

    date = ticker_action.pop("Date")
    ticker_action = ticker_action.set_index(date)

    return pd.concat([df,ticker_action],axis=1)