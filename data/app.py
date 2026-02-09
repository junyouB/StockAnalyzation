from flask import Flask, jsonify, request
from flask_cors import CORS
from data_fetcher import fetch_stock_kline, search_stocks
from curve_analyzer import CurveAnalyzer
import json
import os
import time
import numpy as np

app = Flask(__name__)
CORS(app)

@app.route('/api/stock/kline/<symbol>', methods=['GET'])
def get_stock_kline(symbol):
    try:
        # 使用分离的模块获取股票K线数据
        data = fetch_stock_kline(symbol)
        
        return jsonify({
            'success': True,
            'data': data,
            'symbol': symbol
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)