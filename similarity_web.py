import numpy as np
import json
import glob
import os
import heapq
import time
import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# --- Algorithms (Reused) ---

class SimpleKDTree:
    """
    A simple implementation of KD-Tree for nearest neighbor search.
    """
    def __init__(self, data, indices):
        self.data = data
        self.indices = indices
        self.n, self.m = data.shape
        self.tree = self._build_tree(list(range(self.n)), 0)

    class Node:
        def __init__(self, index, axis, left=None, right=None):
            self.index = index
            self.axis = axis
            self.left = left
            self.right = right

    def _build_tree(self, point_indices, depth):
        if not point_indices:
            return None

        axis = depth % self.m
        
        # Sort point indices by the value at the current axis
        point_indices.sort(key=lambda i: self.data[i][axis])
        median = len(point_indices) // 2
        
        node_index = point_indices[median]
        
        return self.Node(
            index=node_index,
            axis=axis,
            left=self._build_tree(point_indices[:median], depth + 1),
            right=self._build_tree(point_indices[median + 1:], depth + 1)
        )

    def query(self, target, k=1):
        self.best_heap = [] # Max heap storing (-distance, index)
        self._search(self.tree, target, k)
        
        # Return indices sorted by distance (closest first)
        results = sorted([(-d, idx) for d, idx in self.best_heap], key=lambda x: x[0])
        return [idx for _, idx in results]

    def _search(self, node, target, k):
        if node is None:
            return

        dist = np.linalg.norm(self.data[node.index] - target)
        
        # Maintain a heap of size k
        if len(self.best_heap) < k:
            heapq.heappush(self.best_heap, (-dist, node.index))
        elif dist < -self.best_heap[0][0]:
            heapq.heappushpop(self.best_heap, (-dist, node.index))

        axis = node.axis
        diff = target[axis] - self.data[node.index][axis]

        close_branch = node.left if diff < 0 else node.right
        far_branch = node.right if diff < 0 else node.left

        self._search(close_branch, target, k)

        if len(self.best_heap) < k or abs(diff) < -self.best_heap[0][0]:
            self._search(far_branch, target, k)

def dtw_distance(s1, s2):
    n, m = len(s1), len(s2)
    dtw = np.full((n+1, m+1), float('inf'))
    dtw[0, 0] = 0
    
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = abs(s1[i-1] - s2[j-1])
            dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])
            
    return dtw[n, m]

# --- Search Engine ---

