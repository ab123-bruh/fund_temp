import json
import os
import requests
import yfinance as yf

criteria = json.loads(open(os.getcwd() + "\\criteria.json","r").read())
  
class Basket:
    def __init__(self):
        self.portfolio = criteria["Portfolio Weights"]
        
    def get_portfolio(self):
        return self.portfolio
    
    def update_portfolio(self, key: str, value: float):
        values = list(self.portfolio.values())
        if sum(values) + value > 1:
            raise ValueError("Max for current portfolio is " + str(1-sum(values)) + " based on current portfolio.")
        elif key in list(self.portfolio.keys()):
            self.portfolio.update({key: value})
        else:
            self.portfolio[key] = value
            
    def remove_ticker(self, key: str):
        try:
            del self.portfolio[key]
        except KeyError:
            print("This ticker was not in the portfolio.")

class Ticker:
    def __init__(self):
        self.github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"
        self.exchanges = criteria["Exchanges"]
    
    def get_all_tickers(self):
        tickers = {}

        for stock_ex in self.exchanges:
            exchange =  "/" + stock_ex + "/" + stock_ex + "_tickers.txt"
            resp = requests.get(self.github_branch + exchange)
            data = resp.text.split("\n")
            tickers[stock_ex] = data
        
        return tickers
    
    def shortlist_tickers(self):
        new_tickers = []

        for stock_ex in self.exchanges:
            exchange =  "/" + stock_ex + "/" + stock_ex + "_full_tickers.json" 

            url = self.github_branch + exchange # combining the repository dataset with the specific exchange

            resp = requests.get(url)
            data = json.loads(resp.text)

            for i in range(len(data)):
                ticker = data[i]

                check_1 = ticker["symbol"] in list(Basket().get_portfolio().keys())
                check_2 = any(ticker[checker] == "" for checker in list(criteria["Immediate Criteria"].keys()))
                
                # important to note that since the list of tickers is massive, need to find any method to narrow scope

                if check_1 or check_2: 
                    continue

                # numeric comparison
                lastsale = float(ticker["lastsale"][1:])
                volume = float(ticker["volume"])
                marketCap = float(ticker["marketCap"])

                check_3 = lastsale > criteria["Immediate Criteria"]["lastsale"] and \
                    volume > criteria["Immediate Criteria"]["volume"]
                    
                check_4 = marketCap <= criteria["Immediate Criteria"]["marketCap"]

                if check_3 and check_4:
                     new_tickers.append(ticker["symbol"])
            
        return new_tickers

    def recommend_tickers(self):
        tickers = Ticker().shortlist_tickers()
        new_tickers = []

        greater = criteria["Portfolio Criteria"]["Greater"]
        less_than = criteria["Portfolio Criteria"]["Less Than"]
        
        # list of metrics for criteria
        metrics = list(greater.keys())
        metrics.extend(list(less_than.keys()))

        for ticker in tickers:
            values = dict(filter(lambda item: item[0] in metrics, yf.Ticker(ticker).info.items()))
            
            try:
                check_3 = all(values[metric] > x for metric,x in greater.items()) 
                check_4 = all(values[metric] < x for metric,x in less_than.items())
                if check_3 and check_4:
                    new_tickers.append(ticker)

            except KeyError:
                continue

        return new_tickers

# Will be uncommented once its usable

# class DataClean:
#     def __init__(self, symbols: list):
#         self.symbols = symbols
    
#     def add_multiple_tickers(self, tickers: list):
#         pass
    
#     def get_historical_data(self, period: str):
#         self.symbols.extend(DataClean().add_multiple_tickers())

#         return yf.download(tickers=self.symbols,period=period)