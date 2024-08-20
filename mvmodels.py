import pandas as pd
import yfinance as yf
import numpy as np
import requests
from mvdata import TickerData  
from stochastic.processes.noise import FractionalGaussianNoise

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

    tgvs = [tgv+(i*.005) for i in range(-2,10,1)]
    waccs = [wacc+(i*.004) for i in range(-2,5,1)]

    fair_values = np.zeros((len(tgvs),len(waccs)))

    for i in range(len(tgvs)):
        for j in range(len(waccs)):
            pv_fcf = unlevered_fcf.values/((1+waccs[j])**cols2)

            tv = round((unlevered_fcf.values.tolist()[-1]*(1+waccs[j]))/(waccs[j]-tgvs[i]),1)
            pv_tv = round(tv/((1+waccs[j])**cols2.flatten().tolist()[-1]),1)

            enterprise_value = round(pv_tv + pv_fcf.sum(),1)
            fair_value = (enterprise_value+cash-debt)/shares

            fair_values[i,j] += round(fair_value,2)
    
    fair_values = pd.DataFrame(fair_values,index=tgvs,columns=waccs)

    return fair_values

def public_comps(tick: str):
    pass

def residual_income(tick: str):
    pass

def hurst_exponent(df: pd.DataFrame, hurst_window: int):
    df["Return"] = np.log(df['Adj Close'] / df['Adj Close'].shift(1)).dropna()

    hurst_exponents = []

    for start in range(len(df) - hurst_window):
        end = start + hurst_window
        window_data = df['Return'].iloc[start:end]
        
        N = len(window_data)
        mean_adj_ts = window_data - np.mean(window_data)
        cumulative_dev = np.cumsum(mean_adj_ts)
        R = np.max(cumulative_dev) - np.min(cumulative_dev)
        S = np.std(window_data)
        if S == 0 or R == 0:  # Avoid division by zero
            hurst_exponents.append(np.nan)
        else:
            hurst_exponents.append(np.log((R / S)) / np.log(N))
    
    hurst = pd.DataFrame(hurst_exponents,columns=["hurst_exponent"])

    return hurst

def monte_carlo(tick: str, num_days: int, point_per_day: float, num_simulations: int):
    df = TickerData(tick).get_historical_data(start_date="2020-01-01")

    start = df["Adj Close"].values.tolist()[-1]

     # Trading days
    simulation = np.zeros((num_days*point_per_day+1, num_simulations))

    window = 30
    hurst = hurst_exponent(df,window).values.mean()

    m = np.log2(len(df)-window)

    lower_bound = hurst - np.e ** (-7.33 * np.log(np.log(m)) + 4.21)
    upper_bound = hurst + np.e ** (-7.20 * np.log(np.log(m)) + 4.04) 

    for i in range(num_simulations):
        H = np.random.uniform(low=lower_bound,high=upper_bound)
        fgn = FractionalGaussianNoise(hurst=H,t=num_days)
        sim = fgn._sample_fractional_gaussian_noise(num_days*point_per_day)
        
        sim = sim.cumsum()
        sim = np.insert(sim, [0], 0)
        simulation[:, i] += sim

        ruin = np.where(sim < start*-1)[0].tolist()
        if len(ruin) >= 1:
            simulation[ruin[0]:,i] = start*-1

    simulation = pd.DataFrame(simulation) + start

    return simulation