class StockSimilaritySearch:
    def __init__(self, data_dir, seq_length=20):
        self.data_dir = data_dir
        self.seq_length = seq_length
        self.stocks = [] # List of dicts: {'code': ..., 'name': ..., 'kline': [prices...]}
        self.features = []
        self.kd_tree = None
        self.feature_map = [] # Map index in features to index in stocks list

    def load_data(self, limit=3000):
        logger.info(f"Loading stock data from {self.data_dir}...")
        files = glob.glob(os.path.join(self.data_dir, "*.json"))
        logger.info(f"Found {len(files)} files in directory.")
        # limit = min(len(files), limit)
        files = files[:limit]
        
        count = 0
        for i, fpath in enumerate(files):
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    kline = data.get('kline', [])
                    if len(kline) >= self.seq_length:
                        # Take the latest 'seq_length' points
                        recent_kline = kline[-self.seq_length:]
                        closes = [float(k['close']) for k in recent_kline]
                        
                        self.stocks.append({
                            'code': data.get('code'),
                            'name': data.get('name'),
                            'closes': np.array(closes),
                            'full_kline': recent_kline
                        })
                        count += 1
                    else:
                        if i < 5: logger.warning(f"Skipping {fpath}: kline length {len(kline)} < {self.seq_length}")
            except Exception as e:
                logger.error(f"Error loading {fpath}: {e}")
        
        logger.info(f"Loaded {count} stocks.")

    def normalize(self, sequence):
        return (sequence - np.mean(sequence)) / (np.std(sequence) + 1e-8)

    def extract_features(self, sequence):
        norm_seq = self.normalize(sequence)
        
        # 1. Trend
        x = np.arange(len(norm_seq))
        slope, _ = np.polyfit(x, norm_seq, 1)
        
        # 2. Volatility
        returns = np.diff(sequence) / (sequence[:-1] + 1e-8)
        volatility = np.std(returns)
        
        # 3. Shape (Resample to 8 points)
        indices = np.linspace(0, len(norm_seq)-1, 8).astype(int)
        shape_features = norm_seq[indices]
        
        features = np.concatenate(([slope * 100], [volatility * 100], shape_features))
        return features

    def build_index(self):
        logger.info("Building index...")
        feature_list = []
        valid_indices = []
        
        for i, stock in enumerate(self.stocks):
            try:
                feat = self.extract_features(stock['closes'])
                feature_list.append(feat)
                valid_indices.append(i)
            except Exception as e:
                logger.error(f"Error extracting features for {stock['code']}: {e}")

        self.features = np.array(feature_list)
        self.feature_map = valid_indices # map 0..N in features to index in self.stocks
        
        # Build KD-Tree
        self.kd_tree = SimpleKDTree(self.features, np.arange(len(self.features)))
        logger.info("Index built.")

    def search(self, query_seq, top_k=3, candidate_pool_size=50):
        start_time = time.time()
        
        query_seq = np.array(query_seq)
        if len(query_seq) != self.seq_length:
             # Resample if length mismatch (simple linear interpolation)
             x_old = np.linspace(0, 1, len(query_seq))
             x_new = np.linspace(0, 1, self.seq_length)
             query_seq = np.interp(x_new, x_old, query_seq)

        query_features = self.extract_features(query_seq)
        norm_query = self.normalize(query_seq)
        
        # KD-Tree Search
        feature_indices = self.kd_tree.query(query_features, k=candidate_pool_size)
        
        # DTW Reranking
        dtw_results = []
        for feat_idx in feature_indices:
            stock_idx = self.feature_map[feat_idx]
            candidate_seq = self.stocks[stock_idx]['closes']
            norm_candidate = self.normalize(candidate_seq)
            
            dist = dtw_distance(norm_query, norm_candidate)
            dtw_results.append((stock_idx, dist))
            
        dtw_results.sort(key=lambda x: x[1])
        final_results = dtw_results[:top_k]
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        results_data = []
        for stock_idx, dist in final_results:
            stock = self.stocks[stock_idx]
            results_data.append({
                'code': stock['code'],
                'name': stock['name'],
                'closes': stock['closes'].tolist(),
                'distance': dist
            })
            
        return results_data, elapsed_ms

# --- Global Instance ---
search_engine = None

def init_engine():
    global search_engine
    data_path = os.path.abspath("data/stock_data/stocks")
    search_engine = StockSimilaritySearch(data_path)
    search_engine.load_data(limit=3000)
    search_engine.build_index()

# --- Routes ---

@app.route('/')
def index():
    return "Stock Similarity API is running on port 5002"

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/api/generate')
def generate_curve():
    # Generate a smooth abstract curve (simulating hand-drawn)
    length = 20
    
    # 1. Generate 3-5 key points
    num_key_points = np.random.randint(3, 6)
    key_x = np.linspace(0, length-1, num_key_points)
    
    # Random walk for key points but with larger steps to create shape
    key_y = [100]
    for _ in range(num_key_points - 1):
        change = np.random.uniform(-10, 10) # Larger changes for distinct shape
        key_y.append(key_y[-1] + change)
    
    # 2. Interpolate to fill 'length' points (Linear interpolation for simplicity, or polynomial)
    # Using numpy interp for linear connection
    full_x = np.arange(length)
    full_y = np.interp(full_x, key_x, key_y)
    
    # 3. Add slight smoothing/noise to make it look less robotic but still simple
    # Moving average smoothing
    window_size = 3
    smooth_y = np.convolve(full_y, np.ones(window_size)/window_size, mode='valid')
    
    # Pad back to original length (replicate edges)
    pad_start = [smooth_y[0]] * (window_size // 2)
    pad_end = [smooth_y[-1]] * (window_size // 2 + (window_size % 2 == 0)) # Adjustment for even window
    # Actually simpler: just resize or use original ends. 
    # Let's just use the interpolated points directly as they are "abstract" enough (straight lines connected)
    # which mimics a simple mouse draw better than noisy random walk.
    
    return jsonify({'curve': full_y.tolist()})

@app.route('/api/search', methods=['POST'])
def search_curve():
    data = request.json
    curve = data.get('curve')
    if not curve:
        return jsonify({'error': 'No curve provided'}), 400
    
    results, latency = search_engine.search(curve)
    
    return jsonify({
        'results': results,
        'latency': latency
    })

if __name__ == '__main__':
    init_engine()
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)
