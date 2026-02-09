import akshare as ak
import pandas as pd
import requests
from datetime import datetime, timedelta
import json

def fetch_stock_kline_eastmoney(symbol, start_date=None, end_date=None):
    """
    使用东方财富网获取股票K线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期，格式为"YYYY-MM-DD"
        end_date: 结束日期，格式为"YYYY-MM-DD"
    
    Returns:
        list: 格式化后的股票K线数据列表
    """
    try:
        # 如果没有提供日期，使用默认值
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            # 默认获取最近60天的数据
            start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        
        # 验证股票代码格式
        if not symbol or not isinstance(symbol, str):
            raise Exception("股票代码格式错误")
        
        # 构建东方财富网API请求
        # 转换股票代码格式：000001 -> 0.000001
        if len(symbol) == 6:
            secid = f"0.{symbol}"
        else:
            secid = symbol
        
        # 东方财富网API
        url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
        params = {
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116',
            'ut': '7eea3edcaed734bea9cbfc24409ed989',
            'klt': '101',  # 日K
            'fqt': '1',     # 前复权
            'secid': secid,
            'beg': start_date.replace('-', ''),
            'end': end_date.replace('-', '')
        }
        
        # 发送请求
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        # 解析JSON数据
        result = response.json()
        
        # 检查数据是否存在
        if not result or 'data' not in result or not result['data']:
            raise Exception("未获取到股票数据，请检查股票代码是否正确")
        
        # 转换为前端需要的格式
        data = []
        kline_data = result['data']
        
        for item in kline_data:
            data.append({
                'date': item['k'],  # 日期
                'open': float(item['f1']),  # 开盘价
                'close': float(item['f2']),  # 收盘价
                'low': float(item['f3']),   # 最低价
                'high': float(item['f4']),  # 最高价
                'volume': int(item['f5'])   # 成交量
            })
        
        return data
    except Exception as e:
        raise Exception(f"获取股票数据失败: {str(e)}")

def fetch_stock_kline(symbol, start_date=None, end_date=None, adjust="qfq", use_eastmoney=True):
    """
    获取股票K线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期，格式为"YYYYMMDD"
        end_date: 结束日期，格式为"YYYYMMDD"
        adjust: 复权类型，可选值："qfq"(前复权), "hfq"(后复权), ""(不复权)
        use_eastmoney: 是否使用东方财富网数据源
    
    Returns:
        list: 格式化后的股票K线数据列表
    """
    try:
        # 如果使用东方财富网数据源
        if use_eastmoney:
            try:
                return fetch_stock_kline_eastmoney(symbol, start_date, end_date)
            except Exception as e:
                print(f"东方财富网数据源失败，切换到AKShare: {str(e)}")
                # 自动切换到AKShare数据源
                use_eastmoney = False
        
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
