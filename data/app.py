from flask import Flask, jsonify, request
from flask_cors import CORS
from data_fetcher import fetch_stock_kline, search_stocks, resolve_stock_symbol, load_stock_mappings
from curve_analyzer import CurveAnalyzer
import json
import os
import time
import numpy as np
import glob
import requests

app = Flask(__name__)
CORS(app)

@app.route('/api/stock/kline/<symbol>', methods=['GET'])
def get_stock_kline(symbol):
    try:
        # 解析股票代码
        resolved_symbol = resolve_stock_symbol(symbol)
        
        # 使用分离的模块获取股票K线数据
        data = fetch_stock_kline(resolved_symbol)
        
        # 获取股票名称
        code_map, name_map = load_stock_mappings()
        stock_name = code_map.get(resolved_symbol, '')
        
        return jsonify({
            'success': True,
            'data': data,
            'symbol': resolved_symbol,
            'name': stock_name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stock/search', methods=['GET'])
def search_stock():
    try:
        # 获取搜索关键词
        keyword = request.args.get('keyword', '')
        limit = request.args.get('limit', 20, type=int)
        
        if not keyword:
            return jsonify({
                'success': False,
                'error': '请提供搜索关键词'
            }), 400
        
        # 搜索股票
        results = search_stocks(keyword, limit)
        
        return jsonify({
            'success': True,
            'data': results,
            'keyword': keyword,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stock/analyze/<symbol>', methods=['GET'])
def analyze_stock_data(symbol):
    try:
        # 读取test.json文件
        test_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test.json')
        with open(test_json_path, 'r', encoding='utf-8') as f:
            analyze_data = json.load(f)
        
        # 更新股票代码
        analyze_data['stock_info']['symbol'] = symbol
        analyze_data['stock_data']['stock_info']['symbol'] = symbol
        
        return jsonify(analyze_data)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stock/AnalyzeAllData/<symbol>', methods=['GET'])
def analyze_all_data(symbol):
    try:
        # 读取test.json文件
        test_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test.json')
        with open(test_json_path, 'r', encoding='utf-8') as f:
            analyze_data = json.load(f)
        
        # 更新股票代码
        analyze_data['stock_info']['symbol'] = symbol
        analyze_data['stock_data']['stock_info']['symbol'] = symbol
        
        # 更新时间戳
        analyze_data['cache_timestamp'] = time.time()
        
        return jsonify(analyze_data)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/curve/analyze', methods=['POST'])
def analyze_curve():
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 提取x和y数据
        x = np.array(data.get('x', []))
        y = np.array(data.get('y', []))
        
        # 检查数据有效性
        if len(x) < 5 or len(y) < 5:
            return jsonify({
                'success': False,
                'error': '数据点数量至少为5'
            }), 400
        
        # 提取参数
        model = data.get('model', 'polynomial')
        degree = data.get('degree', 3)
        threshold = data.get('threshold', 0.1)
        compression_ratio = data.get('compression_ratio', 0.5)
        
        # 创建曲线分析器
        analyzer = CurveAnalyzer(threshold=threshold)
        
        # 分析曲线
        results = analyzer.analyze_curve(x, y, model=model, degree=degree, compression_ratio=compression_ratio)
        
        # 准备响应数据
        response = {
            'success': True,
            'original_data': {
                'x': x.tolist(),
                'y': y.tolist()
            },
            'fitted_data': {
                'y': results['fitted_y'].tolist()
            },
            'derivatives': results['derivatives'].tolist(),
            'anomalies': results['anomalies'],
            'compressed_data': {
                'x': results['compressed_x'].tolist(),
                'y': results['compressed_y'].tolist()
            },
            'params': results['params'].tolist() if hasattr(results['params'], 'tolist') else results['params'],
            'error': results['error'],
            'compression_info': results['compression_info'],
            'timestamp': time.time()
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stock/ai-analysis/<symbol>', methods=['GET'])
def get_stock_ai_analysis(symbol):
    try:
        # 获取股票K线数据
        kline_data = fetch_stock_kline(symbol)
        
        if not kline_data:
            return jsonify({
                'success': False,
                'error': '未获取到股票数据'
            }), 404
        
        # 数据压缩 - 保留每周的关键数据点
        compressed_data = []
        for i, item in enumerate(kline_data):
            # 每7天保留一个数据点
            if i % 7 == 0 or i == len(kline_data) - 1:
                compressed_data.append(item)
        
        # 计算技术指标
        technical_indicators = calculate_technical_indicators(kline_data)
        
        # 趋势分析
        trend_analysis = analyze_trend(kline_data, technical_indicators)
        
        # 获取股票基本信息
        stock_info = get_stock_basic_info(symbol)
        
        # 构建AI分析数据
        period = "" if not kline_data else f"{kline_data[0]['date']} to {kline_data[-1]['date']}"
        recent_events = [] if not kline_data else [
            f"{kline_data[-1]['date']}: 最新收盘价 {kline_data[-1]['close']}"
        ]
        
        ai_analysis_data = {
            'stock_info': {
                'code': symbol,
                'name': stock_info.get('name', ''),
                'industry': stock_info.get('industry', ''),
                'period': period
            },
            'compressed_data': compressed_data,
            'technical_indicators': technical_indicators,
            'trend_analysis': trend_analysis,
            'recent_events': recent_events
        }
        
        return jsonify({
            'success': True,
            'data': ai_analysis_data,
            'symbol': symbol
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze():
    try:
        data = request.get_json()
        stock_data = data.get('stock_data', '')
        
        if not stock_data:
            return jsonify({
                'success': False,
                'error': '缺少股票数据'
            }), 400
        
        openai_api_key = "sk-fe0d531eb96d4cdcbd4dedbccb7bb131"
        openai_api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {openai_api_key}'
        }
        
        payload = {
            'model': 'qwen-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': '你是一位专业的股票分析师，擅长技术分析和基本面分析。请根据提供的股票数据，进行全面的分析，并给出专业的投资建议。'
                },
                {
                    'role': 'user',
                    'content': f'请分析以下股票数据：\n{stock_data}\n\n分析要求：\n1. 技术面分析：基于提供的技术指标和趋势分析\n2. 基本面分析：基于股票基本信息\n3. 综合判断：给出明确的投资建议\n4. 风险提示：分析可能的风险因素\n\n请使用专业、客观的语言，提供详细的分析报告。'
                }
            ],
            'temperature': 0.7
        }
        
        response = requests.post(openai_api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('choices') and len(result['choices']) > 0:
                ai_result = result['choices'][0]['message']['content']
                return jsonify({
                    'success': True,
                    'result': ai_result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '无效的API响应格式'
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': f'API调用失败: {response.status_code} {response.text}'
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'API调用超时'
        }), 504
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ai/test', methods=['GET'])
def test_ai_analysis():
    try:
        mock_stock_data = {
            'stock_info': {
                'code': '600519',
                'name': '贵州茅台',
                'industry': '白酒',
                'period': '2024-01-01 to 2024-12-31'
            },
            'compressed_data': [
                {'date': '2024-01-01', 'open': 1800, 'high': 1850, 'low': 1780, 'close': 1830, 'volume': 1000000},
                {'date': '2024-02-01', 'open': 1830, 'high': 1880, 'low': 1810, 'close': 1860, 'volume': 1200000},
                {'date': '2024-03-01', 'open': 1860, 'high': 1900, 'low': 1840, 'close': 1880, 'volume': 1100000},
                {'date': '2024-04-01', 'open': 1880, 'high': 1920, 'low': 1860, 'close': 1900, 'volume': 1300000},
                {'date': '2024-05-01', 'open': 1900, 'high': 1950, 'low': 1880, 'close': 1930, 'volume': 1400000}
            ],
            'technical_indicators': {
                'ma': {
                    'ma5': 1900,
                    'ma10': 1880,
                    'ma20': 1860,
                    'ma60': 1840
                },
                'macd': {
                    'dif': 15.5,
                    'dea': 12.3,
                    'hist': 6.4
                },
                'rsi': {
                    'rsi14': 65.2
                },
                'kdj': {
                    'k': 72.5,
                    'd': 68.3,
                    'j': 80.9
                },
                'boll': {
                    'upper': 1950,
                    'middle': 1900,
                    'lower': 1850
                }
            },
            'trend_analysis': {
                'short_term': 'upward',
                'medium_term': 'upward',
                'long_term': 'stable',
                'trend_strength': 'strong'
            },
            'recent_events': [
                '2024-12-31: 最新收盘价 1930',
                '2024-12-30: 成交量放大至140万股'
            ]
        }
        
        formatted_data = json.dumps(mock_stock_data, ensure_ascii=False, indent=2)
        
        openai_api_key = "sk-fe0d531eb96d4cdcbd4dedbccb7bb131"
        openai_api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {openai_api_key}'
        }
        
        payload = {
            'model': 'qwen-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': '你是一位专业的股票分析师，擅长技术分析和基本面分析。请根据提供的股票数据，进行全面的分析，并给出专业的投资建议。'
                },
                {
                    'role': 'user',
                    'content': f'请分析以下股票数据：\n{formatted_data}\n\n分析要求：\n1. 技术面分析：基于提供的技术指标和趋势分析\n2. 基本面分析：基于股票基本信息\n3. 综合判断：给出明确的投资建议\n4. 风险提示：分析可能的风险因素\n\n请使用专业、客观的语言，提供详细的分析报告。'
                }
            ],
            'temperature': 0.7
        }
        
        print('开始调用阿里云DashScope API进行测试...')
        response = requests.post(openai_api_url, headers=headers, json=payload, timeout=30)
        print(f'API响应状态码: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print(f'API响应内容: {result}')
            if result.get('choices') and len(result['choices']) > 0:
                ai_result = result['choices'][0]['message']['content']
                return jsonify({
                    'success': True,
                    'result': ai_result,
                    'test_data': mock_stock_data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '无效的API响应格式',
                    'response': result
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': f'API调用失败: {response.status_code}',
                'response_text': response.text
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'API调用超时'
        }), 504
    except Exception as e:
        print(f'测试接口异常: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_technical_indicators(kline_data):
    """计算技术指标"""
    import pandas as pd
    
    # 转换为DataFrame
    df = pd.DataFrame(kline_data)
    
    # 初始化技术指标结果
    technical_indicators = {
        'ma': {
            'ma5': 0,
            'ma10': 0,
            'ma20': 0,
            'ma60': 0
        },
        'macd': {
            'dif': 0,
            'dea': 0,
            'hist': 0
        },
        'rsi': {
            'rsi14': 0
        },
        'kdj': {
            'k': 0,
            'd': 0,
            'j': 0
        },
        'boll': {
            'upper': 0,
            'middle': 0,
            'lower': 0
        }
    }
    
    # 检查数据是否为空
    if len(df) == 0:
        return technical_indicators
    
    try:
        # 计算移动平均线
        close_prices = df['close'].values
        if len(close_prices) > 0:
            ma5 = calculate_ma(close_prices, 5)
            ma10 = calculate_ma(close_prices, 10)
            ma20 = calculate_ma(close_prices, 20)
            ma60 = calculate_ma(close_prices, 60)
            
            technical_indicators['ma']['ma5'] = float(ma5[-1]) if len(ma5) > 0 else 0
            technical_indicators['ma']['ma10'] = float(ma10[-1]) if len(ma10) > 0 else 0
            technical_indicators['ma']['ma20'] = float(ma20[-1]) if len(ma20) > 0 else 0
            technical_indicators['ma']['ma60'] = float(ma60[-1]) if len(ma60) > 0 else 0
        
        # 计算MACD
        if len(close_prices) > 0:
            macd = calculate_macd(close_prices)
            technical_indicators['macd']['dif'] = float(macd['dif'][-1]) if len(macd['dif']) > 0 else 0
            technical_indicators['macd']['dea'] = float(macd['dea'][-1]) if len(macd['dea']) > 0 else 0
            technical_indicators['macd']['hist'] = float(macd['hist'][-1]) if len(macd['hist']) > 0 else 0
        
        # 计算RSI
        if len(close_prices) > 0:
            rsi14 = calculate_rsi(close_prices, 14)
            technical_indicators['rsi']['rsi14'] = float(rsi14[-1]) if len(rsi14) > 0 else 0
        
        # 计算KDJ
        if len(df) > 0:
            kdj = calculate_kdj(df[['high', 'low', 'close']].values)
            technical_indicators['kdj']['k'] = float(kdj['k'][-1]) if len(kdj['k']) > 0 else 0
            technical_indicators['kdj']['d'] = float(kdj['d'][-1]) if len(kdj['d']) > 0 else 0
            technical_indicators['kdj']['j'] = float(kdj['j'][-1]) if len(kdj['j']) > 0 else 0
        
        # 计算BOLL
        if len(close_prices) > 0:
            boll = calculate_boll(close_prices, 20, 2)
            technical_indicators['boll']['upper'] = float(boll['upper'][-1]) if len(boll['upper']) > 0 else 0
            technical_indicators['boll']['middle'] = float(boll['middle'][-1]) if len(boll['middle']) > 0 else 0
            technical_indicators['boll']['lower'] = float(boll['lower'][-1]) if len(boll['lower']) > 0 else 0
    except Exception as e:
        # 如果计算失败，返回初始值
        pass
    
    return technical_indicators

def calculate_ma(prices, period):
    """计算移动平均线"""
    import numpy as np
    ma = []
    for i in range(len(prices)):
        if i < period - 1:
            ma.append(0)
        else:
            ma.append(np.mean(prices[i-period+1:i+1]))
    return ma

def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
    """计算MACD"""
    import numpy as np
    
    # 计算EMA
    def ema(data, period):
        weights = np.exp(np.linspace(-1., 0., period))
        weights /= weights.sum()
        return np.convolve(data, weights, mode='full')[:len(data)]
    
    ema12 = ema(prices, fast_period)
    ema26 = ema(prices, slow_period)
    dif = ema12 - ema26
    dea = ema(dif, signal_period)
    hist = (dif - dea) * 2
    
    return {'dif': dif.tolist(), 'dea': dea.tolist(), 'hist': hist.tolist()}

def calculate_rsi(prices, period=14):
    """计算RSI"""
    import numpy as np
    
    deltas = np.diff(prices)
    gains = deltas[deltas > 0]
    losses = -deltas[deltas < 0]
    
    avg_gain = np.mean(gains[:period]) if len(gains) > 0 else 0
    avg_loss = np.mean(losses[:period]) if len(losses) > 0 else 0
    
    rsi = []
    for i in range(len(prices)):
        if i < period:
            rsi.append(50)
        else:
            if avg_loss == 0:
                rsi_value = 100
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))
            rsi.append(rsi_value)
            
            # 更新平均 gain 和 loss
            if i < len(deltas):
                delta = deltas[i]
                if delta > 0:
                    avg_gain = (avg_gain * (period - 1) + delta) / period
                    avg_loss = (avg_loss * (period - 1)) / period
                else:
                    avg_gain = (avg_gain * (period - 1)) / period
                    avg_loss = (avg_loss * (period - 1) + abs(delta)) / period
    
    return rsi

def calculate_kdj(ohlc_data, period=9):
    """计算KDJ"""
    import numpy as np
    
    high = ohlc_data[:, 0]
    low = ohlc_data[:, 1]
    close = ohlc_data[:, 2]
    
    rsv = []
    for i in range(len(close)):
        if i < period - 1:
            rsv.append(50)
        else:
            period_high = np.max(high[i-period+1:i+1])
            period_low = np.min(low[i-period+1:i+1])
            if period_high == period_low:
                rsv.append(50)
            else:
                rsv.append((close[i] - period_low) / (period_high - period_low) * 100)
    
    k = []
    d = []
    j = []
    
    for i in range(len(rsv)):
        if i == 0:
            k_val = 50
            d_val = 50
        else:
            k_val = (2/3) * k[i-1] + (1/3) * rsv[i]
            d_val = (2/3) * d[i-1] + (1/3) * k_val
        j_val = 3 * k_val - 2 * d_val
        
        k.append(k_val)
        d.append(d_val)
        j.append(j_val)
    
    return {'k': k, 'd': d, 'j': j}

def calculate_boll(prices, period=20, multiplier=2):
    """计算BOLL"""
    import numpy as np
    
    middle = []
    upper = []
    lower = []
    
    for i in range(len(prices)):
        if i < period - 1:
            middle.append(0)
            upper.append(0)
            lower.append(0)
        else:
            period_prices = prices[i-period+1:i+1]
            ma = np.mean(period_prices)
            std = np.std(period_prices)
            middle.append(ma)
            upper.append(ma + multiplier * std)
            lower.append(ma - multiplier * std)
    
    return {'upper': upper, 'middle': middle, 'lower': lower}

def analyze_trend(kline_data, technical_indicators):
    """趋势分析"""
    # 初始化趋势分析结果
    trend_analysis = {
        'short_term': '震荡',
        'medium_term': '震荡',
        'long_term': '震荡',
        'support_levels': [],
        'resistance_levels': [],
        'signals': []
    }
    
    # 检查数据是否为空
    if not kline_data:
        return trend_analysis
    
    try:
        close_prices = [item['close'] for item in kline_data]
        volumes = [item['volume'] for item in kline_data]
        
        # 短期趋势（最近20天）
        if len(close_prices) >= 20:
            short_term_trend = '上涨' if close_prices[-1] > close_prices[-20] else '下跌' if close_prices[-1] < close_prices[-20] else '震荡'
        else:
            short_term_trend = '震荡'
        
        # 中期趋势（最近60天）
        if len(close_prices) >= 60:
            medium_term_trend = '上涨' if close_prices[-1] > close_prices[-60] else '下跌' if close_prices[-1] < close_prices[-60] else '震荡'
        else:
            medium_term_trend = '震荡'
        
        # 长期趋势（最近120天）
        if len(close_prices) > 120:
            long_term_trend = '上涨' if close_prices[-1] > close_prices[-120] else '下跌' if close_prices[-1] < close_prices[-120] else '震荡'
        else:
            long_term_trend = '震荡'
        
        # 支撑位和阻力位
        support_levels = []
        resistance_levels = []
        if len(close_prices) >= 30:
            support_levels.append(min(close_prices[-30:]))
            resistance_levels.append(max(close_prices[-30:]))
        if len(close_prices) >= 60:
            support_levels.append(min(close_prices[-60:]))
            resistance_levels.append(max(close_prices[-60:]))
        
        # 信号识别
        signals = []
        
        # MACD金叉死叉
        macd = technical_indicators['macd']
        if macd['dif'] > macd['dea']:
            signals.append('MACD金叉')
        else:
            signals.append('MACD死叉')
        
        # RSI超买超卖
        rsi = technical_indicators['rsi']['rsi14']
        if rsi > 70:
            signals.append('RSI超买')
        elif rsi < 30:
            signals.append('RSI超卖')
        
        # KDJ金叉死叉
        kdj = technical_indicators['kdj']
        if kdj['k'] > kdj['d']:
            signals.append('KDJ金叉')
        else:
            signals.append('KDJ死叉')
        
        trend_analysis = {
            'short_term': short_term_trend,
            'medium_term': medium_term_trend,
            'long_term': long_term_trend,
            'support_levels': support_levels,
            'resistance_levels': resistance_levels,
            'signals': signals
        }
    except Exception as e:
        # 如果分析失败，返回初始值
        pass
    
    return trend_analysis

def get_stock_basic_info(symbol):
    """获取股票基本信息"""
    # 从本地文件获取股票信息
    import json
    
    # 搜索股票文件
    stock_files = glob.glob(os.path.join(os.path.dirname(__file__), 'stock_data', 'stocks', '*.json'))
    
    for file_path in stock_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            # 检查股票代码是否匹配
            code = stock_data.get('code', '')
            if symbol in code or code.endswith(symbol):
                return {
                    'name': stock_data.get('name', ''),
                    'industry': stock_data.get('industry', '')
                }
        except Exception:
            pass
    
    return {'name': '', 'industry': ''}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)