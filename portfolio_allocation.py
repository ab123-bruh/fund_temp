import os
import subprocess
import bt
import datetime as dt
import numpy as np

tickers = subprocess.run(args=["python", os.getcwd() + "\\data_cleaning.py"],text=True,stdout=subprocess.PIPE)

results = tickers.stdout.strip('""[]\n').split(', ')

symbols = [element.strip("'\"") for element in results]

current_date = dt.date.today()
start_date = current_date - dt.timedelta(days=365)
start = (start_date - dt.timedelta(days=round((1.5*50)-1,0)))

if start.isoweekday() == 6:
    start = start - dt.timedelta(days=1)
elif start.isoweekday() == 7:
    start = start + dt.timedelta(days=1)

df = bt.get(symbols,start=start.strftime("%Y-%m-%d"))

df_filter = (df - df.loc[df.index == start_date.strftime("%Y-%m-%d")].values)

highest = df_filter.loc[df_filter.index >= start_date.strftime("%Y-%m-%d")].max()
lowest = df_filter.loc[df_filter.index >= start_date.strftime("%Y-%m-%d")].min()

norm_price = ((df_filter - lowest)/(highest - lowest))*(2*np.pi)

rolling_mean = norm_price.rolling(window=50).mean()
rolling_std = norm_price.rolling(window=50).std()

buy_signal = norm_price < rolling_mean - (2 * rolling_std)
sell_signal = norm_price > rolling_mean + (2 * rolling_std)

buy_signal = buy_signal.loc[buy_signal.index >= start_date.strftime("%Y-%m-%d")]
sell_signal = sell_signal.loc[sell_signal.index >= start_date.strftime("%Y-%m-%d")]

strat = bt.Strategy('tailAction', [bt.algos.SelectWhere(buy_signal), 
                                   bt.algos.SelectWhere(sell_signal),
                                   bt.algos.WeighRandomly(),
                                   bt.algos.Rebalance()])

# now we create the Backtest
t = bt.Backtest(strat, df.loc[df.index >= start_date.strftime("%Y-%m-%d")])

# and let's run it!
res = bt.run(t)

res.plot()