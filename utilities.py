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
    
    def get_balance_sheet(self):
        return yf.Ticker(self.ticker).balance_sheet
    
    def get_income_statement(self):
        return yf.Ticker(self.ticker).income_stmt
    
    def get_cash_flow(self):
        return yf.Ticker(self.ticker).cash_flow

    def options_flow(self):
        options = {}
        flow = yf.Ticker(self.ticker).option_chain()

        options["Call"] = flow.calls
        options["Put"] = flow.puts

        return options
    
    def dcf_fair_value(self, num_years: int, wacc: float, tgv: float):
        inital = ["Total Revenue", "EBIT", "Tax Provision", "Depreciation And Amortization", "Capital Expenditure", 
                  "Change In Working Capital", "Cash And Cash Equivalents", "Total Debt", "Ordinary Shares Number"]
        
        ticker = TickerData(self.ticker)
        
        financials = pd.concat([ticker.get_balance_sheet(),
                                ticker.get_income_statement(),
                                ticker.get_cash_flow()],axis=0)
        
        financials = financials.loc[financials.index.isin(inital)]

        financials.columns = [int(val.strftime("%Y")) for val in financials.columns.tolist()]
        start = max(financials.columns.tolist())

        financials = financials.dropna(axis=1).T

        for col in inital:
            financials[col] = financials[col]/1000000
        
        financials = financials[inital]

        if financials.index.values.tolist()[0] == start:
            financials = financials.iloc[::-1]
        
        cash = financials.loc[financials.index == start,inital[-3]].values.tolist()[0]
        debt = financials.loc[financials.index == start,inital[-2]].values.tolist()[0]
        shares = financials.loc[financials.index == start,inital[-1]].values.tolist()[0]

        financials = financials.drop(inital[6:],axis=1)

        growth_rates = pd.DataFrame()

        growth_rates.index = financials.index.values-start

        growth_rates[inital[0]] = (financials[inital[0]]/financials[inital[0]].shift(1)).values-1
        growth_rates[inital[1]] = (financials[inital[1]]/financials[inital[0]]).values

        for col in inital[2:6]:
            growth_rates[col] = (financials[col]/financials["EBIAT"]).values

        growth_rates = growth_rates.T
        financials = financials.T

        for i,k in zip(range(0,num_years,1), range(start,start+num_years,1)):
            v = [j for j in range(growth_rates.columns.tolist()[i],i+1,1)]
            growth_rates[i+1] = growth_rates[v].mean(axis=1)
            financials[k+1] = financials[k] * (1+growth_rates[i+1])

        cols1 = financials.columns.tolist()
        cols1 = np.array(cols1[cols1.index(start+1):])

        financials = financials[cols1]

        values = financials.T

        unlevered_fcf = values[inital[1]]-values[inital[2]]+values[inital[3]]-values[inital[4]]-values[inital[5]]

        cols2 = growth_rates.columns.tolist()
        cols2 = np.array(cols2[cols2.index(1):])

        pv_fcf = unlevered_fcf.values/((1+wacc)**cols2)

        tv = round((unlevered_fcf.values.tolist()[-1]*(1+wacc))/(wacc-tgv),1)

        pv_tv = round(tv/((1+wacc)**cols2.flatten().tolist()[-1]),1)

        enterprise_value = round(pv_tv + pv_fcf.sum(),1)

        fair_value = (enterprise_value+cash-debt)/shares

        return round(fair_value,2)

    
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
                             
    def portfolio_volatility(self, ):
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

        tick_compares = TickerData("IWF VTV SPY ^VIX SIZE").get_historical_data(start_date=date).reset_index()

        treasury = pd.read_html("https://www.multpl.com/10-year-treasury-rate/table/by-year")
        devi_ratio = round(tick_compares["^VIX"].std()/tick_compares["SPY"].std(),4)

        stats["BenchmarkReturn"] = percent_change(tick_compares,"SPY")
        stats["RiskFree"] = round(float(treasury[0].iloc[0,1][:-1])/100,4)

        stats["RiskPremium"] = round(stats["BenchmarkReturn"] - stats["RiskFree"],4) 
        stats["GrowthPremium"] = round(percent_change(tick_compares,"IWF")-stats["RiskFree"],4)
        stats["ValuePremium"] = round(percent_change(tick_compares,"VTV")-stats["RiskFree"],4)
        stats["SizePremium"] = round(percent_change(tick_compares,"SIZE")-stats["RiskFree"],4)

        stats["VIX/SPY Corr"] = tick_compares.corr(numeric_only=True).loc["^VIX", "SPY"].round(decimals=4)
        stats["VIX/SPY Beta"] = stats["VIX/SPY Corr"]*devi_ratio

        stats["ExpectedReturn"] = PortfolioAnalytics(date).portfolio_beta()*stats["RiskPremium"]+stats["RiskFree"]

        return pd.DataFrame(stats,index=["Stats"]).T