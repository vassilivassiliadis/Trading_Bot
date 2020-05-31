# -*- coding: utf-8 -*-
"""
Created on Sat May 30 11:28:06 2020

@author: Vassili
"""
#Notes: The Hist Intrayday prices include when 'full' the 5 last trading days, same for SMA

#ToDo: 
# - dynamically change the end of the trading day depending on the region
# - adapt the trading strategy into a live environment
# - test and use other technical indicators (RSI, Stoch, ...)
# - test and use other trading strategies (Doji, Charttechniques, ...)
# - create charts with bars, candlesticks etc. (Bloomberg Style)

#Import the necessary libraries
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
from matplotlib import pyplot as plt
from datetime import datetime
import pandas as pd

#################
####Functions####
#################        

#Creates a list of Simple Moving Average DataFrames of each chosen stock
def moving_average(rollingterm):
    sma_list=[]
    for i in range(0,5):
        local_sma=hist_list[i].sort_values('date')[['4. close']].rolling(rollingterm).mean()
        local_sma.columns=['SMA']
        sma_list.append(local_sma)
    return sma_list

#########################
####Trading Bot Setup####
#########################

#Enter your own AlphaVantage Key
#Get one for free under https://www.alphavantage.co/support/#api-key
ts = TimeSeries(key='ENTER YOUR OWN KEY',output_format='pandas')
ti = TechIndicators(key='ENTER YOUR OWN KEY', output_format='pandas')

#Choose 5 stocks (prefer volatile ones) and the values for the Short Term and the Long Term Simple Moving Average (SMA)
stock1='AAL'
stock2='CCL'
stock3='TWTR'
stock4='AMD'
stock5='DAL'
short_term=25
long_term=75
stock_list=[stock1, stock2, stock3, stock4, stock5]
#today=date.today()

#Attention: Since Alpha Vantage API call frequency is only 5 calls per minute,
#you have to run the API Code Snippets with a break of 1 minute each

#Get historical data from your chosen stocks
for index, item in enumerate(stock_list,start=1):
    if index == 1: hist_list=[]
    hist, meta_data = ts.get_intraday(symbol=item,outputsize='full',interval='1min')
    hist_list.append(hist)

#Create a list for the trading days    
trading_days_list=list(reversed(hist.index.strftime("%Y-%m-%d").unique()))

#Get the SMA Short Term data from your chosen stocks
#Version 1 (Alpha Vantage API):
# for index, item in enumerate(stock_list,start=1):
#     if index == 1: sma_st_list=[]
#     sma_st, meta_data = ti.get_sma(symbol=item,interval='1min',time_period=short_term)
#     sma_st_list.append(sma_st)
#Version 2 (own function):
sma_st_list=moving_average(short_term)
  
#Get the SMA Long Term data from your chosen stocks
#Version 1 (Alpha Vantage API):
# for index, item in enumerate(stock_list,start=1):
#     if index == 1: sma_lt_list=[]
#     sma_lt, meta_data = ti.get_sma(symbol=item,interval='1min',time_period=long_term)
#     sma_lt_list.append(sma_lt)
#Version 2 (own function):
sma_lt_list=moving_average(long_term)
    
#Daily Visual Analysis    
for i in range(0,5):
    for j in range(0,5):
        plt.plot(hist_list[i].loc[trading_days_list[j],'4. close'],label="stock")
        plt.plot(sma_st_list[i].loc[trading_days_list[j],:],label="short_term_sma "+ str(short_term))    
        plt.plot(sma_lt_list[i].loc[trading_days_list[j],:],label="long_term_sma "+ str(long_term))
        plt.title(stock_list[i]+" "+trading_days_list[j])
        plt.legend()
        plt.xticks(rotation=90)
        plt.show()

#Visual Analysis for the whole period
for i in range(0,5):
    plt.plot(hist_list[i].loc[:,'4. close'],label="stock")
    plt.plot(sma_st_list[i],label="short_term_sma "+ str(short_term))    
    plt.plot(sma_lt_list[i],label="long_term_sma "+ str(long_term))
    plt.title(stock_list[i])
    plt.legend()
    plt.xticks(rotation=90)
    plt.show()

