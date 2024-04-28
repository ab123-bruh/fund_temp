import os
import subprocess

tickers = subprocess.run(args=["python", os.getcwd() + "\\data_cleaning.py"],text=True,stdout=subprocess.PIPE)

results = tickers.stdout.strip('""[]\n').split(', ')

symbols = [element.strip("'\"") for element in results]

print(symbols)
