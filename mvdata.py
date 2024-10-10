import pandas as pd
import yfinance as yf
import numpy as np
import requests
import datetime as dt

# change this to EquitiesData
class EquitiesData:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.rapid_api_key = ""
            
    def get_historical_data(self):
        start_date = (dt.datetime.today() - pd.DateOffset(years=5)).strftime("%Y-%m-%d")
        df = yf.download(self.ticker,start=start_date)

        return df
    
    def options_flow(self):
        options = {}
        flow = yf.Ticker(self.ticker).option_chain() 

        options["Call"] = flow.calls
        options["Put"] = flow.puts

        return options
    
    def get_intraday_data(self, time: str, same_day: bool):
        if time not in ["1min","5min","15min","30min","60min"]:
            raise ValueError("Invalid API call. Retry or visit https://www.alphavantage.co/documentation/ for valid calls")

        querystring = {
            "symbol": self.ticker,
            "function":"TIME_SERIES_INTRADAY",
            "interval": time,
            "outputsize": "full"
        }

        headers = {
            "x-rapidapi-key": self.rapid_api_key,
            "x-rapidapi-host": "alpha-vantage.p.rapidapi.com"
        }

        url = "https://" + headers["x-rapidapi-host"] + "/query"

        response = requests.get(url, headers=headers, params=querystring).json()

        df = pd.DataFrame(response["Time Series (" + time + ")"]).T

        df.columns = ["Open", "High", "Low", "Close", "Volume"]

        if same_day:
            day = dt.datetime.today().strftime("%Y-%m-%d")
            df = df.loc[df.index >= day + " 00:00:00"]

        return df
    
    # may need to have this in other areas as well
    def get_technicals(self, indicator: str, period: int):
        querystring = {
            "symbol": self.ticker,
            "function": indicator,
            "series_type": "close",
            "time_period": str(period),
            "interval":"daily"
        }

        headers = {
            "x-rapidapi-key": self.rapid_api_key,
            "x-rapidapi-host": "alpha-vantage.p.rapidapi.com"
        }

        url = "https://" + headers["x-rapidapi-host"] + "/query"

        response = requests.get(url, headers=headers, params=querystring).json()

        indicator_data = pd.DataFrame(response["Technical Analysis: " + indicator])
        indicator_data = indicator_data.T.loc[::-1].astype(float)

        return indicator_data
    
    def get_financials(self,statement: str):
        querystring = {
            "symbol": self.ticker.lower(),
            "target_currency": "USD",
            "period_type": "annual",
            "statement_type": statement
        }

        headers = {
            "x-rapidapi-key": self.rapid_api_key,
            "x-rapidapi-host": "seeking-alpha.p.rapidapi.com"
        }

        url = "https://" + headers["x-rapidapi-host"] + "/symbols/get-financials"

        values = requests.get(url, headers=headers, params=querystring).json()

        values_dataset = pd.DataFrame()

        for p1 in range(len(values)):
            part_data = values[p1]["rows"]

            for p2 in range(len(part_data)):
                sub_data = pd.DataFrame(part_data[p2]["cells"])
                sub_data["account"] = part_data[p2]["value"]

                sub_data = sub_data.loc[(sub_data["class"] != "archive-lock") & (sub_data["value"] != False)]
                
                sub_data["value"] = sub_data["value"].str.replace("[$,)]","",regex=True)
                sub_data["value"] = sub_data["value"].str.replace("(","-")

                if (sub_data["value"].str[-1] == "%").any():
                    sub_data["value"] = sub_data["value"].str.replace("%","")
                    sub_data["value"] = sub_data["value"].replace("-",np.nan)
                    sub_data["value"] = sub_data["value"].replace("NM",np.nan)
                    sub_data["value"] = sub_data["value"].astype(float)/100
                else:
                    sub_data["value"] = sub_data["value"].replace("-",np.nan)
                    sub_data["value"] = sub_data["value"].replace("NM",np.nan)
                    sub_data["value"] = sub_data["value"].astype(float)
                
                sub_data = sub_data.rename(columns={"name": "date"})
                
                values_dataset = pd.concat([values_dataset,sub_data[["account","date","value"]]])
        
        values_dataset = values_dataset.reset_index(drop=True)

        financials_data = pd.DataFrame(index=values_dataset["account"].drop_duplicates().tolist(),
                                       columns=values_dataset["date"].drop_duplicates().tolist()) 
        
        for date in financials_data.columns.tolist():
            financials_data[date] = values_dataset.loc[values_dataset["date"] == date, "value"].values
            financials_data[date] = financials_data[date].fillna(0)
        
        return financials_data

    def get_estimates(self, field: str):
        if field != "eps" or field != "revenues":
            raise ValueError("The data type must be either 'eps' or 'revenues'.")
        
        querystring = {
            "symbol": self.ticker.lower(),
            "data_type": field,
            "period_type": 'quarterly'
        }

        headers = {
            "x-rapidapi-key": self.rapid_api_key,
            "x-rapidapi-host": "seeking-alpha.p.rapidapi.com"
        }

        url = "https://" + headers["x-rapidapi-host"] + "/symbols/get-estimates"

        response = requests.get(url, headers=headers, params=querystring).json()

        data = response["data"]

        df = pd.concat([pd.DataFrame(data[i]["attributes"],index=[0]) 
                        for i in range(len(data))],axis=0).reset_index(drop=True)

        df.index = df["period_end_date"].values

        df = df[["actual","consensus"]]

        return df