##########################
#####Live Environment#####
##########################

#tbd

##################
#####Backtest#####
##################

#Strategy Single Stock goes long when Short Term SMA CROSSES above the Long Term SMA and Short if it is the other way round, it trades only within a day
#You can only have 1 position for a stock (Long/Short/None)
#It closes a position you entered, if the profits are >= max_profit, the losses are <=max_loss or if the trading day ends    
def backtest_strategy_singlestock(capital,s,hist_list,sma_st_list,sma_lt_list,stock_list,max_loss,max_profit):
    #Creating a trading log and initializing the variables
    trading_log=pd.DataFrame(columns=['Date','Stock','Price','Long/Short','Capital'])
    number=0
    long=0
    short=0
    shares=0
    state=[]
    #For Loop that goes through each timepoint
    for j in range(0,hist_list[s].shape[0]+1):
        try:
            #Checks if you have a long position on the stock
            if long==1:
                #Sells the stock if the profits are >= max_profit
                if hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3] \
                / trading_log.loc[number-1,'Price'] >= 1+max_profit:
                    long=0
                    capital=capital+shares*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                    trading_log.loc[number,'Stock']=stock_list[s]
                    trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Long/Short']='Closed Long with Profit'
                    trading_log.loc[number,'Capital']=capital
                    number=number+1
                #Sells the stock if the losses are <= max_loss
                elif hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3] \
                / trading_log.loc[number-1,'Price'] <= 1-max_loss:
                    long=0
                    capital=capital+shares*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                    trading_log.loc[number,'Stock']=stock_list[s]
                    trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Long/Short']='Closed Long with Loss'
                    trading_log.loc[number,'Capital']=capital
                    number=number+1
                #Sells the stock if the trading day ends
                elif hist_list[s].iloc[[-j]].index.strftime("%H:%M")[0]=='16:00':
                    long=0
                    capital=capital+shares*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                    trading_log.loc[number,'Stock']=stock_list[s]
                    trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Long/Short']='End Day'
                    trading_log.loc[number,'Capital']=capital
                    number=number+1
            #Checks if you have a short position on the stock
            if short==1:
                #Buys the stock if the profits are >= max_profit
                if trading_log.loc[number-1,'Price'] \
                / hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3] >= 1+max_profit:
                    short=0
                    capital=capital+shares*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                    trading_log.loc[number,'Stock']=stock_list[s]
                    trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Long/Short']='Closed Short with Profit'
                    trading_log.loc[number,'Capital']=capital
                    number=number+1
                #Buys the stock if the losses are <= max_loss    
                elif trading_log.loc[number-1,'Price'] \
                / hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3] <= 1-max_loss:
                    short=0
                    capital=capital+shares*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                    trading_log.loc[number,'Stock']=stock_list[s]
                    trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Long/Short']='Closed Short with Loss'
                    trading_log.loc[number,'Capital']=capital
                    number=number+1
                #Buys the stock if the trading day ends    
                elif hist_list[s].iloc[[-j]].index.strftime("%H:%M")[0]=='16:00':
                    short=0
                    capital=capital+shares*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                    trading_log.loc[number,'Stock']=stock_list[s]
                    trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                    trading_log.loc[number,'Long/Short']='End Day'
                    trading_log.loc[number,'Capital']=capital
                    number=number+1
            #Checks if the Short Term Average is higher than the Long Term
            if sma_st_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].SMA > \
              sma_lt_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].SMA:
                  state.append('S>L')
            #Checks if the Long Term Average is higher than the Short Term
            elif sma_st_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].SMA < \
              sma_lt_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].SMA:
                  state.append('L>S')
            #Enters a long trade only if the Short Term Average crosses 
            #the Long Term (happens when the state changes and the last state is 'S>L')      
            #and only if you dont have any other position for that stock     
            if state[-1]!=state[-2] and state[-1]=='S>L' \
              and long==0 and short ==0 and hist_list[s].iloc[[-j]].index.strftime("%H:%M")[0]!='16:00':
                  trade_capital=max(min(100,capital),0)
                  capital=capital-trade_capital
                  long=1
                  shares=trade_capital/hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                  trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                  trading_log.loc[number,'Stock']=stock_list[s]
                  trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                  trading_log.loc[number,'Long/Short']='Enter Long'
                  trading_log.loc[number,'Capital']=capital
                  number=number+1
            #Enters a short trade only if the Long Term Average crosses 
            #the Short Term (happens when the state changes and the last state is 'L>S')      
            #and only if you dont have any other position for that stock
            elif  state[-1]!=state[-2] and state[-1]=='L>S' \
              and short==0 and long==0 and hist_list[s].iloc[[-j]].index.strftime("%H:%M")[0]!='16:00':
                  trade_capital=max(min(100,capital),0)
                  capital=capital+trade_capital
                  short=1
                  shares=-trade_capital/hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                  trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                  trading_log.loc[number,'Stock']=stock_list[s]
                  trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                  trading_log.loc[number,'Long/Short']='Enter Short'
                  trading_log.loc[number,'Capital']=capital
                  number=number+1
        except: 
            continue          
    return trading_log

