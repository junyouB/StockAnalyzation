import pandas as pd
import numpy as np
import requests
from typing import Optional, Dict, Any

class DataFetcher:
    def __init__(self):
        pass
    
    def get_stock_data(self, symbol: str, period: str = '1y', interval: str = '1d') -> Optional[pd.DataFrame]:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            period: 时间周期，如 '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
            interval: 数据间隔，如 '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'
            
        Returns:
            包含股票数据的DataFrame，失败返回None
        """
        try:
            # 这里使用yfinance作为示例，实际项目中可以替换为其他数据源
            import yfinance as yf
            df = yf.download(symbol, period=period, interval=interval)
            if df.empty:
                return None
            return df
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
    
    def get_realtime_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            包含实时数据的字典，失败返回None
        """
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d')
            if data.empty:
                return None
            
            return {
                'symbol': symbol,
                'price': data['Close'].iloc[-1],
                'open': data['Open'].iloc[-1],
                'high': data['High'].iloc[-1],
                'low': data['Low'].iloc[-1],
                'volume': data['Volume'].iloc[-1],
                'datetime': data.index[-1].strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            print(f"获取实时数据失败: {e}")
            return None
