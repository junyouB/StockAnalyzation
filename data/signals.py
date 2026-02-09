import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any

class Signals:
    def __init__(self):
        pass
    
    def generate_ma_signals(self, data: pd.DataFrame, short_period: int = 10, long_period: int = 50) -> pd.DataFrame:
        """
        基于移动平均线生成买卖信号
        
        Args:
            data: 包含股票数据和移动平均线的DataFrame
            short_period: 短期移动平均线周期
            long_period: 长期移动平均线周期
            
        Returns:
            添加了买卖信号的DataFrame
        """
        df = data.copy()
        df['Signal'] = 0
        
        # 金叉：短期均线上穿长期均线
        df.loc[(df[f'MA{short_period}'] > df[f'MA{long_period}']) & (df[f'MA{short_period}'].shift(1) <= df[f'MA{long_period}'].shift(1)), 'Signal'] = 1
        
        # 死叉：短期均线下穿长期均线
        df.loc[(df[f'MA{short_period}'] < df[f'MA{long_period}']) & (df[f'MA{short_period}'].shift(1) >= df[f'MA{long_period}'].shift(1)), 'Signal'] = -1
        
        return df
    
    def generate_macd_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        基于MACD生成买卖信号
        
        Args:
            data: 包含MACD指标的DataFrame
            
        Returns:
            添加了买卖信号的DataFrame
        """
        df = data.copy()
        df['MACD_Signal'] = 0
        
        # MACD线上穿信号线
        df.loc[(df['MACD'] > df['Signal']) & (df['MACD'].shift(1) <= df['Signal'].shift(1)), 'MACD_Signal'] = 1
        
        # MACD线下穿信号线
        df.loc[(df['MACD'] < df['Signal']) & (df['MACD'].shift(1) >= df['Signal'].shift(1)), 'MACD_Signal'] = -1
        
        return df
    
    def generate_rsi_signals(self, data: pd.DataFrame, overbought: int = 70, oversold: int = 30) -> pd.DataFrame:
        """
        基于RSI生成买卖信号
        
        Args:
            data: 包含RSI指标的DataFrame
            overbought: 超买阈值
            oversold: 超卖阈值
            
        Returns:
            添加了买卖信号的DataFrame
        """
        df = data.copy()
        df['RSI_Signal'] = 0
        
        # RSI低于超卖阈值
        df.loc[df['RSI'] < oversold, 'RSI_Signal'] = 1
        
        # RSI高于超买阈值
        df.loc[df['RSI'] > overbought, 'RSI_Signal'] = -1
        
        return df
    
    def generate_bollinger_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        基于布林带生成买卖信号
        
        Args:
            data: 包含布林带指标的DataFrame
            
        Returns:
            添加了买卖信号的DataFrame
        """
        df = data.copy()
        df['BB_Signal'] = 0
        
        # 价格触及下轨
        df.loc[df['Close'] <= df['BB_Lower'], 'BB_Signal'] = 1
        
        # 价格触及上轨
        df.loc[df['Close'] >= df['BB_Upper'], 'BB_Signal'] = -1
        
        return df
    
    def generate_combined_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        综合所有指标生成买卖信号
        
        Args:
            data: 包含所有指标的DataFrame
            
        Returns:
            添加了综合买卖信号的DataFrame
        """
        df = data.copy()
        
        # 生成各个指标的信号
        df = self.generate_ma_signals(df)
        df = self.generate_macd_signals(df)
        df = self.generate_rsi_signals(df)
        df = self.generate_bollinger_signals(df)
        
        # 综合信号：计算信号总和
        df['Combined_Signal'] = df[['Signal', 'MACD_Signal', 'RSI_Signal', 'BB_Signal']].sum(axis=1)
        
        # 标准化信号：>0为买入，<0为卖出
        df['Final_Signal'] = 0
        df.loc[df['Combined_Signal'] > 0, 'Final_Signal'] = 1
        df.loc[df['Combined_Signal'] < 0, 'Final_Signal'] = -1
        
        return df
    
    def get_latest_signal(self, data: pd.DataFrame) -> int:
        """
        获取最新的买卖信号
        
        Args:
            data: 包含信号的DataFrame
            
        Returns:
            最新的信号值 (1: 买入, -1: 卖出, 0: 持有)
        """
        if 'Final_Signal' in data.columns:
            return data['Final_Signal'].iloc[-1]
        elif 'Signal' in data.columns:
            return data['Signal'].iloc[-1]
        else:
            return 0