#Strategy All Stocks goes long when Short Term SMA CROSSES above the Long Term SMA and Short if it is the other way round, trades only within a day, takes in consideration all stocks
#You can only have 1 position for a stock (Long/Short/None)
#It closes a position you entered, if the profits are >= max_profit, the losses are <=max_loss or if the trading day ends    
def backtest_strategy_allstocks(capital,hist_list,sma_st_list,sma_lt_list,stock_list,max_loss,max_profit):
    trading_log=pd.DataFrame(columns=['Date','Stock','Price','Long/Short','Capital'])
    number=0
    long=[0, 0, 0, 0, 0]
    short=[0, 0, 0, 0, 0]
    shares= [0, 0, 0, 0, 0]
    state=[[],[],[],[],[]]
    max_range=0
    for i in range(0,5):
        if hist_list[i].shape[0]+1 > max_range:
            max_range=hist_list[i].shape[0]+1    
    for j in range(0,max_range) :
        for s in range(0,5):
            try :
                if long[s]==1:
                    if hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3] \
                    / trading_log[trading_log.loc[:,'Stock']==stock_list[s]].iloc[-1,2] >= 1+max_profit:
                        long[s]=0
                        capital=capital+shares[s]*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                        trading_log.loc[number,'Stock']=stock_list[s]
                        trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Long/Short']='Closed Long with Profit'
                        trading_log.loc[number,'Capital']=capital
                        number=number+1
                    elif hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3] \
                    / trading_log[trading_log.loc[:,'Stock']==stock_list[s]].iloc[-1,2] <= 1-max_loss:
                        long[s]=0
                        capital=capital+shares[s]*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                        trading_log.loc[number,'Stock']=stock_list[s]
                        trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Long/Short']='Closed Long with Loss'
                        trading_log.loc[number,'Capital']=capital
                        number=number+1
                    elif hist_list[s].iloc[[-j]].index.strftime("%H:%M")[0]=='16:00':
                        long[s]=0
                        capital=capital+shares[s]*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                        trading_log.loc[number,'Stock']=stock_list[s]
                        trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Long/Short']='End Day'
                        trading_log.loc[number,'Capital']=capital
                        number=number+1
                if short[s]==1:
                    if trading_log[trading_log.loc[:,'Stock']==stock_list[s]].iloc[-1,2] \
                    / hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3] >= 1+max_profit:
                        short[s]=0
                        capital=capital+shares[s]*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                        trading_log.loc[number,'Stock']=stock_list[s]
                        trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Long/Short']='Closed Short with Profit'
                        trading_log.loc[number,'Capital']=capital
                        number=number+1
                    elif trading_log[trading_log.loc[:,'Stock']==stock_list[s]].iloc[-1,2] \
                    / hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3] <= 1-max_loss:
                        short[s]=0
                        capital=capital+shares[s]*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                        trading_log.loc[number,'Stock']=stock_list[s]
                        trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Long/Short']='Closed Short with Loss'
                        trading_log.loc[number,'Capital']=capital
                        number=number+1
                    elif hist_list[s].iloc[[-j]].index.strftime("%H:%M")[0]=='16:00':
                        short[s]=0
                        capital=capital+shares[s]*hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                        trading_log.loc[number,'Stock']=stock_list[s]
                        trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                        trading_log.loc[number,'Long/Short']='End Day'
                        trading_log.loc[number,'Capital']=capital
                        number=number+1
                if sma_st_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].SMA > \
                  sma_lt_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].SMA:
                      state[s].append('S>L')
                elif sma_st_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].SMA < \
                  sma_lt_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].SMA:
                      state[s].append('L>S')            
                if state[s][-1]!=state[s][-2] and state[s][-1]=='S>L' \
                  and long[s]==0 and short[s] ==0 and hist_list[s].iloc[[-j]].index.strftime("%H:%M")[0]!='16:00':
                      trade_capital=max(min(100,capital),0)
                      capital=capital-trade_capital
                      long[s]=1
                      shares[s]=trade_capital/hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                      trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                      trading_log.loc[number,'Stock']=stock_list[s]
                      trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                      trading_log.loc[number,'Long/Short']='Enter Long'
                      trading_log.loc[number,'Capital']=capital
                      number=number+1
                elif  state[s][-1]!=state[s][-2] and state[s][-1]=='L>S' \
                  and short[s]==0 and long[s]==0 and hist_list[s].iloc[[-j]].index.strftime("%H:%M")[0]!='16:00':
                      trade_capital=max(min(100,capital),0)
                      capital=capital+trade_capital
                      short[s]=1
                      shares[s]=-trade_capital/hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                      trading_log.loc[number,'Date']=hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M")[0]
                      trading_log.loc[number,'Stock']=stock_list[s]
                      trading_log.loc[number,'Price']=hist_list[s].loc[list(hist_list[s].iloc[[-j]].index.strftime("%Y-%m-%d %H:%M"))[0]].iloc[0][3]
                      trading_log.loc[number,'Long/Short']='Enter Short'
                      trading_log.loc[number,'Capital']=capital
                      number=number+1
            except:                
                continue          
    return trading_log

