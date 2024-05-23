import json
import os
import requests
import yfinance as yf
import numpy as np

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
        self.file =  "_full_tickers.json"
    
    def get_all_tickers(self):
        tickers = {}

        for stock_ex in self.exchanges:
            exchange =  "/" + stock_ex + "/" + stock_ex + self.file
            resp = requests.get(self.github_branch + exchange)
            tickers[stock_ex] = json.loads(resp.text)
        
        return tickers
    
    def shortlist_tickers(self):
        tickers = Ticker().get_all_tickers()
        new_tickers = []

        crit = list(criteria["Immediate Criteria"].keys())

        for stock_ex in self.exchanges:
            data = tickers[stock_ex]

            ticker_data = []
            metric_data = {metric: [] for metric in crit}

            for tick_val in data:
                check_1 = tick_val["symbol"] in list(Basket().get_portfolio().keys())
                check_2 = any(tick_val[checker] == "" for checker in crit)

                if check_1 or check_2:
                    continue
                
                lastsale = float(tick_val[crit[0]][1:])
                volume = float(tick_val[crit[1]])
                marketCap = float(tick_val[crit[2]])

                ticker_data.append(tick_val["symbol"])
                
                # loop unrolling to save time here
                metric_data[crit[0]].append(lastsale)
                metric_data[crit[1]].append(volume)
                metric_data[crit[2]].append(marketCap)
                        
            metric_arrays = {metric: np.array(values) for metric, values in metric_data.items()}
            
            check_3 = np.ones(len(ticker_data), dtype=bool)
            check_4 = np.ones(len(ticker_data), dtype=bool)

            check_3 &= metric_arrays[crit[0]] > criteria["Immediate Criteria"][crit[0]]
            check_3 &= metric_arrays[crit[1]] > criteria["Immediate Criteria"][crit[1]]

            check_4 &= metric_arrays[crit[2]] < criteria["Immediate Criteria"][crit[2]]

            final_check = check_3 & check_4

            ticker_data = np.array(ticker_data)[final_check].tolist()

            new_tickers.extend(ticker_data)
        
        new_tickers = [tick.replace("/",".") for tick in new_tickers if "^" not in tick]

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


print(Ticker().recommend_tickers())
