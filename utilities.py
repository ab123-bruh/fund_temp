import pandas as pd
import yfinance as yf
import datetime as dt

def ticker_history(start_date="2020-01-01", end_date=dt.datetime.today().strftime("%Y-%m-%d")):
    return yf.download("SPY",start=start_date,end=end_date)["Close"]

def correlation_matrix():
    a = ticker_history()
    return a.corr()

class OneTicker:
    pass

class MultipleTickers:
    def __init__(self, ticker: str, symbols: list=None):
        self.ticker = ticker 
        self.symbols = symbols   
    
    def get_historical_data(self, start_date="2020-01-01", end_date=dt.datetime.today().strftime("%Y-%m-%d")):
        return yf.download(self.ticker,start=start_date,end=end_date)["Close"]
    
    def build_correlation_matrix(self):
        pass
    
    def get_data():
        pass

print(correlation_matrix())