class EconIndicatorsData:
    def __init__(self) -> None:
        pass

    def risk_metrics(self):
        def percent_change(df: pd.DataFrame, tick: str):
            df_tick = df[tick]
            val = df_tick.iloc[len(df_tick)-1]/df_tick.iloc[0]
            val = val - 1
            return val.round(decimals=4)
        
        stats = {}

        tick_compares = EquitiesData("IWF VTV SPY ^VIX SIZE").get_historical_data()
        tick_compares = tick_compares["Adj Close"].reset_index()

        tick_compares = tick_compares.loc[tick_compares["Date"] >= str(dt.datetime.today().year) + "-01-01"]

        treasury = pd.read_html("https://www.multpl.com/10-year-treasury-rate/table/by-year")

        stats["BenchmarkReturn"] = percent_change(tick_compares,"SPY")
        stats["RiskFree"] = round(float(treasury[0].iloc[0,1][:-1])/100,4)

        stats["RiskPremium"] = round(stats["BenchmarkReturn"] - stats["RiskFree"],4) 
        stats["GrowthPremium"] = round(percent_change(tick_compares,"IWF")-stats["RiskFree"],4)
        stats["ValuePremium"] = round(percent_change(tick_compares,"VTV")-stats["RiskFree"],4)
        stats["SizePremium"] = round(percent_change(tick_compares,"SIZE")-stats["RiskFree"],4)

        stats["VIX/SPY Corr"] = tick_compares.corr(numeric_only=True).loc["^VIX", "SPY"].round(decimals=4)
        stats["VIX/SPY Beta"] = stats["VIX/SPY Corr"]*round(tick_compares["^VIX"].std()/tick_compares["SPY"].std(),4)

        return stats

class AlgoStatsData:
    def __init__(self, ticker: str):
        self.ticker = ticker

    # This is essentially meant to be a dataframe for backtesting actions
    # Formatting for this will change dependent on what we use to backtest (we may need to create our own)
    def action_tickers(self,buy_indicator: pd.DataFrame,sell_indicator: pd.DataFrame):
        tick_buy = pd.DataFrame(buy_indicator[self.ticker])
        tick_buy["BuySignal"] = "Buy"
        tick_buy = tick_buy.rename(columns={self.ticker:"BuyAction"})

        tick_sell = pd.DataFrame(sell_indicator[self.ticker])
        tick_sell["SellSignal"] = "Sell"
        tick_sell = tick_sell.rename(columns={self.ticker:"SellAction"})

        actions = pd.concat([tick_buy,tick_sell],axis=1)
                        
        actions.loc[(actions["BuyAction"] == False) & (actions["SellAction"] == False), ["BuySignal","SellSignal"]] = "Hold"

        buy = actions.loc[(actions["BuySignal"] == "Buy") & (actions["BuyAction"] == True), "BuySignal"]
        sell = actions.loc[(actions["SellSignal"] == "Sell") & (actions["SellAction"] == True), "SellSignal"]
        hold = actions.loc[(actions["BuySignal"] == "Hold") & (actions["SellSignal"] == "Hold"), "BuySignal"]

        actions = pd.concat([buy,sell,hold],axis=0).reset_index()
        actions.columns = ["Date", self.ticker + "_Signal"]

        actions = actions.sort_values(by="Date",ascending=True).reset_index(drop=True)

        decision = []
        previous_decision = ""
        
        for value in actions[self.ticker + "_Signal"].values.tolist():
            if value == previous_decision:
                decision.append("Hold")
            else:
                decision.append(value)
                previous_decision = value
        
        actions[self.ticker + "_Signal"] = decision
        actions = actions.drop(["Date"],axis=1)

        return actions
    
    def backtest_algo(self):
        pass

    def results(self):
        pass

    def plot_algo(self):
        pass

    def performance(self):
        pass 

    def walk_forward_optimization(self):
        pass