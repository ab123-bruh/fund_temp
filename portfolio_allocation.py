import json
import os
import requests
import yfinance as yf

class Ticker:
    def __init__(self):
        self.criteria = json.loads(open(os.getcwd() + "\\criteria.json","r").read())
        self.github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"
    
    def get_all_tickers(self,NYSE=True,AMEX=True,NASDAQ=True):
        exchanges = self.criteria["Exchanges"]

        get_exchanges = [NYSE,NASDAQ,AMEX]

        tickers = []

        for stock_ex, check_exchange in zip(exchanges,get_exchanges):
            if check_exchange:
                exchange =  "/" + stock_ex + "/" + stock_ex + "_tickers.txt"
                resp = requests.get(self.github_branch + exchange).text.split("\n")
                tickers.extend(resp)

        tickers.sort()
        
        return tickers
    
    def get_portfolio_tickers(self):
        return list(self.criteria["Portfolio Weights"].keys())
    
    def add_portfolio_tickers(self, key: str, value: float):
        portfolio = self.criteria["Portfolio Weights"]
        portfolio[key] = value
    
    def remove_portfolio_tickers(self):
        pass
    
    def shortlist_tickers(self):
        new_tickers = []

        for stock_ex in self.criteria["Exchanges"]:
            exchange =  "/" + stock_ex + "/" + stock_ex + "_full_tickers.json" 

            url = self.github_branch + exchange # combining the repository dataset with the specific exchange

            resp = requests.get(url)
            data = json.loads(resp.text)

            for i in range(len(data)):
                ticker = data[i]

                immediate_criteria = list(self.criteria["Immediate Criteria"].keys()) # ["lastsale", "volume", "marketCap"]
                
                # important to note that since the list of tickers is massive, need to find any method to narrow scope

                # Step 1: Check to see if anything is blank from the full json file or ticker already in portfolio
                if ticker["symbol"] in Ticker().get_portfolio_tickers() or \
                      any(ticker[checker] == "" for checker in immediate_criteria): continue

                # numeric comparison
                lastsale = float(ticker[immediate_criteria[0]][1:])
                volume = float(ticker[immediate_criteria[1]])
                marketCap = float(ticker[immediate_criteria[2]])

                # Step 2: eliminate low cost stocks, less volume, and bound the marketcap due to portfolio size
                check_1 = lastsale > self.criteria["Immediate Criteria"][immediate_criteria[0]] \
                    and volume > self.criteria["Immediate Criteria"][immediate_criteria[1]]
                    
                check_2 = marketCap <= self.criteria["Immediate Criteria"][immediate_criteria[2]]

                if check_1 and check_2:
                     new_tickers.append(ticker["symbol"])
            
        return new_tickers

    def recommended_tickers(self):
        new_tickers = Ticker().shortlist_tickers()

        greater = self.criteria["Portfolio Criteria"]["Greater"]
        less_than = self.criteria["Portfolio Criteria"]["Less Than"]
        
        # list of metrics for criteria
        metrics = list(greater.keys())
        metrics.extend(list(less_than.keys()))

        for ticker in new_tickers:
            values = dict(filter(lambda item: item[0] in metrics, yf.Ticker(ticker).info.items()))
            
            try:
                # Step 3: select tickers whick satisfy all of these conditions
                check_3 = all(values[metric] > x for metric,x in greater.items()) 
                check_4 = all(values[metric] < x for metric,x in less_than.items())
                if check_3 and check_4:
                    continue
                else:
                    new_tickers.remove(ticker)

            except KeyError:
                continue

        return new_tickers


tickers = Ticker().get_portfolio_tickers()

tickers.extend(Ticker().recommended_tickers())

print(tickers)