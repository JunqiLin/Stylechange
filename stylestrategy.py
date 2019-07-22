#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 16:15:26 2019

@author: linjunqi
"""

import pandas as pd
import numpy as np 
import talib as ta

from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties

# 获取沪深300和中证500的历史数据
hz_price = np.flipud(np.array(pd.read_excel('./hs300.xlsx')['close']))[:,np.newaxis]
zz_price = np.flipud(np.array(pd.read_excel('./zz500.xlsx')['close']))[:,np.newaxis]

# 构建dataframe存储历史价格数据、相对强弱指标、仓位信息记录、累计收益等信息
data = pd.DataFrame(np.vstack([hz_price.T,zz_price.T]).T,columns=['hs300','zz500'])
# 使用缺失值的前一日数据进行填充
data.fillna(axis=0,method='ffill')

#计算相对强弱指标
data['P'] = np.log(data.zz500) - np.log(data.hs300)

# 产生交易信号函数
def strategy1(data,N1,N2,fee_ratio = 0):                    #N1日新高，N2日新低
   data['flag_hs'] = 0 
   data['flag_zz'] = 0
   data['rd_strategy'] = 0                                  #策略的每日收益
   data['change'] = 0                                       #记录仓位改变的flag
   data['net_zz'] = 0                                       #csi500净收益
   data['net_hs'] = 0                                       #csi300净收益
   data['rd_zz'] = data['zz500'].pct_change(1).fillna(0)    #csi500每日收益
   data['rd_hs'] = data['hs300'].pct_change(1).fillna(0)    #csi300每日收益
   
   for i in range(max(N1,N2),data.shape[0] - 1):
       # 相对强弱指标创新高，做多小盘
       if data.P[i] >= np.max(data.P[i - N1:i]):
           data.loc[i + 1 ,'flag_zz'] = 1
           data.loc[i + 1 ,'flag_hs'] = 0

       # 相对强弱指标创新低，做多大盘
       elif data.P[i] <= np.min(data.P[i - N2:i]):
           data.loc[i + 1 ,'flag_zz'] = 0
           data.loc[i + 1 ,'flag_hs'] = 1
       # 无信号时保持原本仓位
       else:
           data.loc[i + 1 ,'flag_zz'] = data.loc[i ,'flag_zz']
           data.loc[i + 1 ,'flag_hs'] = data.loc[i ,'flag_hs']
           
   data.loc[data['flag_zz'] ==1,'rd_strategy'] = data.loc[data['flag_zz'] ==1,'rd_zz']
   data.loc[data['flag_hs'] ==1,'rd_strategy'] = data.loc[data['flag_hs'] ==1,'rd_hs']

   data.loc[data['flag_hs'] != data.flag_hs.shift(1),'change'] = 1 
   data.loc[0,'change'] = 0
   data['net_zz'] = (1+data['rd_zz']).cumprod()
   data['net_hs'] = (1+data['rd_hs']).cumprod()
   data['rd_strategy'] = data['rd_strategy'] - fee_ratio*data['change']
   data['net_strategy'] = (1 + data['rd_strategy']).cumprod()   #策略净收益
   return data

d = strategy1(data,20,20,0)
plt.plot(d['net_zz'],color = 'red',label='zz500')
plt.plot(d['net_hs'],color = 'yellow',label = 'hs300')
plt.plot(d['net_strategy'], color = 'blue',label = 'net_strategy')
plt.plot(d['flag_zz']-0.5,color = 'green',label = 'flag')
plt.xlabel('trade days')
plt.ylabel('cum_returns')
plt.legend()
plt.show()
d.to_csv('record.csv')