import pandas as pd
import yfinance as yf
import numpy as np
import requests
import json
from concurrent.futures import ThreadPoolExecutor

# need to add the code to get the portfolio data from the broker
# also need to see if the broker can provide us with historical intraday data 
    # this would go back to one year 
    # intraday 1min data as that is a massive sample size


class RecommendTicker:
    def __init__(self):
        self.github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"
        self.exchanges = ["nyse", "nasdaq", "amex"]
    
    def get_tickers(self):
        tickers = []

        for stock_ex in self.exchanges:
            exchange =  "/" + stock_ex + "/" + stock_ex +  "_full_tickers.json"
            resp = requests.get(self.github_branch + exchange)
            tickers.append(pd.DataFrame(json.loads(resp.text)))

        tickers = pd.concat(tickers,axis=0)

        tickers["lastsale"] = tickers["lastsale"].str[1:].astype(float).round(decimals=2)
        tickers["volume"] = tickers["volume"].astype(int)

        # Some of them were null so slapped zero since we are not using them
        tickers["marketCap"] = tickers["marketCap"].replace('','0.0').astype(float)
        tickers = tickers.sort_values(by="symbol").reset_index(drop=True)

        return tickers

    def shortlist_tickers(self):
        metrics = ['quoteType','beta', 'profitMargins', 'priceToBook', 'trailingEps', 'forwardEps', 'quickRatio', 
                   'currentRatio', 'debtToEquity', 'returnOnEquity', 'enterpriseToRevenue', 'revenueGrowth']
        
        def get_info(ticker: str):
            value = {}
            try:
                value[ticker] = dict(filter(lambda item: item[0] in metrics, 
                                            yf.Ticker(ticker).info.items()))
            except:
                value[ticker] = {}
            
            return value

        tickers = RecommendTicker().get_tickers()

        tickers = tickers.drop(["url"],axis=1)
        tickers = tickers.loc[(tickers["marketCap"] < 2000000000) & (tickers["lastsale"] > 5) 
                              & (tickers["volume"] > 200000) & (tickers["industry"] != '') 
                              & (tickers["sector"] != '')]
        
        with ThreadPoolExecutor() as executor:
            ticker_data = list(executor.map(get_info, tickers["symbol"].tolist()))
        
        metric_values = {metric: [] for metric in metrics}
        
        new_tickers = []

        for ticker in ticker_data:
            tick = list(ticker.keys())[0]
            new_tickers.append(tick)
            for metric in metrics:
                value = ticker[tick].get(metric, np.nan)
                metric_values[metric].append(value)
        
        metric_arrays = {metric: np.array(values) for metric, values in metric_values.items()}

        tickers = pd.concat([tickers,pd.DataFrame(metric_arrays)],axis=1).dropna()
        
        return tickers