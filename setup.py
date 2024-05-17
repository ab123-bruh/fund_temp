import json
import os
import requests
import yfinance as yf

criteria = json.loads(open(os.getcwd() + "\\criteria.json","r").read())
  
class Basket:
    def __init__(self):
        self.portfolio = criteria["Portfolio Weights"]
        self.tickers = list(self.portfolio.keys())
        self.values = list(self.portfolio.values())
        
    def get_portfolio(self):
        return self.portfolio
    
    def update_portfolio(self, key: str, value: float):
        if sum(self.values) + value > 1:
            raise ValueError("Max for current portfolio is " + str(1-sum(self.values)) + " based on current portfolio.")
        elif key in self.tickers:
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
    
    def get_all_tickers(self):
        exchanges = criteria["Exchanges"]

        tickers = []

        for stock_ex in exchanges:
            exchange =  "/" + stock_ex + "/" + stock_ex + "_tickers.txt"
            resp = requests.get(self.github_branch + exchange).text.split("\n")
            tickers.extend(resp)

        tickers.sort()
        
        return tickers
    
    def shortlist_tickers(self):
        new_tickers = []

        for stock_ex in criteria["Exchanges"]:
            exchange =  "/" + stock_ex + "/" + stock_ex + "_full_tickers.json" 

            url = self.github_branch + exchange # combining the repository dataset with the specific exchange

            resp = requests.get(url)
            data = json.loads(resp.text)

            for i in range(len(data)):
                ticker = data[i]

                immediate_criteria = list(criteria["Immediate Criteria"].keys()) # ["lastsale", "volume", "marketCap"]
                
                # important to note that since the list of tickers is massive, need to find any method to narrow scope

                if ticker["symbol"] in Basket().get_portfolio() or \
                      any(ticker[checker] == "" for checker in immediate_criteria): continue

                # numeric comparison
                lastsale = float(ticker[immediate_criteria[0]][1:])
                volume = float(ticker[immediate_criteria[1]])
                marketCap = float(ticker[immediate_criteria[2]])

                check_1 = lastsale > criteria["Immediate Criteria"][immediate_criteria[0]] \
                    and volume > criteria["Immediate Criteria"][immediate_criteria[1]]
                    
                check_2 = marketCap <= criteria["Immediate Criteria"][immediate_criteria[2]]

                if check_1 and check_2:
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