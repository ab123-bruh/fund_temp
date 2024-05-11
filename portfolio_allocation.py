import json
import os
import requests
import yfinance as yf

class Criteria:
    def __init__(self):
        self.criteria = json.loads(open(os.getcwd() + "\\criteria.json","r").read())
    
    def add_criteria(self, key, value):
        self.criteria[key] = value
    
    def remove_criteria(self):
        pass
    
    def get_criteria(self):
        return self.criteria


class Ticker:
    def __init__(self):
        self.github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"
    
    def get_all_tickers(self,NYSE=True,AMEX=True,NASDAQ=True):
        exchanges = ["nyse", "nasdaq", "amex"]

        get_exchanges = [NYSE,NASDAQ,AMEX]

        tickers = []

        for stock_ex, check_exchange in zip(exchanges,get_exchanges):

            if check_exchange:
                exchange =  "/" + stock_ex + "/" + stock_ex + "_tickers.txt"
                resp = requests.get(self.github_branch + exchange).text.split("\n")
                tickers.extend(resp)

        tickers.sort()
        
        return tickers
    
    def portfolio_tickers(self):
        return list(self.criteria["Portfolio Weights"].keys())

    def recommended_tickers(self):
        criteria = Criteria().get_criteria()
        
        new_tickers = []

        for stock_ex in self.criteria["Exchanges"]:
            exchange =  "/" + stock_ex + "/" + stock_ex + "_full_tickers.json" 

            url = self.github_branch + exchange # combining the repository dataset with the specific exchange

            resp = requests.get(url)
            data = json.loads(resp.text)

            for i in range(len(data)):
                ticker = data[i]

                immediate_criteria = list(criteria["Immediate Criteria"].keys()) # ["lastsale", "volume", "marketCap"]
                
                # important to note that since the list of tickers is massive, need to find any method to narrow scope

                # Step 1: Check to see if anything is blank from the full json file or ticker already in portfolio
                if ticker["symbol"] in Ticker().portfolio_tickers() or \
                      any(ticker[checker] == "" for checker in immediate_criteria): continue

                # numeric comparison
                lastsale = float(ticker[immediate_criteria[0]][1:])
                volume = float(ticker[immediate_criteria[1]])
                marketCap = float(ticker[immediate_criteria[2]])

                # Step 2: eliminate low cost stocks, less volume, and bound the marketcap due to portfolio size
                check_1 = lastsale > criteria["Immediate Criteria"][immediate_criteria[0]] \
                    and volume > criteria["Immediate Criteria"][immediate_criteria[1]]
                    
                check_2 = marketCap >= criteria["Immediate Criteria"][immediate_criteria[2]]["min"] \
                                and marketCap <= criteria["Immediate Criteria"][immediate_criteria[2]]["max"]

                if check_1 and check_2:
                    greater = criteria["Portfolio Criteria"]["Greater"]
                    less_than = criteria["Portfolio Criteria"]["Less Than"]

                    symbol = ticker["symbol"]

                    # list of metrics for criteria
                    metrics = list(greater.keys())
                    metrics.extend(list(less_than.keys()))

                    values = dict(filter(lambda item: item[0] in metrics, yf.Ticker(symbol).info.items()))
                    
                    try:
                        # Step 3: select tickers whick satisfy all of these conditions
                        check_3 = all(values[metric] > x for metric,x in greater.items()) 
                        check_4 = all(values[metric] < x for metric,x in less_than.items())
                        if check_3 and check_4:
                            new_tickers.append(symbol)

                    except KeyError:
                        continue
        
        return new_tickers



print(len(Ticker().get_all_tickers()))