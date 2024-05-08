import json
import requests
import os
import yfinance as yf

# Click on the file to refer to the criteria set or print it in the test jupyter notebook
criteria = json.loads(open(os.getcwd() + "\\criteria.json","r").read())

tickers = list(criteria["Portfolio Weights"].keys())

for stock_ex in criteria["Exchanges"]:
    github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"
    exchange =  "/" + stock_ex + "/" + stock_ex + "_full_tickers.json" 

    url = github_branch + exchange # combining the repository dataset with the specific exchange

    resp = requests.get(url)
    data = json.loads(resp.text)

    for i in range(len(data)):
        ticker = data[i]

        immediate_criteria = list(criteria["Immediate Criteria"].keys()) # ["lastsale", "volume", "marketCap"]
        
        # important to note that since the list of tickers is massive, need to find any method to narrow scope

        # Step 1: Check to see if anything is blank from the full json file or ticker already in portfolio
        if ticker["symbol"] in tickers or any(ticker[checker] == "" for checker in immediate_criteria): 
            continue

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
                    tickers.append(symbol)

            except KeyError:
                continue

print(tickers)
