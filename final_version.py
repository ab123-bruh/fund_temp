import json
import requests
import yfinance

exchanges = ["nyse", "nasdaq", "amex"]

tickers = []

for stock_ex in exchanges:
    github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"
    exchange =  "/" + stock_ex + "/" + stock_ex + "_full_tickers.json" 

    url = github_branch + exchange

    resp = requests.get(url)
    data = json.loads(resp.text)

    for i in range(len(data)):
        ticker = data[i]

        if ticker["lastsale"] == "" or ticker["volume"] == "" or ticker["marketCap"] == "":
            continue

        a = float(ticker["lastsale"][1:]) > 10 and float(ticker["volume"]) > 200000
        b = float(ticker["marketCap"]) >= 10000000000 and float(ticker["marketCap"]) <= 15000000000

        if a and b:
            tickers.append(ticker["symbol"])

print(len(tickers)) # this currently returns a list that is too large. need to probably squeeze the margin tighter
