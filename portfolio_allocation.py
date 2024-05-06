import os
import subprocess
import bt
from datetime import datetime
from datetime import timedelta

tickers = subprocess.run(args=["python", os.getcwd() + "\\data_cleaning.py"],text=True,stdout=subprocess.PIPE)

results = tickers.stdout.strip('""[]\n').split(', ')

symbols = [element.strip("'\"") for element in results]

start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

print(bt.get(symbols,start=start))
