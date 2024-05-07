import os
import subprocess
import bt
import datetime as dt

tickers = subprocess.run(args=["python", os.getcwd() + "\\data_cleaning.py"],text=True,stdout=subprocess.PIPE)

results = tickers.stdout.strip('""[]\n').split(', ')

symbols = [element.strip("'\"") for element in results]

current_date = dt.date.today()
start_date = current_date - dt.timedelta(days=365)

num_previous_trading_days = sum(1 for day in range((current_date - start_date).days + 1) if (start_date + dt.timedelta(days=day)).weekday() < 5)

days = round((1.9*num_previous_trading_days)-1,0)

start = (current_date - dt.timedelta(days=days)).strftime("%Y-%m-%d")

df = bt.get(symbols,start=start)
