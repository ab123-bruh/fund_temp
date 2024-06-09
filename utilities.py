import yfinance as yf
import numpy as np
from retrieve import Basket

class TickerData:
    def __init__(self, ticker: str):
        self.ticker = ticker
            
    def get_historical_data(self,start_date: str):
        return yf.download(self.ticker,start=start_date)["Adj Close"]
    
    def ticker_volatility(self,start_date: str):
        return self.get_historical_data(start_date).std()

    def financial_statements(self,quarterly=True):
        financials = {}

        symbol = yf.Ticker(self.ticker)

        if quarterly is False:
            financials["balanceSheet"] = symbol.balance_sheet
            financials["incomeStatement"] = symbol.income_stmt
            financials["cashFlow"] = symbol.cash_flow
        else:
            financials["balanceSheet"] = symbol.quarterly_balance_sheet
            financials["incomeStatement"] = symbol.quarterly_income_stmt
            financials["cashFlow"] = symbol.quarterly_cash_flow

        return financials
    
    def options_flow(self):
        options = {}
        flow = yf.Ticker(self.ticker).option_chain()

        options["Call"] = flow.calls
        options["Put"] = flow.puts

        return options

    
class PortfolioAnalytics:
    def __init__(self, start_date: str):
        self.portfolio = Basket().get_portfolio()
        self.start_date = start_date
    
    def portfolio_data(self):
        tick = ""

        for ticker in list(self.portfolio.keys()):
            tick += (ticker + " ")

        return TickerData(tick).get_historical_data(self.start_date)

    def correlation_matrix(self):
        df = self.portfolio_data().corr()
        df = df.where(np.triu(np.ones(df.shape)).astype(np.bool_))

        return df
                             
    def portfolio_volatility(self):
        Q = PortfolioAnalytics().portfolio_data().cov()
        w = np.array(list(self.portfolio.values()))

        var = np.matmul(np.matmul(w.T,Q),w)

        return np.sqrt(var)
    
    def portfolio_beta(self):
        # building the table for portfolio beta here
        pass
    
    def hypothetical_return(self):
        pass

    def simulations(self):
        pass