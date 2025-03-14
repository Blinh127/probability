#!/usr/bin/env python
# coding: utf-8

# In[23]:


import pandas as pd
import talib
import matplotlib.pyplot as plt
import vnstock
import numpy as np
from vnstock import Vnstock 


# p(v) : xác suất mà khối lượng phiên 2 cao hơn khối lượng phiên 1
# p(a) xác suất mua tại điểm engulfing, giá sẽ tăng ít nhất 5 % sau 7 ngày
# p(b) : xác suất mà có phiên 3 (close > open)
probabilities = {}

# Danh sách mã cổ phiếu cần kiểm tra
stock_list = ['HPG', 'VIB', 'MSN', 'MSH', 'EVF', 'CTG', 'MBB', 'KBC', 'SSI']
def calculate_probability(df, signal_col, threshold=0.05, days=7):
    success_count = 0
    total_signals = 0
    
    for idx in df[df[signal_col]].index:
        future_prices = df.loc[idx:].iloc[:days]['close']
        if len(future_prices) == days:
            price_change = (future_prices.max() - df.loc[idx, 'close']) / df.loc[idx, 'close']
            if price_change >= threshold:
                success_count += 1
            total_signals += 1
    
    return success_count / total_signals if total_signals > 0 else 0
    
for stock in stock_list:
    vnstock_instance = Vnstock().stock(symbol=stock, source='VCI')  # Sửa ticker thành stock
    start_date = "2020-01-01"
    end_date = "2025-01-01"
    df_ticker = vnstock_instance.quote.history(symbol=stock, start=start_date, end=end_date)

    if df_ticker.empty:
        print(f"{stock} không có dữ liệu, bỏ qua!")
        continue
    
    # Khởi tạo dictionary cho mỗi stock
    probabilities[stock] = {}
    df_ticker['open'] = df_ticker['close'].shift(1)
    df_ticker['Engulfing_Signal'] = talib.CDLENGULFING(df_ticker['open'], df_ticker['high'], df_ticker['low'], df_ticker['close'])
    df_ticker['Bullish_Engulfing'] = df_ticker['Engulfing_Signal'] > 0
    df_ticker['Bearish_Engulfing'] = df_ticker['Engulfing_Signal'] < 0
    df_ticker['Volume_Condition'] = df_ticker['volume'] > df_ticker['volume'].shift(1)
    

    # p(v) : xác suất mà khối lượng phiên 2 cao hơn khối lượng phiên 1
    # p(a) xác suất mua tại điểm engulfing, giá sẽ tăng ít nhất 5 % sau 7 ngày
    # p(b) : xác suất mà có phiên 3 (close > open)
    P_V = df_ticker['Volume_Condition'].mean()
    P_A = calculate_probability(df_ticker, 'Bullish_Engulfing', threshold=0.05, days=7)

    # Xác định xác suất xảy ra Bullish Engulfing và Volume Condition đồng thời
    P_AV = (df_ticker['Bullish_Engulfing'] & df_ticker['Volume_Condition']).mean()
    P_A_V = P_AV / P_V
    # Xác định xác suất phiên tiếp theo có giá đóng cửa cao hơn
    P_B = (df_ticker['close'].shift(-1) > (df_ticker['open'].shift(-1))).mean()
    
    # Xác suất P(B|A,V) - phiên tiếp theo có close > open nếu Bullish Engulfing + Volume Condition
    P_BAV = (df_ticker[df_ticker['Bullish_Engulfing'] & df_ticker['Volume_Condition']]['close'].shift(-1) > 
             (df_ticker[df_ticker['Bullish_Engulfing'] & df_ticker['Volume_Condition']])['open'].shift(-1)).mean()
    P_BV = ((df_ticker['close'].shift(-1) > (df_ticker['open'].shift(-1))) &  (df_ticker['volume'] > df_ticker['volume'].shift(1))).mean()
    P_V_B = P_BV / P_B
    # Tính P(A, V | B) theo Bayes
    P_AVB = (P_BAV * P_AV) / P_B if P_B > 0 else 0
    P_BA = (df_ticker[df_ticker['Bullish_Engulfing']]['close'].shift(-1) > df_ticker[df_ticker['Bullish_Engulfing']]['close']).mean()
    P_AB = (P_BA * P_A) / P_B if P_B > 0 else 0
    P_A_BV = P_BAV * P_A_V * P_V / (P_V_B * P_B)
    # Lưu vào probabilities
    probabilities[stock]['P(A,V|B)'] = P_AVB
    probabilities[stock]['P(A)'] = P_A
    probabilities[stock]['P(B|A)'] = P_BA if P_A > 0 else 0
    probabilities[stock]['P(B)'] = P_B
    probabilities[stock]['P(A|B)'] = P_AB if P_B > 0 else 0
    probabilities[stock]['P(V)'] = P_V  
    probabilities[stock]['P(B|A,V)'] = P_BAV
    probabilities[stock]['P(A|B,V)'] =  P_A_BV

# In kết quả
for stock, probs in probabilities.items():
    print((
        f"{stock}: P(A) = {probs['P(A)']:.2%}, "
        f"P(B|A) = {probs['P(B|A)']:.2%}, "
        f"P(B) = {probs['P(B)']:.2%}, "
        f"P(A|B) = {probs['P(A|B)']:.2%}, "
        f"P(V) = {probs['P(V)']:.2%}, "
        f"P(B|A,V) = {probs['P(B|A,V)']:.2%}"
        f"P(A|B.V) = {probs['P(A|B,V)']:.2%}"
    ))


# In[ ]:




