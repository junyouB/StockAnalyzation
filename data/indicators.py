import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

class Indicators:
    def __init__(self):
        pass
    
    def calculate_ma(self, data: pd.DataFrame, periods: list = [5, 10, 20, 50, 200]) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            data: 包含股票数据的DataFrame
            periods: 移动平均线周期列表
            
        Returns:
            添加了移动平均线的DataFrame
        """
        df = data.copy()
        for period in periods:
            df[f'MA{period}'] = df['Close'].rolling(window=period).mean()
        return df
    
    def calculate_macd(self, data: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
        """
        计算MACD指标
        
        Args:
            data: 包含股票数据的DataFrame
            fast_period: 快速移动平均线周期
            slow_period: 慢速移动平均线周期
            signal_period: 信号线周期
            
        Returns:
            添加了MACD指标的DataFrame
        """
        df = data.copy()
        exp1 = df['Close'].ewm(span=fast_period, adjust=False).mean()
        exp2 = df['Close'].ewm(span=slow_period, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
        df['Histogram'] = df['MACD'] - df['Signal']
        return df
    
    def calculate_rsi(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算RSI指标
        
        Args:
            data: 包含股票数据的DataFrame
            period: RSI计算周期
            
        Returns:
            添加了RSI指标的DataFrame
        """
        df = data.copy()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    
    def calculate_bollinger_bands(self, data: pd.DataFrame, period: int = 20, num_std: float = 2) -> pd.DataFrame:
        """
        计算布林带
        
        Args:
            data: 包含股票数据的DataFrame
            period: 计算周期
            num_std: 标准差倍数
            
        Returns:
            添加了布林带指标的DataFrame
        """
        df = data.copy()
        df['BB_Middle'] = df['Close'].rolling(window=period).mean()
        df['BB_Std'] = df['Close'].rolling(window=period).std()
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * num_std)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * num_std)
        return df
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有指标
        
        Args:
            data: 包含股票数据的DataFrame
            
        Returns:
            添加了所有指标的DataFrame
        """
        df = self.calculate_ma(data)
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        df = self.calculate_bollinger_bands(df)
        return df
