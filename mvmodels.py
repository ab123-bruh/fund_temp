import pandas as pd
import yfinance as yf
import numpy as np
import requests
import mvdata as mvD
from stochastic.processes.noise import FractionalGaussianNoise

# Make sure you have the three financial statements before inputting the data to calculate
def weighted_cost(tick: str, fin_state: pd.DataFrame):    
    stats = mvD.EconIndicatorsData().risk_metrics()

    cols = ["Effective Tax Rate", "Interest Expense", "Total Debt"]

    fin_state = fin_state.loc[fin_state.index.isin(cols)]
    fin_state = fin_state.dropna(axis=1).T 
    fin_state = fin_state[cols]
    fin_state = fin_state.loc[fin_state.index == max(fin_state.columns.tolist())]

    metrics = {col: yf.Ticker(tick).info[col] for col in ["beta", "marketCap", "enterpriseValue"]}

    cost_of_equity = stats["RiskFree"] + (metrics["beta"]*stats["RiskPremium"])
    waec = (metrics["marketCap"] * cost_of_equity)/metrics["enterpriseValue"]
    
    cost_of_debt = (-fin_state["Interest Expense"] / fin_state["Total Debt"]) * (1 - fin_state["Effective Tax Rate"])
    wadc = ((metrics["enterpriseValue"]-metrics["marketCap"]) * cost_of_debt) / metrics["enterpriseValue"]
    wadc = wadc.values.tolist()[0]

    final_values = {
        "WAEC": round(waec,4),
        "WADC": round(wadc,4),
        "WACC": waec + wadc
    }

    return final_values

# Possibly put the tgv as the CPI change YoY as that measures inflation
def dcf_fair_value(tick: str, num_years: int, tgv: float):
    inital = ["Total Revenues", "EBIT", "Income Tax Expense", "Depreciation & Amortization", 
              "Capital Expenditure", "Change In Net Working Capital", "Cash And Equivalents", 
              "Total Common Shares Outstanding"]
    
    ticker = mvD.EquitiesData(tick)
    
    financials = pd.concat([ticker.get_financials("income-statement"),
                            ticker.get_financials("balance-sheet"),
                            ticker.get_financials("cash-flow-statement")],axis=0)
    
    financials = financials.drop(["TTM", "Last Report"],axis=1)

    financials.columns = [int(val[4:]) for val in financials.columns.tolist()]

    wacc = weighted_cost(tick,financials)
    start = max(financials.columns.tolist())

    if financials.index.values.tolist()[0] == start:
        financials = financials.iloc[::-1]
    
    financials = financials.T 

    cash = financials.loc[financials.index == start,"Cash And Equivalents"].values.tolist()[0]
    shares = financials.loc[financials.index == start,"Total Common Shares Outstanding"].values.tolist()[0]
    
    debt = 0
    for fin in ["Short-Term Borrowings", "Current Portion of Lease Obligations", 
                "Long-Term Debt", "Capital Leases"]:
        if fin in financials.columns.tolist():
            debt += financials.loc[financials.index == start, fin].values.tolist()[0]

    financials = financials[inital[:len(inital)-2]]

    growth_rates = pd.DataFrame()
    growth_rates.index = financials.index.values-start

    growth_rates["Total Revenues"] = (financials["Total Revenues"]/financials["Total Revenues"].shift(1)).values-1
    growth_rates["EBIT"] = (financials["EBIT"]/financials["Total Revenues"]).values

    for col in inital[2:]:
        growth_rates[col] = (financials[col]/financials["EBIT"]).values

    growth_rates = growth_rates.T
    values = financials.T

    for i,k in zip(range(0,num_years,1), range(start,start+num_years,1)):
        years = [j for j in range(growth_rates.columns.tolist()[i],i+1,1)]
        growth_rates[i+1] = growth_rates[years].mean(axis=1)
        values[k+1] = values[k] * (1+growth_rates[i+1])

    cols1 = values.columns.tolist()
    cols1 = np.array(cols1[cols1.index(start+1):])

    financials = financials[cols1]
    values = values.T                  

    unlevered_fcf = values["EBIT"]-values["Income Tax Expense"]+values["Depreciation & Amortization"]\
        -values["Capital Expenditure"]-values["Change In Net Working Capital"]
    
    cols2 = growth_rates.columns.tolist()
    cols2 = np.array(cols2[cols2.index(1):])

    tgvs = [tgv+(i*.005) for i in range(-2,10,1)]
    waccs = [round(wacc["WACC"]+(i*.004),2) for i in range(-2,5,1)]

    fair_values = np.zeros((len(tgvs),len(waccs)))

    for i in range(len(tgvs)):
        for j in range(len(waccs)):
            pv_fcf = unlevered_fcf.values/((1+waccs[j])**cols2)

            tv = round((unlevered_fcf.values.tolist()[-1]*(1+waccs[j]))/(waccs[j]-tgvs[i]),1)
            pv_tv = round(tv/((1+waccs[j])**cols2.flatten().tolist()[-1]),1)

            enterprise_value = pv_tv + pv_fcf.sum()
            fair_value = (enterprise_value+cash-debt)/shares

            fair_values[i,j] += round(fair_value,2)
    
    fair_values = pd.DataFrame(fair_values,index=tgvs,columns=waccs)

    return fair_values

