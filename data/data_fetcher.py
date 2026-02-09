import akshare as ak
import pandas as pd
import logging
import time

# 配置日志
logging.basicConfig(level=logging.DEBUG)
def fetch_stock_kline(symbol, start_date="20230101", end_date="20240101", adjust="qfq", max_retries=3):
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
    retry_count = 0
    while retry_count < max_retries:
        try:
            logging.debug(f"开始获取股票数据 (尝试 {retry_count + 1}/{max_retries}): {symbol}, 开始日期: {start_date}, 结束日期: {end_date}")
            # 使用AKShare获取股票K线数据
            stock_zh_a_hist_df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            logging.debug(f"获取数据成功，共{len(stock_zh_a_hist_df)}条记录")
            
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
            
            logging.debug(f"数据转换成功，返回{len(data)}条记录")
            return data
        except Exception as e:
            logging.error(f"获取股票数据失败: {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                logging.info(f"等待1秒后重试...")
                time.sleep(1)  # 减少等待时间
            else:
                # 返回更详细的错误信息，包括重试次数
                raise Exception(f"获取股票数据失败，已重试{max_retries}次: {str(e)}")
