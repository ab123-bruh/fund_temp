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
        if key not in list(self.portfolio.keys()):
            raise KeyError("The key needs to be added to the portfolio first.")

        # self.portfolio.update
    
    def add_portfolio(self, key: str, value: float):
        values = sum(list(self.portfolio.values()))

        if key in list(self.portfolio.keys()):
            raise KeyError(key + "is already in portfolio. If you want to change the weight, update portfolio instead.")
        elif values + value > 1:
            raise ValueError("The max value you can add is " + str(1-values) + " based on current portfolio.")

        self.portfolio[key] = value
    
    def remove_portfolio(self, key: str):
        try:
            del self.portfolio[key]
        except KeyError:
            pass

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

                check_1 = lastsale > self.criteria["Immediate Criteria"][immediate_criteria[0]] \
                    and volume > self.criteria["Immediate Criteria"][immediate_criteria[1]]
                    
                check_2 = marketCap <= self.criteria["Immediate Criteria"][immediate_criteria[2]]

                if check_1 and check_2:
                     new_tickers.append(ticker["symbol"])
            
        return new_tickers

    def recommend_tickers(self):
        new_tickers = []

        greater = criteria["Portfolio Criteria"]["Greater"]
        less_than = criteria["Portfolio Criteria"]["Less Than"]
        
        # list of metrics for criteria
        metrics = list(greater.keys())
        metrics.extend(list(less_than.keys()))

        for ticker in Ticker().shortlist_tickers():
            values = dict(filter(lambda item: item[0] in metrics, yf.Ticker(ticker).info.items()))
            
            try:
                check_3 = all(values[metric] > x for metric,x in greater.items()) 
                check_4 = all(values[metric] < x for metric,x in less_than.items())
                if check_3 and check_4:
                    new_tickers.append(ticker)

            except KeyError:
                new_tickers.remove(ticker)

        return new_tickers