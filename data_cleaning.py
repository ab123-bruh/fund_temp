import json
import requests
import yfinance as yf
import pandas as pd

exchanges = ["nyse", "nasdaq", "amex"] # US Stock Exchanges

metric_evaluation = ["symbol", "currentPrice", "beta", "revenueGrowth", "priceToBook", "debtToEquity", "profitMargins", 
                     "quickRatio", "fiftyDayAverage", "pegRatio"]

tickers = []

for stock_ex in exchanges:
    github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"
    exchange =  "/" + stock_ex + "/" + stock_ex + "_full_tickers.json" 

    url = github_branch + exchange # combining the repository dataset with the specific exchange

    resp = requests.get(url)
    data = json.loads(resp.text)

    for i in range(len(data)):
        ticker = data[i]

        # important to note that since the list of tickers is massive, need to find any method to narrow scope

        # Step 1: Check to see if anything is blank from the full json file
        if ticker["lastsale"] == "" or ticker["volume"] == "" or ticker["marketCap"] == "":
            continue

        ticker["lastsale"] = float(ticker["lastsale"][1:])
        ticker["volume"] = float(ticker["volume"])
        ticker["marketCap"] = float(ticker["marketCap"])

        # Step 2: eliminate low cost stocks, less volume, and bound the marketcap due to portfolio size
        check_1 = ticker["lastsale"] > 5 and ticker["volume"] > 200000
        check_2 = ticker["marketCap"] >= 2000000000 and ticker["marketCap"] <= 15000000000

        if check_1 and check_2:
            values = dict(filter(lambda item: item[0] in metric_evaluation, 
                                 yf.Ticker(ticker[metric_evaluation[0]]).info.items()))
            
            tickers.append(values)
            
# Putting the symbol first for readability purposes
tickers = pd.DataFrame(tickers)

tickers = tickers.dropna(axis=0)

# Convert to numeric to eliminate based on certain conditions
for col in metric_evaluation[1:]:
    tickers[col] = pd.to_numeric(tickers[col])
    

# Step 3: eliminate any criteria which is greater or less than right away so we have a smaller dataset 
#         which this was started in the first check of seeing if latest price less than 50 day moving average
tickers = tickers.loc[(tickers[metric_evaluation[3]] > .05) & (tickers[metric_evaluation[4]] < 12) 
                      & (tickers[metric_evaluation[5]] < 100) & (tickers[metric_evaluation[6]] > .15) 
                      & (tickers[metric_evaluation[7]] > 1) & (tickers[metric_evaluation[8]] > tickers[metric_evaluation[1]])
                      & (tickers[metric_evaluation[9]] < 5)]

# Step 4: out of the eliminated criteria from previous, take beta between .5 & 1.5
tickers = tickers.loc[(tickers[metric_evaluation[2]] >= .5) & (tickers[metric_evaluation[2]] <= 1.5)]

tickers = tickers[metric_evaluation].reset_index(drop=True)

print(tickers["symbol"].tolist())
