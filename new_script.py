import json
import os
import requests
import yfinance as yf
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

criteria = json.loads(open(os.getcwd() + "\\criteria.json","r").read())

github_branch = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main"

tickers = {}

for stock_ex in criteria["Exchanges"]:
    exchange =  "/" + stock_ex + "/" + stock_ex + "_full_tickers.json"
    resp = requests.get(github_branch + exchange)
    tickers[stock_ex] = json.loads(resp.text)

print(tickers["amex"][0])