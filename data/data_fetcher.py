import akshare as ak
import pandas as pd

def fetch_stock_kline(symbol, start_date="20230101", end_date="20240101", adjust="qfq"):
    """
    获取股票K线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期，格式为"YYYYMMDD"
        end_date: 结束日期，格式为"YYYYMMDD"
        adjust: 复权类型，可选值："qfq"(前复权), "hfq"(后复权), ""(不复权)
    
    Returns:
        list: 格式化后的股票K线数据列表
    """
    try:
        # 使用AKShare获取股票K线数据
        stock_zh_a_hist_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        # 转换为前端需要的格式
        data = []
        for index, row in stock_zh_a_hist_df.iterrows():
            data.append({
                'date': row['日期'],
                'open': row['开盘'],
                'high': row['最高'],
                'low': row['最低'],
                'close': row['收盘'],
                'volume': row['成交量']
            })
        
        return data
    except Exception as e:
        raise Exception(f"获取股票数据失败: {str(e)}")
