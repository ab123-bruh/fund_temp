import pandas as pd
import yfinance as yf
import numpy as np
from retrieve import Basket 
import datetime as dt

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
        Q = PortfolioAnalytics(self.start_date).portfolio_data().cov()
        w = np.array(list(self.portfolio.values()))

        var = np.matmul(np.matmul(w.T,Q),w)

        return np.sqrt(var)
    
    def portfolio_beta(self):
        beta = 0

        for tick,weight in self.portfolio.items():
            try:
                beta += (weight*yf.Ticker(tick).info["beta"])
            except:
                continue
        
        return beta
    
    def risk_metrics(self):
        def percent_change(df: pd.DataFrame, tick: str):
            return ((df[tick].iloc[len(df)-1]/df[tick].iloc[0])-1).round(decimals=4)
        
        stats = {}

        date = dt.date(dt.date.today().year,1,1).strftime("%Y-%m-%d")

        tick_compares = TickerData("IWF VTV SPY ^VIX SIZE").get_historical_data(start_date=date)
        tick_compares = tick_compares.reset_index()

        treasury = pd.read_html("https://www.multpl.com/10-year-treasury-rate/table/by-year")
        devi_ratio = round(tick_compares["^VIX"].std()/tick_compares["SPY"].std(),4)

        stats["BenchmarkReturn"] = percent_change(tick_compares,"SPY")
        stats["RiskFree"] = round(float(treasury[0].iloc[0,1][:-1])/100,4)

        stats["RiskPremium"] = stats["BenchmarkReturn"] - stats["RiskFree"] 
        stats["GrowthPremium"] = percent_change(tick_compares,"IWF")-stats["RiskFree"]
        stats["ValuePremium"] = percent_change(tick_compares,"VTV")-stats["RiskFree"]
        stats["SizePremium"] = percent_change(tick_compares,"SIZE")-stats["RiskFree"]

        stats["VIX/SPY Corr"] = tick_compares.corr(numeric_only=True).loc["^VIX", "SPY"].round(decimals=4)
        stats["VIX/SPY Beta"] = stats["VIX/SPY Corr"]*devi_ratio

        stats["ExpectedReturn"] = PortfolioAnalytics(date).portfolio_beta()*stats["RiskPremium"]+stats["RiskFree"]

        return pd.DataFrame(stats,index=["Stats"]).T


print(PortfolioAnalytics("2020-01-01").risk_metrics())