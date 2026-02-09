import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def fetch_stock_kline(symbol, start_date=None, end_date=None, adjust="qfq"):
    """
    获取股票K线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期，格式为"YYYYMMDD"
        end_date: 结束日期，格式为"YYYYMMDD"
        adjust: 复权类型，可选值："qfq"(前复权), "hfq"(后复权), ""(不复权)
        max_retries: 最大重试次数
    
    Returns:
        list: 格式化后的股票K线数据列表
    """
    try:
        # 如果没有提供日期，使用默认值
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            # 默认获取最近60天的数据
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
        
        # 验证股票代码格式
        if not symbol or not isinstance(symbol, str):
            raise Exception("股票代码格式错误")
        
        # 使用AKShare获取股票K线数据
        stock_zh_a_hist_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        # 检查数据是否为空
        if stock_zh_a_hist_df.empty:
            raise Exception("未获取到股票数据，请检查股票代码是否正确")
        
        # 转换为前端需要的格式
        data = []
        for index, row in stock_zh_a_hist_df.iterrows():
            data.append({
                'date': str(row['日期']),
                'open': float(row['开盘']),
                'high': float(row['最高']),
                'low': float(row['最低']),
                'close': float(row['收盘']),
                'volume': int(row['成交量'])
            })
        
        return data
    except Exception as e:
        raise Exception(f"获取股票数据失败: {str(e)}")
