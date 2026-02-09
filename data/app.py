from flask import Flask, jsonify
from flask_cors import CORS
from data_fetcher import fetch_stock_kline

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)