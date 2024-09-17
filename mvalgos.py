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


# mostly short term type of trading as this will be used when Hurst under .45 (from .45 to .55 not as reasonable)
# either over or under bought stock for short term analysis
class MeanReversion:
    def __init__(self, ticker: str):
        self.ticker = ticker
    
    def rsi_measure(self):
        tick = mvD.EquitiesData(self.ticker)

        df = tick.get_historical_data()["Adj Close"]
        rsi = tick.get_technicals("RSI", 14)

        buy_signal = rsi <= 30
        sell_signal = rsi >= 70

        rsi_index = pd.DataFrame(df.index)
        rsi_index[self.ticker + "_Signal"] = mvD.AlgoStats(self.ticker).action_tickers(buy_signal,sell_signal)

        date = rsi_index.pop("Date")
        rsi_index = rsi_index.set_index(date)

        return pd.concat([df,rsi_index],axis=1)

    def bollinger_bands(self, past_days: int):
        tick = mvD.EquitiesData(self.ticker)
        df = tick.get_historical_data()
        df.index = df.index.strftime("%Y-%m-%d")

        adj_close = df.pop("Adj Close")

        wmas = tick.get_technicals("WMA", 20)

        b = np.where(wmas.index == df.index[0])[0].tolist()[0]
        missing_data = wmas.loc[(wmas.index >= wmas.index[b-past_days]) & (wmas.index < wmas.index[b])]
        # reversing order
        missing_data = missing_data.loc[::-1]

        wmas = wmas.loc[wmas.index >= df.index[0]]
        wmas.columns = ["WMA_t"]

        for i in range(1,past_days+1,1):
            wmas["WMA_t-" + str(i)] = wmas["WMA_t"].shift(i).values
            # gets the values, reverses the order again, then finally becomes a list so weird lol
            wmas["WMA_t-" + str(i)].iloc[:i] = missing_data.iloc[:i].loc[::-1].values.T[0].tolist()
        
        df = pd.concat([df,wmas],axis=1)
        # this value is a day ahead of what it will say on the dataset
        # df["WMA_t-0"].shift(-1) essentially is the next days point in time
        # but it shows as if its the current point in time in the dataset
        df["Diff"] = df["WMA_t"].shift(-1) - df["WMA_t"]

        # since the next day WMA won't be there, we will have to add some noise to the current one
        # needs to be better modified to allow for a sense of crazy jumps in one day
        temp_kicker = np.random.normal(loc=df["Diff"].mean(),scale=df["Diff"].std())
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

        position = 0
        buy_signal = []
        sell_signal = []

        for i in range(len(adj_close)):
            state_i = algo_test.iloc[i].to_dict()
            state_i["Price"] = adj_close.iloc[i]

            if position != 0:
                if state_i["Predicted WMA_t+1"] < position - (2 * state_i["ATR_t"]):
                    buy_position = False
                    sell_position = True
                    position = 0
                elif state_i["Predicted WMA_t+1"] >= state_i["Upper Track"]:
                    buy_position = False
                    sell_position = True
                    position = 0
                elif state_i["Predicted WMA_t+1"] > position + (2 * state_i["ATR_t"]):
                    buy_position = False
                    sell_position = True
                    position = 0
            elif position == 0:
                if state_i["Predicted WMA_t+1"] <= state_i["Lower Track"]:
                    buy_position = True
                    sell_position = False
                    position = state_i["Price"]
                elif state_i["Predicted WMA_t+1"] < state_i["Price"] - (2 * state_i["ATR_t"]):
                    buy_position = True
                    sell_position = False
                    position = state_i["Price"]
            else:
                buy_position = False
                sell_position = False        
            
            buy_signal.append(buy_position)
            sell_signal.append(sell_position)
        
        buy_signal = pd.DataFrame(buy_signal,index=adj_close.index,columns=[self.ticker])
        sell_signal = pd.DataFrame(sell_signal,index=adj_close.index,columns=[self.ticker])

        bollinger_band = pd.DataFrame(algo_test.index)
        bollinger_band[self.ticker + "_Signal"] = mvD.AlgoStats(self.ticker).action_tickers(buy_signal,sell_signal)

        date = bollinger_band.pop("Date")
        bollinger_band = bollinger_band.set_index(date)

        return pd.concat([adj_close,bollinger_band],axis=1)

    def money_flow_measure(self):
        pass