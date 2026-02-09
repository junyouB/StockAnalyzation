import streamlit as st
import pandas as pd
import numpy as np

class UI:
    def __init__(self):
        pass
    
    def display_signal(self, signal: int, symbol: str):
        """
        显示买卖信号
        
        Args:
            signal: 信号值 (1: 买入, -1: 卖出, 0: 持有)
            symbol: 股票代码
        """
        if signal == 1:
            st.success(f"📈 **买入信号** - 股票 {symbol} 目前处于买入区间")
        elif signal == -1:
            st.error(f"📉 **卖出信号** - 股票 {symbol} 目前处于卖出区间")
        else:
            st.info(f"📊 **持有信号** - 股票 {symbol} 目前处于持有区间")
    
    def display_data_overview(self, data: pd.DataFrame):
        """
        显示数据概览
        
        Args:
            data: 包含股票数据的DataFrame
        """
        # 计算基本统计信息
        latest_price = data['Close'].iloc[-1]
        open_price = data['Open'].iloc[-1]
        high_price = data['High'].iloc[-1]
        low_price = data['Low'].iloc[-1]
        volume = data['Volume'].iloc[-1]
        
        # 计算涨跌幅
        prev_price = data['Close'].iloc[-2] if len(data) > 1 else latest_price
        change = latest_price - prev_price
        change_percent = (change / prev_price) * 100
        
        # 显示概览卡片
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="最新价格",
                value=f"${latest_price:.2f}",
                delta=f"{change:.2f} ({change_percent:.2f}%)",
                delta_color="normal"
            )
        
        with col2:
            st.metric(label="开盘价", value=f"${open_price:.2f}")
        
        with col3:
            st.metric(label="最高价", value=f"${high_price:.2f}")
        
        with col4:
            st.metric(label="最低价", value=f"${low_price:.2f}")
        
        with col5:
            st.metric(label="成交量", value=f"{volume:,.0f}")
        
        st.markdown("---")
    
    def display_signal_analysis(self, data: pd.DataFrame):
        """
        显示信号分析
        
        Args:
            data: 包含信号数据的DataFrame
        """
        # 统计信号分布
        if 'Final_Signal' in data.columns:
            signal_counts = data['Final_Signal'].value_counts()
            
            # 计算信号比例
            total_signals = signal_counts.sum()
            buy_ratio = signal_counts.get(1, 0) / total_signals * 100
            sell_ratio = signal_counts.get(-1, 0) / total_signals * 100
            hold_ratio = signal_counts.get(0, 0) / total_signals * 100
            
            # 显示信号分布
            st.write("### 信号分布")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label="买入信号", value=f"{signal_counts.get(1, 0)}", delta=f"{buy_ratio:.1f}%")
            
            with col2:
                st.metric(label="卖出信号", value=f"{signal_counts.get(-1, 0)}", delta=f"{sell_ratio:.1f}%")
            
            with col3:
                st.metric(label="持有信号", value=f"{signal_counts.get(0, 0)}", delta=f"{hold_ratio:.1f}%")
            
            # 显示最近的信号历史
            st.write("### 最近信号历史")
            recent_signals = data[['Close', 'Final_Signal']].tail(20)
            recent_signals['Signal'] = recent_signals['Final_Signal'].apply(
                lambda x: "买入" if x == 1 else "卖出" if x == -1 else "持有"
            )
            recent_signals['Date'] = recent_signals.index.strftime('%Y-%m-%d')
            
            # 显示信号表格
            st.dataframe(
                recent_signals[['Date', 'Close', 'Signal']],
                use_container_width=True,
                hide_index=True
            )
        
        st.markdown("---")
    
    def display_data_table(self, data: pd.DataFrame):
        """
        显示原始数据表格
        
        Args:
            data: 包含股票数据的DataFrame
        """
        # 选择要显示的列
        display_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # 添加指标列
        indicator_columns = ['MA5', 'MA10', 'MA20', 'MACD', 'Signal', 'RSI', 'BB_Upper', 'BB_Middle', 'BB_Lower', 'Final_Signal']
        for col in indicator_columns:
            if col in data.columns:
                display_columns.append(col)
        
        # 显示数据表格
        st.dataframe(
            data[display_columns].tail(50),
            use_container_width=True,
            height=400
        )
    
    def display_error(self, message: str):
        """
        显示错误信息
        
        Args:
            message: 错误信息
        """
        st.error(message)
    
    def display_success(self, message: str):
        """
        显示成功信息
        
        Args:
            message: 成功信息
        """
        st.success(message)
    
    def display_info(self, message: str):
        """
        显示信息
        
        Args:
            message: 信息内容
        """
        st.info(message)