def residual_income(tick: str, num_years: int):
    inital = ["Book Value / Share", "Diluted EPS"]

    ticker = mvD.EquitiesData(tick)

    financials = pd.concat([ticker.get_financials("income-statement"),
                            ticker.get_financials("balance-sheet")],axis=0)
    
    financials = financials.drop(["TTM", "Last Report"],axis=1)

    waec = weighted_cost(tick,financials)

    financials = financials.loc[financials.index.isin(inital)]

    financials.columns = [int(val[4:]) for val in financials.columns.tolist()]
    start = max(financials.columns.tolist())

    financials = financials.dropna(axis=1).T 
    financials = financials[inital]

    if financials.index.values.tolist()[0] == start:
        financials = financials.iloc[::-1]
    
    growth_rates = pd.DataFrame()
    growth_rates.index = financials.index.values-start

    growth_rates[inital[0]] = (financials[inital[0]]/financials[inital[0]].shift(1)).values-1
    growth_rates[inital[1]] = (financials[inital[1]]/financials[inital[1]].shift(1)).values-1

    growth_rates = growth_rates.fillna(0)

    growth_rates = growth_rates.T
    financials = financials.T

    for i,k in zip(range(0,num_years,1), range(start,start+num_years,1)):
        years = [j for j in range(growth_rates.columns.tolist()[i],i+1,1)]
        growth_rates[i+1] = growth_rates[years].mean(axis=1)
        financials[k+1] = financials[k] * (1+growth_rates[i+1])
        
    cols1 = financials.columns.tolist()
    cols1 = np.array(cols1[cols1.index(start+1):])

    begin_book_value = financials.loc[financials.index == inital[0], start].values.tolist()[0]

    financials = financials[cols1]
    values = financials.T

    cols2 = growth_rates.columns.tolist()
    cols2 = np.array(cols2[cols2.index(1):])

    residual_income = values["Diluted EPS"] - (values["Book Value / Share"]*waec["WAEC"])

    pv_res_income = residual_income / ((1+waec["WAEC"]) ** cols2)

    fair_value = begin_book_value + pv_res_income.sum()

    return round(fair_value,2)

def hurst_exponent(df: pd.DataFrame, hurst_window: int):
    ret = np.log((df/df.shift(1)).dropna())

    hurst_exponents = []

    for end in range(len(ret),-1,-1):
        start = end - hurst_window
        window_data = ret.iloc[start:end]
        
        mean_adj_ts = window_data - np.mean(window_data)
        cumulative_dev = np.cumsum(mean_adj_ts)
        R = np.max(cumulative_dev) - np.min(cumulative_dev)
        S = np.std(window_data)
        if S == 0 or R == 0:  # Avoid division by zero
            hurst_exponents.insert(0,np.nan)
        else:
            hurst_exponents.insert(0,np.log((R / S)) / np.log(len(window_data)))
    
    hurst_exponents = pd.Series(hurst_exponents)

    hurst_exponents.index = df.index
    hurst_exponents = hurst_exponents.dropna()
    
    return hurst_exponents

def monte_carlo(tick: str, num_days: int, point_per_day: float, num_simulations: int):
    df = mvD.EquitiesData(tick).get_historical_data()["Adj Close"]

    start = df.values.tolist()[-1]

     # Trading days
    simulation = np.zeros((num_days*point_per_day+1, num_simulations))

    window = 30
    hurst = hurst_exponent(df,window)

    for i in range(num_simulations):
        H = np.random.normal(loc=hurst.mean(),scale=hurst.std())
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

def value_at_risk(tick: str):
    df = monte_carlo(tick,252,1,1000)

