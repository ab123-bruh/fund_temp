import json
import requests
import yfinance as yf
import pandas as pd


exchanges = ["nyse", "nasdaq", "amex"] # US Stock Exchanges

tickers = []

for stock_ex in exchanges:
    github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"
    exchange =  "/" + stock_ex + "/" + stock_ex + "_full_tickers.json" 

    url = github_branch + exchange # combining the repository dataset with the specific exchange

    resp = requests.get(url)
    data = json.loads(resp.text)

    for i in range(len(data)):
        ticker = data[i]

        # important to note that since the list of tickers is massive, need to find any method to narrow the scope

        # Step 1: Check to see if anything is blank from the full json file
        if ticker["lastsale"] == "" or ticker["volume"] == "" or ticker["marketCap"] == "":
            continue
        
        # Step 2: eliminate low cost stocks, less volume, and bound the marketcap due to portfolio size
        a = float(ticker["lastsale"][1:]) > 10 and float(ticker["volume"]) > 200000
        b = float(ticker["marketCap"]) >= 2000000000 and float(ticker["marketCap"]) <= 15000000000

        if a and b:
            # Step 3: gather data of specific metrics which we will use to eliminate any that don't fit in criteria
            #         and if any of these are missing, they are automatically eliminated from our scope 
            metric_evaluation = ["symbol", "beta", "revenueGrowth", "priceToBook", "debtToEquity", 
                                 "profitMargins", "quickRatio", "fiftyDayAverage", "pegRatio"]
            
            try:
                tick = pd.DataFrame(yf.Ticker(ticker["symbol"]).info)[metric_evaluation].drop_duplicates()
                tickers.append(tick)
            except:
                continue
    
tickers = pd.concat(tickers,axis=0).reset_index(drop=True)

print(tickers) # this currently takes too long to process. need to make it shorter
