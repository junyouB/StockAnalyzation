from flask import Flask, jsonify
from flask_cors import CORS
from data_fetcher import fetch_stock_kline
import json
import os

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)