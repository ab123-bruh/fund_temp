import pandas as pd
import yfinance as yf
import numpy as np
import requests
import mvdata as mvD
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit

# Ideally these algos are borrowing from methods in engineering applications so methods from thermodynamics
# or other disciplines to determine actions in a time series is what users look for
# need to also use simple indicators so that we are able to bootstrap methods with current avaliable funds

# this one will be more so identifying most important variables to watch for using ML 
# trend is either up or down here
class TrendFollowing:
    def __init__(self):
        pass

    def lstm(self):
        pass


# mostly short term type of trading as this will be used when Hurst under .5
# either over or under bought stock for short term analysis
class MeanReversion:
    def __init__(self, ticker: str):
        self.ticker = ticker

    # use the enhanced method to improve this method 
        # need to build the buy and sell points for the algo
        # get the signal dataframe and return that
        # backtest the algo for performance

        # once that is completed, then use the buy and sell signals from the paper to get 
        # each of the buy and sell signals for the dataset
    def bollinger_bands(self, num_wma_vars: int):
        tick = mvD.TickerData(self.ticker)
        df = tick.get_historical_data()
        df.index = df.index.strftime("%Y-%m-%d")

        adj_close = df.pop("Adj Close")

        wmas = tick.get_technicals("WMA", 20)

        b = np.where(wmas.index == df.index[0])[0].tolist()[0]
        missing_data = wmas.loc[(wmas.index >= wmas.index[b-num_wma_vars]) & (wmas.index < wmas.index[b])]

        wmas = wmas.loc[wmas.index >= df.index[0]]
        wmas.columns = ["WMA_t"]

        for i in range(1,num_wma_vars+1,1):
            wmas["WMA_t-" + str(i)] = wmas["WMA_t"].shift(i).values
            # reverses the order, gets the values, reverses the order again,
            # then finally becomes a list so weird lol
            wmas["WMA_t-" + str(i)].iloc[:i] = missing_data.loc[::-1].iloc[:i].loc[::-1].values.T[0].tolist()
        
        df = pd.concat([df,wmas],axis=1)
        # this value is a day ahead of what it will say on the dataset
        # df["WMA_t-0"].shift(-1) essentially is the next days point in time
        df["Diff"] = df["WMA_t"].shift(-1) - df["WMA_t"]

        # since the next day WMA won't be there, we will have to add some noise to the current one
        # needs to be better modified to allow for a sense of crazy jumps in one day
        mean = df["Diff"].mean()
        temp_kicker = np.random.uniform(low=-mean,high=mean)
        current_point = df["Diff"].iloc[len(df)-2]

        df["Diff"] = df["Diff"].fillna(current_point+temp_kicker)

        # need to fine-tune this for optimal "prediction"
        regr = RandomForestRegressor(max_depth=15, random_state=0)
        tscv = TimeSeriesSplit(n_splits=5)

        predict = []

        for train_index, test_index in tscv.split(df):
            train_split = df.iloc[train_index]
            test_split = df.iloc[test_index]

            features_train = train_split.columns.tolist()
            features_test = test_split.columns.tolist()

            X_train = train_split[features_train[:-1]]
            X_test = test_split[features_test[:-1]]
            y_train = train_split[features_train[-1]]
            y_test = test_split[features_test[-1]]
            
            regr.fit(X_train, y_train)
            
            y_pred = regr.predict(X_test)

            results = {
                "True Values": y_test.values,
                "Predicted Values": y_pred
            }

            results = pd.DataFrame(results,index=y_test.index)

            predict.append(results)
            
        predict = pd.concat(predict)
        test_start = predict.index[0]

        current = df["WMA_t"].loc[df.index >= test_start].values.tolist()

        algo_test = pd.DataFrame(index=predict.index)
        algo_test["Predicted WMA_t+1"] = (predict["Predicted Values"] + current).values

        for sig in ["ATR","SMA"]:
            signal = tick.get_technicals(sig,20)
            algo_test[sig + "_t"] = signal.loc[signal.index >= test_start]
        
        rolling_std = df["Close"].rolling(window=20).std()
        rolling_std = rolling_std.loc[rolling_std.index >= test_start]

        algo_test["Upper Track"] = algo_test["SMA"] + (3*rolling_std)
        algo_test["Lower Track"] = algo_test["SMA"] - (3*rolling_std)

        adj_close = adj_close.loc[adj_close.index >= test_start]

        buy_signal = []
        sell_signal = []

        # for i in range(len(adj_close)):

        # bollinger_band = pd.DataFrame(algo_test.index)
        # bollinger_band[self.ticker + "_Signal"] = mvD.AlgoStats(self.ticker).action_tickers(buy_signal,sell_signal)

        # date = bollinger_band.pop("Date")
        # bollinger_band = bollinger_band.set_index(date)

        # return pd.concat([adj_close,bollinger_band],axis=1)

    def rsi_measure(self):
        tick = mvD.TickerData(self.ticker)

        df = tick.get_historical_data()["Adj Close"]
        rsi = tick.get_technicals("RSI", 14)

        buy_signal = rsi <= 30
        sell_signal = rsi >= 70

        rsi_index = pd.DataFrame(df.index)
        rsi_index[self.ticker + "_Signal"] = mvD.AlgoStats(self.ticker).action_tickers(buy_signal,sell_signal)

        date = rsi_index.pop("Date")
        rsi_index = rsi_index.set_index(date)

        return pd.concat([df,rsi_index],axis=1)
    
    def money_flow_measure(self):
        pass