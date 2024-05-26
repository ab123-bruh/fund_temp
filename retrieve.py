import json
import os
import requests
import yfinance as yf
import numpy as np
from concurrent.futures import ThreadPoolExecutor

criteria = json.loads(open(os.getcwd() + "\\criteria.json","r").read())
  
class Basket:
    def __init__(self):
        self.portfolio = criteria["Portfolio Weights"]
        self.greater = criteria["Portfolio Criteria"]["Greater"]
        self.less_than = criteria["Portfolio Criteria"]["Less Than"]
        
    def get_portfolio(self):
        return self.portfolio
    
    def get_immediate_criteria(self):
        return criteria["Immediate Criteria"]
    
    def get_greater_criteria(self):
        return self.greater

    def get_less_criteria(self):
        return self.less_than
    
    def get_metrics(self):
        return list(self.greater.keys()) + list(self.less_than.keys())
        
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

class GetTicker:
    def __init__(self):
        self.github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"
        self.exchanges = criteria["Exchanges"]
        self.file =  "_full_tickers.json"
    
    def get_all_tickers(self,symbol_only=False):
        tickers = {}

        for stock_ex in self.exchanges:
            exchange =  "/" + stock_ex + "/" + stock_ex + self.file
            resp = requests.get(self.github_branch + exchange)
            tickers[stock_ex] = json.loads(resp.text)

        if symbol_only is True:
            return [tickers[stock_ex][i]["symbol"] for stock_ex, i in zip(self.exchanges, range(len(tickers)))]
        
        return tickers
    
    def shortlist_tickers(self):
        tickers = GetTicker().get_all_tickers()
        new_tickers = []

        crit = list(Basket().get_immediate_criteria().keys())

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
    
    def get_yahoo_info(self,ticker: str):
        metrics = Basket().get_metrics()
        try:
            value = {ticker: dict(filter(lambda item: item[0] in metrics, yf.Ticker(ticker).info.items()))}
        except:
            value = {ticker: {}}
        
        return value

    def recommend_tickers(self):
        tickers = GetTicker().shortlist_tickers()
        metrics = Basket().get_metrics()

        with ThreadPoolExecutor() as executor:
            ticker_data = list(executor.map(GetTicker().get_yahoo_info, tickers))
        
        ticker_data = [e for e in ticker_data if len(list(e[list(e.keys())[0]].keys())) == len(metrics)]
        
        metric_values = {metric: [] for metric in metrics}

        new_tickers = []

        for ticker in ticker_data:
            tick = list(ticker.keys())[0]
            new_tickers.append(tick)
            for metric in metrics:
                value = ticker[tick].get(metric, np.nan)
                metric_values[metric].append(value)
        
        metric_arrays = {metric: np.array(values) for metric, values in metric_values.items()}

        # Create boolean arrays for the conditions
        check_3 = np.ones(len(new_tickers), dtype=bool)
        check_4 = np.ones(len(new_tickers), dtype=bool)

        for metric, x in Basket().get_greater_criteria().items():
            check_3 &= metric_arrays[metric] > x

        for metric, x in Basket().get_less_criteria().items():
            check_4 &= metric_arrays[metric] < x
            
        # Combine the conditions
        final_check = check_3 & check_4

        # Get the final list of tickers that meet the conditions
        new_tickers = np.array(new_tickers)[final_check].tolist()
        
        return new_tickers