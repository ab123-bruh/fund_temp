import pandas as pd
import yfinance as yf
import numpy as np
from retrieve import Basket

class TickerData:
    def __init__(self, tickers: list, start_date: str):
        self.tickers = tickers
        self.start_date = start_date
    
    def get_historical_data(self):
        ticker = self.tickers[0]

        for tick in self.tickers[1:]:
            ticker += (" " + tick)
        
        data = yf.download(ticker,start=self.start_date)

        return data["Adj Close"]
    
    def correlation_matrix(self):
        df = self.get_historical_data().corr()
        df = df.where(np.triu(np.ones(df.shape)).astype(np.bool_))

        return df
    
    def ticker_volatility(self):
        return self.get_historical_data().std()


class PortfolioAnalytics:
    def __init__(self):
        self.portfolio = Basket().get_portfolio()
    
    def portfolio_volatility(self):
        Q = TickerData(list(self.portfolio.keys()),"2020-01-01").get_historical_data().cov()
        w = np.array(list(self.portfolio.values()))

        var = np.matmul(np.matmul(w.T,Q),w)

        return np.sqrt(var)