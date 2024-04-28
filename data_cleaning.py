import json
import requests
import yfinance as yf
import pandas as pd

# Click on the file to refer to the criteria set or print it in the test jupyter notebook
criteria = json.loads(open("criteria.json","r").read())

tickers = []

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
        if ticker[criteria["Metrics"][0]] in list(criteria["Portfolio Weights"].keys()) or any(ticker[checker] == "" for checker in immediate_criteria): 
            continue

        ticker[immediate_criteria[0]] = float(ticker[immediate_criteria[0]][1:])
        ticker[immediate_criteria[1]] = float(ticker[immediate_criteria[1]])
        ticker[immediate_criteria[2]] = float(ticker[immediate_criteria[2]])

        # Step 2: eliminate low cost stocks, less volume, and bound the marketcap due to portfolio size
        check_1 = ticker[immediate_criteria[0]] > criteria["Immediate Criteria"][immediate_criteria[0]] \
            and ticker[immediate_criteria[1]] > criteria["Immediate Criteria"][immediate_criteria[1]]
        check_2 = ticker[immediate_criteria[2]] >= criteria["Immediate Criteria"][immediate_criteria[2]]["min"] \
                         and ticker[immediate_criteria[2]] <= criteria["Immediate Criteria"][immediate_criteria[2]]["max"]

        if check_1 and check_2:
            values = dict(filter(lambda item: item[0] in criteria["Metrics"], 
                                 yf.Ticker(ticker[criteria["Metrics"][0]]).info.items()))
            
            tickers.append(values)
            
# Putting the symbol first for readability purposes
tickers = pd.DataFrame(tickers)

tickers = tickers.dropna(axis=0)

# Convert to numeric to eliminate based on certain conditions
for col in criteria["Metrics"][1:]:
    tickers[col] = pd.to_numeric(tickers[col])
    
# Step 3: eliminate any criteria which we have greater than
portfolio_criteria = list(criteria["Portfolio Criteria"]["Greater"].keys()) 
for column in portfolio_criteria:
    tickers = tickers.loc[tickers[column] > criteria["Portfolio Criteria"]["Greater"][column]]

# Step 4: eliminate any criteria which we have less than
portfolio_criteria = list(criteria["Portfolio Criteria"]["Less Than"].keys()) 
for column in portfolio_criteria:
    tickers = tickers.loc[tickers[column] < criteria["Portfolio Criteria"]["Less Than"][column]]


# Step 5: range of criteria
beta = criteria["Metrics"][2]
beta_min = criteria["Portfolio Criteria"]["beta"]["min"]
beta_max = criteria["Portfolio Criteria"]["beta"]["max"]

tickers = tickers.loc[(tickers[beta] >= beta_min) & (tickers[beta] <= beta_max) 
                      & (tickers[criteria["Metrics"][8]] > tickers[criteria["Metrics"][1]])]

tickers = tickers[criteria["Metrics"]].reset_index(drop=True)

print(tickers[criteria["Metrics"][0]].tolist())
