import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

class Visualization:
    def __init__(self):
        pass
    
    def plot_candlestick(self, data: pd.DataFrame, show_ma: bool = True, show_bollinger: bool = True):
        """
        绘制K线图
        
        Args:
            data: 包含股票数据的DataFrame
            show_ma: 是否显示移动平均线
            show_bollinger: 是否显示布林带
        """
        fig = go.Figure()
        
        # 添加K线
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='K线'
        ))
        
        # 添加移动平均线
        if show_ma:
            for ma in ['MA5', 'MA10', 'MA20', 'MA50', 'MA200']:
                if ma in data.columns:
                    fig.add_trace(go.Scatter(
                        x=data.index,
                        y=data[ma],
                        name=ma,
                        line=dict(width=1)
                    ))
        
        # 添加布林带
        if show_bollinger and 'BB_Upper' in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['BB_Upper'],
                name='布林带上轨',
                line=dict(width=1, color='gray', dash='dash')
            ))
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['BB_Middle'],
                name='布林带中轨',
                line=dict(width=1, color='gray')
            ))
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['BB_Lower'],
                name='布林带下轨',
                line=dict(width=1, color='gray', dash='dash')
            ))
        
        # 图表布局
        fig.update_layout(
            title='K线图',
            xaxis_title='日期',
            yaxis_title='价格',
            xaxis_rangeslider_visible=False,
            height=600,
            template='plotly_white'
        )
        
        # 显示图表
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_indicators(self, data: pd.DataFrame, show_macd: bool = True, show_rsi: bool = True):
        """
        绘制技术指标图
        
        Args:
            data: 包含指标数据的DataFrame
            show_macd: 是否显示MACD
            show_rsi: 是否显示RSI
        """
        # 确定子图数量
        rows = 0
        if show_macd:
            rows += 1
        if show_rsi:
            rows += 1
        
        if rows == 0:
            return
        
        # 创建子图
        fig = make_subplots(
            rows=rows, 
            cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=[title for title, show in zip(['MACD', 'RSI'], [show_macd, show_rsi]) if show]
        )
        
        # 当前行索引
        current_row = 1
        
        # 添加MACD
        if show_macd and all(col in data.columns for col in ['MACD', 'Signal', 'Histogram']):
            # MACD线
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['MACD'],
                name='MACD',
                line=dict(color='blue')
            ), row=current_row, col=1)
            
            # 信号线
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['Signal'],
                name='Signal',
                line=dict(color='red')
            ), row=current_row, col=1)
            
            # 柱状图
            fig.add_trace(go.Bar(
                x=data.index,
                y=data['Histogram'],
                name='Histogram',
                marker_color=data['Histogram'].apply(lambda x: 'green' if x > 0 else 'red')
            ), row=current_row, col=1)
            
            current_row += 1
        
        # 添加RSI
        if show_rsi and 'RSI' in data.columns:
            # RSI线
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data['RSI'],
                name='RSI',
                line=dict(color='purple')
            ), row=current_row, col=1)
            
            # 超买超卖线
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
        
        # 图表布局
        fig.update_layout(
            height=600,
            template='plotly_white',
            showlegend=True
        )
        
        # 显示图表
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_signal_history(self, data: pd.DataFrame):
        """
        绘制信号历史图
        
        Args:
            data: 包含信号数据的DataFrame
        """
        if 'Final_Signal' not in data.columns:
            return
        
        fig = go.Figure()
        
        # 信号数据
        signal_data = data[data['Final_Signal'] != 0].copy()
        
        # 买入信号
        buy_signals = signal_data[signal_data['Final_Signal'] == 1]
        if not buy_signals.empty:
            fig.add_trace(go.Scatter(
                x=buy_signals.index,
                y=buy_signals['Close'],
                mode='markers',
                name='买入信号',
                marker=dict(color='green', size=10, symbol='triangle-up')
            ))
        
        # 卖出信号
        sell_signals = signal_data[signal_data['Final_Signal'] == -1]
        if not sell_signals.empty:
            fig.add_trace(go.Scatter(
                x=sell_signals.index,
                y=sell_signals['Close'],
                mode='markers',
                name='卖出信号',
                marker=dict(color='red', size=10, symbol='triangle-down')
            ))
        
        # 价格线
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            name='价格',
            line=dict(color='blue', width=1)
        ))
        
        # 图表布局
        fig.update_layout(
            title='信号历史',
            xaxis_title='日期',
            yaxis_title='价格',
            height=500,
            template='plotly_white'
        )
        
        # 显示图表
        st.plotly_chart(fig, use_container_width=True)
