import baostock as bs
import pandas as pd
from datetime import datetime, timedelta
import logging
import time
import threading
import json
import os

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 数据存储路径
# 获取项目根目录（data目录的父目录）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data', 'stock_data')
STOCKS_DIR = os.path.join(DATA_DIR, 'stocks')

# 股票代码和名称映射缓存
_stock_code_map = None
_stock_name_map = None

def load_stock_mappings():
    """
    从本地文件加载股票代码和名称的映射
    """
    global _stock_code_map, _stock_name_map
    
    if _stock_code_map is not None and _stock_name_map is not None:
        logger.debug(f"使用缓存的股票映射，代码映射: {len(_stock_code_map)}, 名称映射: {len(_stock_name_map)}")
        return _stock_code_map, _stock_name_map
    
    _stock_code_map = {}
    _stock_name_map = {}
    
    # 用于处理短代码冲突
    short_code_conflicts = {}
    
    try:
        if not os.path.exists(STOCKS_DIR):
            logger.warning(f"股票数据目录不存在: {STOCKS_DIR}")
            return _stock_code_map, _stock_name_map
        
        logger.info(f"开始加载股票映射，目录: {STOCKS_DIR}")
        
        # 遍历所有股票文件
        for filename in os.listdir(STOCKS_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(STOCKS_DIR, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        stock_data = json.load(f)
                    
                    code = stock_data.get('code', '')
                    name = stock_data.get('name', '')
                    
                    if code:
                        # 代码 -> 名称映射（支持多种格式）
                        _stock_code_map[code] = name
                        # 也支持不带前缀的代码
                        if '.' in code:
                            short_code = code.split('.')[1]
                            # 记录短代码冲突
                            if short_code in short_code_conflicts:
                                short_code_conflicts[short_code].append(code)
                            else:
                                short_code_conflicts[short_code] = [code]
                    
                    if name:
                        # 名称 -> 代码映射
                        _stock_name_map[name] = code
                
                except Exception as e:
                    logger.error(f"读取股票文件失败: {filename}, 错误: {str(e)}")
        
        # 处理短代码冲突，优先选择股票（排除指数）
        for short_code, codes in short_code_conflicts.items():
            if len(codes) > 1:
                # 有冲突，优先选择股票（排除指数）
                stock_code = None
                for code in codes:
                    name = _stock_code_map.get(code, '')
                    # 如果名称不包含"指数"，则认为是股票
                    if '指数' not in name:
                        stock_code = code
                        break
                
                # 如果所有都是指数，选择第一个
                if stock_code is None:
                    stock_code = codes[0]
                
                # 更新映射，使用优先选择的代码
                _stock_code_map[short_code] = _stock_code_map[stock_code]
                logger.debug(f"短代码冲突 {short_code}: {codes} -> 选择 {stock_code} ({_stock_code_map[stock_code]})")
        
        logger.info(f"加载股票映射成功，代码映射: {len(_stock_code_map)}, 名称映射: {len(_stock_name_map)}")
        if len(_stock_name_map) > 0:
            logger.debug(f"名称映射示例: {list(_stock_name_map.items())[:5]}")
    except Exception as e:
        logger.error(f"加载股票映射失败: {str(e)}")
    
    return _stock_code_map, _stock_name_map

def resolve_stock_symbol(symbol):
    """
    解析股票符号，支持代码或名称
    
    Args:
        symbol: 股票代码（如 "000001", "sh.600000"）或股票名称（如 "浦发银行"）
    
    Returns:
        str: 标准化的BaoStock格式代码（如 "sh.600000"），如果找不到返回None
    """
    code_map, name_map = load_stock_mappings()
    
    # 如果已经是BaoStock格式，直接返回
    if '.' in symbol:
        return symbol
    
    # 检查是否为中文名称
    is_chinese_name = any('\u4e00' <= char <= '\u9fff' for char in symbol)
    
    # 尝试从代码映射中查找
    if symbol in code_map:
        # 如果映射值是名称，需要反向查找
        mapped_value = code_map[symbol]
        if mapped_value in name_map:
            return name_map[mapped_value]
        # 如果映射值本身就是代码
        if '.' in mapped_value:
            return mapped_value
    
    # 尝试从名称映射中查找（精确匹配）
    if symbol in name_map:
        return name_map[symbol]
    
    # 尝试模糊匹配名称
    for name, code in name_map.items():
        if symbol in name:
            logger.info(f"模糊匹配: '{symbol}' -> '{name}' ({code})")
            return code
    
    # 如果都不匹配
    if is_chinese_name:
        # 如果是中文名称但找不到映射，返回None
        logger.error(f"未找到股票名称 '{symbol}' 的映射")
        return None
    else:
        # 如果是代码，尝试直接转换为BaoStock格式
        logger.warning(f"未找到股票代码 '{symbol}' 的映射，尝试转换为BaoStock格式")
        return convert_code_to_baostock(symbol)

def search_stocks(keyword, limit=20):
    """
    搜索股票，支持代码和名称的模糊搜索
    
    Args:
        keyword: 搜索关键词（代码或名称）
        limit: 返回结果数量限制
    
    Returns:
        list: 匹配的股票列表，每个元素包含 code, name
    """
    code_map, name_map = load_stock_mappings()
    results = []
    
    # 搜索代码
    for code, name in code_map.items():
        if keyword.lower() in code.lower():
            # 找到对应的完整代码
            full_code = None
            for n, c in name_map.items():
                if n == name:
                    full_code = c
                    break
            
            if full_code and not any(r['code'] == full_code for r in results):
                results.append({
                    'code': full_code,
                    'name': name
                })
    
    # 搜索名称
    for name, code in name_map.items():
        if keyword.lower() in name.lower():
            if not any(r['code'] == code for r in results):
                results.append({
                    'code': code,
                    'name': name
                })
    
    # 限制返回数量
    return results[:limit]

def get_stock_file_path(code):
    """
    获取股票文件路径
    """
    return os.path.join(STOCKS_DIR, f"{code}.json")

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

def get_stock_data_from_file(symbol):
    """
    从本地JSON文件获取股票数据
    
    Args:
        symbol: 股票代码
    
    Returns:
        list: 格式化后的股票K线数据列表，如果文件中没有数据则返回None
    """
    try:
        file_path = get_stock_file_path(symbol)
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            stock_data = json.load(f)
        
        # 获取K线数据
        kline_data = stock_data.get('kline', [])
        
        if not kline_data:
            return None
        
        logger.debug(f"从文件获取数据成功，代码: {symbol}, 数据行数: {len(kline_data)}")
        return kline_data
    except Exception as e:
        logger.error(f"从文件获取数据失败，代码: {symbol}, 错误: {str(e)}")
        return None

def fetch_stock_kline_from_api(symbol, start_date=None, end_date=None, adjust="qfq", max_retries=3):
    """
    从BaoStock API获取股票K线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期，格式为"YYYY-MM-DD"
        end_date: 结束日期，格式为"YYYY-MM-DD"
        adjust: 复权类型，可选值："qfq"(前复权), "hfq"(后复权), ""(不复权)
        max_retries: 最大重试次数
    
    Returns:
        DataFrame: 股票K线数据
    """
    logger.debug(f"开始从API获取股票数据，代码: {symbol}, 开始日期: {start_date}, 结束日期: {end_date}, 复权类型: {adjust}")
    
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
                return df
            else:
                bs.logout()
                raise Exception("未获取到股票数据")
                
        except Exception as e:
            logger.error(f"第 {attempt + 1} 次调用失败: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"等待 2 秒后重试...")
                time.sleep(2)
            else:
                logger.error(f"达到最大重试次数 {max_retries}，获取股票数据失败")
                raise

def save_stock_data_to_file(code, name, industry, area, kline_data):
    """
    保存股票数据到JSON文件
    """
    try:
        file_path = get_stock_file_path(code)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 准备数据
        stock_data = {
            'code': code,
            'name': name,
            'industry': industry,
            'area': area,
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'kline': []
        }
        
        # 转换K线数据
        if not kline_data.empty:
            for index, row in kline_data.iterrows():
                try:
                    stock_data['kline'].append({
                        'date': str(row.get('date', '')),
                        'open': float(row.get('open', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'close': float(row.get('close', 0)),
                        'volume': int(row.get('volume', 0))
                    })
                except Exception as e:
                    logger.error(f"转换K线数据失败，代码: {code}, 错误: {str(e)}")
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stock_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"股票数据保存成功，代码: {code}, 文件: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存股票数据失败，代码: {code}, 错误: {str(e)}")
        return False

def fetch_and_save_stock_data(code, name="", industry="", area=""):
    """
    从API获取并保存股票数据到文件
    """
    logger.info(f"开始抓取并保存股票数据，代码: {code}, 名称: {name}")
    
    try:
        # 从API获取数据
        kline_data = fetch_stock_kline_from_api(code)
        
        if not kline_data.empty:
            # 保存到文件
            if save_stock_data_to_file(code, name, industry, area, kline_data):
                logger.info(f"股票数据抓取并保存成功，代码: {code}")
                return True
            else:
                logger.error(f"股票数据保存失败，代码: {code}")
                return False
        else:
            logger.error(f"股票数据抓取失败，代码: {code}")
            return False
    except Exception as e:
        logger.error(f"抓取并保存股票数据失败，代码: {code}, 错误: {str(e)}")
        return False

def fetch_stock_kline(symbol, start_date=None, end_date=None, adjust="qfq", max_retries=3):
    """
    获取股票K线数据（优先从本地JSON文件获取）
    
    Args:
        symbol: 股票代码（如 "000001", "sh.600000"）或股票名称（如 "浦发银行"）
        start_date: 开始日期，格式为"YYYY-MM-DD"
        end_date: 结束日期，格式为"YYYY-MM-DD"
        adjust: 复权类型，可选值："qfq"(前复权), "hfq"(后复权), ""(不复权)
        max_retries: 最大重试次数
    
    Returns:
        list: 格式化后的股票K线数据列表
    """
    logger.debug(f"开始获取股票数据，代码/名称: {symbol}, 开始日期: {start_date}, 结束日期: {end_date}, 复权类型: {adjust}")
    
    # 解析股票符号，支持代码或名称
    resolved_symbol = resolve_stock_symbol(symbol)
    
    if resolved_symbol is None:
        raise Exception(f"未找到股票 '{symbol}'，请检查股票代码或名称是否正确")
    
    logger.info(f"解析股票符号: '{symbol}' -> '{resolved_symbol}'")
    
    # 首先尝试从本地JSON文件获取
    data = get_stock_data_from_file(resolved_symbol)
    
    if data:
        logger.debug(f"从本地JSON文件获取数据成功，代码: {resolved_symbol}")
        return data
    
    # 文件中没有数据，从API获取
    logger.info(f"本地JSON文件中没有股票数据，从API获取，代码: {resolved_symbol}")
    
    try:
        # 从API获取数据
        kline_data = fetch_stock_kline_from_api(resolved_symbol, start_date, end_date, adjust, max_retries)
        
        # 检查数据是否为空
        if kline_data.empty:
            raise Exception("未获取到股票数据")
        
        # 转换为前端需要的格式
        data = []
        for index, row in kline_data.iterrows():
            data.append({
                'date': str(row['date']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
        
        if not data:
            raise Exception("数据处理后为空")
        
        # 异步保存到文件（不阻塞API响应）
        def save_to_file_async():
            try:
                # 获取股票基本信息
                lg = bs.login()
                if lg.error_code == '0':
                    rs = bs.query_stock_basic(code=resolved_symbol)
                    if rs.error_code == '0':
                        data_list = []
                        while (rs.error_code == '0') & rs.next():
                            data_list.append(rs.get_row_data())
                        if data_list:
                            stock_info = pd.DataFrame(data_list, columns=rs.fields)
                            if not stock_info.empty:
                                name = stock_info.iloc[0].get('code_name', '')
                                industry = stock_info.iloc[0].get('industry', '')
                                area = stock_info.iloc[0].get('area', '')
                                save_stock_data_to_file(resolved_symbol, name, industry, area, kline_data)
                    bs.logout()
            except Exception as e:
                logger.error(f"异步保存数据失败，代码: {resolved_symbol}, 错误: {str(e)}")
        
        # 启动异步保存线程
        save_thread = threading.Thread(target=save_to_file_async, daemon=True)
        save_thread.start()
        
        logger.debug(f"数据处理完成，返回 {len(data)} 条记录")
        return data
    except Exception as e:
        logger.error(f"获取股票数据失败，代码: {resolved_symbol}, 错误: {str(e)}")
        raise
