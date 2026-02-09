import baostock as bs
import pandas as pd
import logging
import time
import threading
import schedule
from datetime import datetime, timedelta
import random
import os
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='stock_tracker.log'
)
logger = logging.getLogger(__name__)

# 数据存储路径
DATA_DIR = 'stock_data'
STOCKS_DIR = os.path.join(DATA_DIR, 'stocks')

# 失败计数器
consecutive_failures = 0
MAX_CONSECUTIVE_FAILURES = 10
FAILURE_PAUSE_TIME = 60  # 失败暂停时间（秒）

def init_storage():
    """
    初始化存储目录
    """
    try:
        # 创建数据目录
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            logger.info(f"创建数据目录: {DATA_DIR}")
        
        # 创建股票目录
        if not os.path.exists(STOCKS_DIR):
            os.makedirs(STOCKS_DIR)
            logger.info(f"创建股票目录: {STOCKS_DIR}")
        
        logger.info("存储目录初始化成功")
    except Exception as e:
        logger.error(f"存储目录初始化失败: {str(e)}")

def get_stock_file_path(code):
    """
    获取股票文件路径
    """
    return os.path.join(STOCKS_DIR, f"{code}.json")

def save_stock_data_to_file(code, name, industry, area, kline_data, merge=False):
    """
    保存股票数据到JSON文件
    
    Args:
        code: 股票代码
        name: 股票名称
        industry: 行业
        area: 地区
        kline_data: K线数据 (DataFrame)
        merge: 是否与已有数据合并（增量更新）
    """
    try:
        file_path = get_stock_file_path(code)
        
        existing_kline = []
        if merge:
            # 读取已有数据
            stock_data = get_stock_data_from_file(code)
            if stock_data and stock_data.get('kline'):
                existing_kline = stock_data['kline']
                logger.debug(f"读取到已有K线数据，共 {len(existing_kline)} 条")
        
        # 准备数据
        stock_data = {
            'code': code,
            'name': name,
            'industry': industry,
            'area': area,
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'kline': existing_kline.copy() if merge else []
        }
        
        # 转换K线数据
        if not kline_data.empty:
            for index, row in kline_data.iterrows():
                try:
                    new_kline_item = {
                        'date': str(row.get('date', '')),
                        'open': float(row.get('open', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'close': float(row.get('close', 0)),
                        'volume': int(row.get('volume', 0))
                    }
                    
                    if merge:
                        # 增量更新：只添加日期比已有数据新的记录
                        new_date = new_kline_item['date']
                        if existing_kline:
                            last_date = existing_kline[-1].get('date', '')
                            if new_date > last_date:
                                stock_data['kline'].append(new_kline_item)
                                logger.debug(f"添加新K线数据，日期: {new_date}")
                            else:
                                logger.debug(f"跳过旧数据，日期: {new_date}, 最后日期: {last_date}")
                        else:
                            stock_data['kline'].append(new_kline_item)
                    else:
                        # 完全覆盖
                        stock_data['kline'].append(new_kline_item)
                except Exception as e:
                    logger.error(f"转换K线数据失败，代码: {code}, 错误: {str(e)}")
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stock_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"股票数据保存成功，代码: {code}, 文件: {file_path}, K线数量: {len(stock_data['kline'])}")
        return True
    except Exception as e:
        logger.error(f"保存股票数据失败，代码: {code}, 错误: {str(e)}")
        return False

def get_stock_data_from_file(code):
    """
    从JSON文件读取股票数据
    """
    try:
        file_path = get_stock_file_path(code)
        
        if not os.path.exists(file_path):
            logger.debug(f"股票数据文件不存在，代码: {code}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            stock_data = json.load(f)
        
        logger.debug(f"从文件读取股票数据成功，代码: {code}")
        return stock_data
    except Exception as e:
        logger.error(f"读取股票数据失败，代码: {code}, 错误: {str(e)}")
        return None

def convert_code_to_baostock(code):
    """
    将股票代码转换为BaoStock格式
    """
    if isinstance(code, str):
        code = code.strip()
        # 深圳股票 (000xxx, 001xxx, 002xxx, 003xxx, 300xxx)
        if code.startswith(('000', '001', '002', '003', '300')):
            return f"sz.{code}"
        # 上海股票 (600xxx, 601xxx, 603xxx, 605xxx, 688xxx)
        elif code.startswith(('600', '601', '603', '605', '688')):
            return f"sh.{code}"
        # 北京股票 (bj8xxxxx, bj9xxxxx)
        elif code.startswith(('bj8', 'bj9')):
            return f"bj.{code}"
        # 已经是BaoStock格式
        elif '.' in code:
            return code
        else:
            return f"sh.{code}"
    return code

def get_all_stocks():
    """
    获取所有可申请的股票列表
    """
    global consecutive_failures
    try:
        logger.info("开始获取所有股票列表")
        
        # 使用BaoStock获取股票列表
        lg = bs.login()
        if lg.error_code != '0':
            logger.error(f"BaoStock登录失败: {lg.error_msg}")
            consecutive_failures += 1
            return pd.DataFrame()
        
        rs = bs.query_all_stock(day=datetime.now().strftime("%Y-%m-%d"))
        if rs.error_code != '0':
            logger.error(f"获取股票列表失败: {rs.error_msg}")
            bs.logout()
            consecutive_failures += 1
            return pd.DataFrame()
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if data_list:
            stock_list = pd.DataFrame(data_list, columns=rs.fields)
            logger.info(f"获取股票列表成功，共 {len(stock_list)} 只股票")
            consecutive_failures = 0
            return stock_list
        else:
            logger.error("股票列表为空")
            consecutive_failures += 1
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"获取股票列表失败: {str(e)}")
        consecutive_failures += 1
        return pd.DataFrame()

def fetch_stock_kline_from_api(symbol, start_date=None, end_date=None, adjust="qfq", max_retries=3):
    """
    从BaoStock API获取股票K线数据
    """
    global consecutive_failures
    
    logger.debug(f"开始获取股票数据，代码: {symbol}, 开始日期: {start_date}, 结束日期: {end_date}, 复权类型: {adjust}")
    
    # 转换为BaoStock格式
    baostock_code = convert_code_to_baostock(symbol)
    
    # 如果没有提供日期，使用默认值
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        # 默认获取最近60天的数据
        start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    
    logger.debug(f"使用日期范围: {start_date} 到 {end_date}, BaoStock代码: {baostock_code}")
    
    # 转换复权类型
    adjustflag = "3"  # 默认前复权
    if adjust == "hfq":
        adjustflag = "2"  # 后复权
    elif adjust == "":
        adjustflag = "1"  # 不复权
    
    # 尝试多次调用API
    for attempt in range(max_retries):
        try:
            # 登录BaoStock
            lg = bs.login()
            if lg.error_code != '0':
                raise Exception(f"BaoStock登录失败: {lg.error_msg}")
            
            # 获取K线数据
            rs = bs.query_history_k_data_plus(
                baostock_code,
                "date,open,high,low,close,volume",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag=adjustflag
            )
            
            if rs.error_code != '0':
                bs.logout()
                raise Exception(f"查询失败: {rs.error_msg}")
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            bs.logout()
            
            if data_list:
                df = pd.DataFrame(data_list, columns=rs.fields)
                df['open'] = pd.to_numeric(df['open'])
                df['high'] = pd.to_numeric(df['high'])
                df['low'] = pd.to_numeric(df['low'])
                df['close'] = pd.to_numeric(df['close'])
                df['volume'] = pd.to_numeric(df['volume'])
                
                logger.debug(f"获取数据成功，数据行数: {len(df)}")
                consecutive_failures = 0  # 重置失败计数器
                return df
            else:
                bs.logout()
                raise Exception("未获取到股票数据")
                
        except Exception as e:
            logger.error(f"第 {attempt + 1} 次调用失败: {str(e)}")
            if attempt < max_retries - 1:
                # 随机延迟，避免请求过于集中
                delay = random.uniform(1, 3)
                logger.info(f"等待 {delay:.1f} 秒后重试...")
                time.sleep(delay)
            else:
                logger.error(f"达到最大重试次数 {max_retries}，获取股票数据失败")
                consecutive_failures += 1
                return pd.DataFrame()

def get_last_kline_date(code):
    """
    获取股票最后一条K线数据的日期
    """
    try:
        stock_data = get_stock_data_from_file(code)
        if stock_data and stock_data.get('kline'):
            kline_list = stock_data['kline']
            if kline_list:
                last_date = kline_list[-1].get('date', '')
                if last_date:
                    logger.debug(f"股票 {code} 最后K线日期: {last_date}")
                    return last_date
        return None
    except Exception as e:
        logger.error(f"获取股票最后K线日期失败，代码: {code}, 错误: {str(e)}")
        return None

def fetch_and_save_stock_data(code, name="", industry="", area="", incremental=False):
    """
    抓取并保存股票数据
    
    Args:
        code: 股票代码
        name: 股票名称
        industry: 行业
        area: 地区
        incremental: 是否增量更新（仅获取新数据）
    """
    global consecutive_failures
    
    logger.info(f"开始抓取股票数据，代码: {code}, 名称: {name}, 增量更新: {incremental}")
    
    # 如果是增量更新，获取最后一条K线数据的日期
    start_date = None
    if incremental:
        last_date = get_last_kline_date(code)
        if last_date:
            # 从最后一条数据的下一天开始获取
            last_date_obj = datetime.strptime(last_date, "%Y-%m-%d")
            next_date = last_date_obj + timedelta(days=1)
            start_date = next_date.strftime("%Y-%m-%d")
            
            # 检查起始日期是否超过今天
            today = datetime.now().strftime("%Y-%m-%d")
            if start_date > today:
                logger.info(f"股票数据已是最新，最后日期: {last_date}, 无需更新")
                return True
            
            logger.info(f"增量更新，从 {start_date} 开始获取数据")
        else:
            logger.warning(f"无法获取最后K线日期，将获取全部数据")
    
    # 从API获取数据
    kline_data = fetch_stock_kline_from_api(code, start_date=start_date)
    
    if not kline_data.empty:
        # 保存到文件（增量更新时使用merge模式）
        if save_stock_data_to_file(code, name, industry, area, kline_data, merge=incremental):
            logger.info(f"股票数据抓取并保存成功，代码: {code}")
            return True
        else:
            logger.error(f"股票数据保存失败，代码: {code}")
            return False
    else:
        logger.error(f"股票数据抓取失败，代码: {code}")
        return False

def continuous_fetch_worker():
    """
    持续抓取工作线程
    """
    global consecutive_failures
    
    logger.info("启动持续抓取工作线程")
    
    # 获取所有股票列表
    stock_list = get_all_stocks()
    if stock_list.empty:
        logger.error("没有获取到股票列表")
        return
    
    try:
        # 遍历所有股票
        for index, row in stock_list.iterrows():
            try:
                # 检查连续失败次数
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.warning(f"连续失败 {consecutive_failures} 次，暂停 {FAILURE_PAUSE_TIME} 秒...")
                    time.sleep(FAILURE_PAUSE_TIME)
                    consecutive_failures = 0
                
                code = row.get('code', '')
                name = row.get('code_name', '')
                industry = row.get('industry', '')
                area = row.get('area', '')
                
                # 检查是否已经抓取过
                file_path = get_stock_file_path(code)
                if os.path.exists(file_path):
                    # 已有股票：增量更新K线数据
                    logger.info(f"已有股票，进行增量更新，代码: {code}")
                    success = fetch_and_save_stock_data(code, name, industry, area, incremental=True)
                else:
                    # 全新股票：添加完整数据
                    logger.info(f"全新股票，添加完整数据，代码: {code}")
                    success = fetch_and_save_stock_data(code, name, industry, area, incremental=False)
                
                if not success:
                    logger.warning(f"跳过失败的股票，代码: {code}")
                
                # 随机延迟，避免请求过于集中
                time.sleep(random.uniform(0.2, 0.8))
                
                # 每处理100只股票记录一次
                if (index + 1) % 100 == 0:
                    logger.info(f"已检查 {index + 1}/{len(stock_list)} 只股票")
                    
            except Exception as e:
                logger.error(f"处理股票数据失败，代码: {code}, 错误: {str(e)}")
                consecutive_failures += 1
        
        logger.info(f"持续抓取完成，共处理 {len(stock_list)} 只股票")
    except Exception as e:
        logger.error(f"持续抓取失败: {str(e)}")

def refresh_all_stocks():
    """
    刷新所有股票数据（增量更新）
    """
    global consecutive_failures
    
    logger.info("开始刷新所有股票数据（增量更新）")
    
    try:
        # 获取所有已保存的股票文件
        stock_files = [f for f in os.listdir(STOCKS_DIR) if f.endswith('.json')]
        
        logger.info(f"需要刷新 {len(stock_files)} 只股票")
        
        # 刷新每只股票的数据
        for index, filename in enumerate(stock_files):
            try:
                # 检查连续失败次数
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.warning(f"连续失败 {consecutive_failures} 次，暂停 {FAILURE_PAUSE_TIME} 秒...")
                    time.sleep(FAILURE_PAUSE_TIME)
                    consecutive_failures = 0
                
                code = filename.replace('.json', '')
                
                # 读取现有数据
                stock_data = get_stock_data_from_file(code)
                if stock_data:
                    name = stock_data.get('name', '')
                    industry = stock_data.get('industry', '')
                    area = stock_data.get('area', '')
                else:
                    name = ""
                    industry = ""
                    area = ""
                
                # 增量更新：只获取新数据
                success = fetch_and_save_stock_data(code, name, industry, area, incremental=True)
                
                if not success:
                    logger.warning(f"跳过失败的股票，代码: {code}")
                
                # 随机延迟，避免请求过于集中
                time.sleep(random.uniform(0.2, 0.6))
                
                # 每处理50只股票记录一次
                if (index + 1) % 50 == 0:
                    logger.info(f"已刷新 {index + 1}/{len(stock_files)} 只股票")
                    
            except Exception as e:
                logger.error(f"刷新股票数据失败，代码: {code}, 错误: {str(e)}")
                consecutive_failures += 1
        
        logger.info(f"所有股票数据刷新完成，共处理 {len(stock_files)} 只股票")
    except Exception as e:
        logger.error(f"刷新所有股票数据失败: {str(e)}")

def job_refresh_all():
    """
    定时刷新任务
    """
    logger.info("定时刷新任务开始执行")
    refresh_all_stocks()
    logger.info("定时刷新任务执行完成")

def start_tracker():
    """
    启动跟踪服务
    """
    # 初始化存储目录
    init_storage()
    
    # 启动持续抓取线程
    fetch_thread = threading.Thread(target=continuous_fetch_worker, daemon=True)
    fetch_thread.start()
    logger.info("持续抓取线程已启动")
    
    # 设置定时任务
    # 每天早上9:30
    schedule.every().day.at("09:30").do(job_refresh_all)
    # 每天中午12:30
    schedule.every().day.at("12:30").do(job_refresh_all)
    # 每天晚上18:30
    schedule.every().day.at("18:30").do(job_refresh_all)
    
    logger.info("定时调度器已启动，每天早中晚各执行一次")
    
    # 循环执行
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_tracker()
