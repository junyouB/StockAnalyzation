import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.data_fetcher import DataFetcher
from data.indicators import Indicators
from data.signals import Signals
from frontend.visualization import Visualization
from frontend.ui import UI

class StockAnalysisApp:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.indicators = Indicators()
        self.signals = Signals()
        self.visualization = Visualization()
        self.ui = UI()
    
    def run(self):
        """
        运行应用
        """
        # 设置页面配置
        st.set_page_config(
            page_title="股票技术分析工具",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 页面标题
        st.title("📈 股票技术分析工具")
        st.markdown("---")
        
        # 侧边栏 - 股票选择和参数设置
        with st.sidebar:
            st.header("参数设置")
            
            # 股票代码输入
            symbol = st.text_input("股票代码", value="AAPL", placeholder="例如: AAPL, MSFT, GOOGL")
            
            # 时间周期选择
            period = st.selectbox(
                "时间周期",
                options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                index=5
            )
            
            # 数据间隔选择
            interval = st.selectbox(
                "数据间隔",
                options=["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"],
                index=8
            )
            
            # 指标选择
            st.header("指标选择")
            show_ma = st.checkbox("移动平均线", value=True)
            show_macd = st.checkbox("MACD", value=True)
            show_rsi = st.checkbox("RSI", value=True)
            show_bollinger = st.checkbox("布林带", value=True)
            
            # 执行按钮
            analyze_button = st.button("开始分析")
        
        # 主内容区
        if analyze_button:
            # 显示加载状态
            with st.spinner("正在获取数据并分析..."):
                # 获取数据
                data = self.data_fetcher.get_stock_data(symbol, period, interval)
                
                if data is None:
                    st.error(f"无法获取股票 {symbol} 的数据，请检查股票代码是否正确。")
                    return
                
                # 计算指标
                data = self.indicators.calculate_all_indicators(data)
                
                # 生成信号
                data = self.signals.generate_combined_signals(data)
                
                # 获取最新信号
                latest_signal = self.signals.get_latest_signal(data)
                
                # 显示信号
                self.ui.display_signal(latest_signal, symbol)
                
                # 显示数据概览
                self.ui.display_data_overview(data)
                
                # 可视化图表
                col1, col2 = st.columns(2)
                
                with col1:
                    # K线图
                    st.subheader("K线图")
                    self.visualization.plot_candlestick(data, show_ma, show_bollinger)
                
                with col2:
                    # 指标图
                    st.subheader("技术指标")
                    self.visualization.plot_indicators(data, show_macd, show_rsi)
                
                # 信号分析
                st.subheader("信号分析")
                self.ui.display_signal_analysis(data)
                
                # 数据表格
                st.subheader("原始数据")
                self.ui.display_data_table(data)
        
        # 页脚
        st.markdown("---")
        st.markdown("© 2024 股票技术分析工具 | 数据来源: Yahoo Finance")

if __name__ == "__main__":
    app = StockAnalysisApp()
    app.run()
