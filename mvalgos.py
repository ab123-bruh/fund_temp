import pandas as pd
import yfinance as yf
import requests
import numpy as np
from mvdata import TickerData

def dcf_fair_value(tick: str, num_years: int, wacc: float, tgv: float):
    inital = ["Total Revenues", "EBIT", "Income Tax Expense", "Depreciation & Amortization", 
              "Capital Expenditure", "Change In Net Working Capital", "Cash And Equivalents", 
              "Current Portion of LT Debt", "Total Common Shares Outstanding"]
    
    ticker = TickerData(tick)
    
    financials = pd.concat([ticker.get_financials("income-statement"),
                            ticker.get_financials("balance-sheet"),
                            ticker.get_financials("cash-flow-statement")],axis=0)
    
    financials = financials.drop(["TTM", "Last Report"],axis=1)
    
    financials = financials.loc[financials.index.isin(inital)]
    financials = financials[~financials.index.duplicated(keep="first")]

    financials.columns = [int(val[4:]) for val in financials.columns.tolist()]
    start = max(financials.columns.tolist())

    financials = financials.dropna(axis=1).T 
    financials = financials[inital]

    if financials.index.values.tolist()[0] == start:
        financials = financials.iloc[::-1]
    
    cash = financials.loc[financials.index == start,inital[-3]].values.tolist()[0]
    debt = financials.loc[financials.index == start,inital[-2]].values.tolist()[0]
    shares = financials.loc[financials.index == start,inital[-1]].values.tolist()[0]

    financials = financials.drop(inital[6:],axis=1)

    growth_rates = pd.DataFrame()
    growth_rates.index = financials.index.values-start

    growth_rates["Total Revenues"] = (financials["Total Revenues"]/financials["Total Revenues"].shift(1)).values-1
    growth_rates["EBIT"] = (financials["EBIT"]/financials["Total Revenues"]).values

    for col in inital[2:6]:
        growth_rates[col] = (financials[col]/financials["EBIT"]).values

    growth_rates = growth_rates.T
    financials = financials.T

    for i,k in zip(range(0,num_years,1), range(start,start+num_years,1)):
        years = [j for j in range(growth_rates.columns.tolist()[i],i+1,1)]
        growth_rates[i+1] = growth_rates[years].mean(axis=1)
        financials[k+1] = financials[k] * (1+growth_rates[i+1])

    cols1 = financials.columns.tolist()
    cols1 = np.array(cols1[cols1.index(start+1):])

    financials = financials[cols1]
    values = financials.T                  

    unlevered_fcf = values[inital[1]]-values[inital[2]]+values[inital[3]]-values[inital[4]]-values[inital[5]]
    
    cols2 = growth_rates.columns.tolist()
    cols2 = np.array(cols2[cols2.index(1):])

    pv_fcf = unlevered_fcf.values/((1+wacc)**cols2)

    tv = round((unlevered_fcf.values.tolist()[-1]*(1+wacc))/(wacc-tgv),1)
    pv_tv = round(tv/((1+wacc)**cols2.flatten().tolist()[-1]),1)

    enterprise_value = round(pv_tv + pv_fcf.sum(),1)
    fair_value = (enterprise_value+cash-debt)/shares

    return round(fair_value,2)

def tail_action(tickers: list, start_date: str):
    tick_str = ""

    for tick in tickers:
        tick_str += (tick + " ")

    df = TickerData(tick_str).get_historical_data(start_date=start_date)
    window = 50

    rolling_mean = df.rolling(window=window).mean()
    rolling_std = df.rolling(window=window).std()

    buy_signal = df < rolling_mean - (2 * rolling_std)
    sell_signal = df >= rolling_mean + (2 * rolling_std)

    ticker_action = pd.DataFrame(df.index)

    for tick in tickers:
        ticker_action[tick + "_Signal"] = TickerData(tick).action_tickers(buy_signal,sell_signal)

    date = ticker_action.pop("Date")
    ticker_action = ticker_action.set_index(date)

    return pd.concat([df,ticker_action],axis=1)