#Backtesting your strategy for the stocks by creating a trading log
trading_log=backtest_strategy_allstocks(capital=1000, max_loss=0.01, max_profit=0.015, hist_list=hist_list, sma_lt_list=sma_lt_list, sma_st_list=sma_st_list, stock_list=stock_list)

trading_log_0=backtest_strategy_singlestock(capital=1000,s=0, max_loss=0.01, max_profit=0.015, hist_list=hist_list, sma_lt_list=sma_lt_list, sma_st_list=sma_st_list, stock_list=stock_list)
trading_log_1=backtest_strategy_singlestock(capital=1000,s=1, max_loss=0.01, max_profit=0.015, hist_list=hist_list, sma_lt_list=sma_lt_list, sma_st_list=sma_st_list, stock_list=stock_list)
trading_log_2=backtest_strategy_singlestock(capital=1000,s=2, max_loss=0.01, max_profit=0.015, hist_list=hist_list, sma_lt_list=sma_lt_list, sma_st_list=sma_st_list, stock_list=stock_list)
trading_log_3=backtest_strategy_singlestock(capital=1000,s=3, max_loss=0.01, max_profit=0.015, hist_list=hist_list, sma_lt_list=sma_lt_list, sma_st_list=sma_st_list, stock_list=stock_list)
trading_log_4=backtest_strategy_singlestock(capital=1000,s=4, max_loss=0.01, max_profit=0.015, hist_list=hist_list, sma_lt_list=sma_lt_list, sma_st_list=sma_st_list, stock_list=stock_list)


