import numpy as np
import time
import logging
import random
import heapq
import sys

# Configure logging
logging.basicConfig(
    filename='similarity_search.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

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

        # Check if we need to search the far branch
        # If the distance to the plane is less than the worst distance in our heap, we must check
        if len(self.best_heap) < k or abs(diff) < -self.best_heap[0][0]:
            self._search(far_branch, target, k)

def dtw_distance(s1, s2):
    """
    Compute Dynamic Time Warping distance between two sequences.
    """
    n, m = len(s1), len(s2)
    dtw = np.full((n+1, m+1), float('inf'))
    dtw[0, 0] = 0
    
    # Optimization: If lengths are equal and we want to be fast, we can use a window
    # But for length ~60, full matrix is fine (~3600 ops)
    
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = abs(s1[i-1] - s2[j-1])
            dtw[i, j] = cost + min(dtw[i-1, j], dtw[i, j-1], dtw[i-1, j-1])
            
    return dtw[n, m]

class StockSimilaritySearch:
    def __init__(self, num_stocks=3000, seq_length=60):
        self.num_stocks = num_stocks
        self.seq_length = seq_length
        self.stock_data = []
        self.normalized_data = []
        self.features = []
        self.kd_tree = None

    def generate_random_walk(self, length, start_price=100, volatility=0.02):
        prices = [start_price]
        for _ in range(length - 1):
            change = np.random.normal(0, volatility)
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        return np.array(prices)

    def generate_data(self):
        logging.info(f"Generating {self.num_stocks} simulated stock records...")
        for i in range(self.num_stocks):
            # Randomize start price and volatility for variety
            start = np.random.uniform(10, 200)
            vol = np.random.uniform(0.01, 0.05)
            prices = self.generate_random_walk(self.seq_length, start, vol)
            self.stock_data.append(prices)
        logging.info("Data generation complete.")

    def normalize(self, sequence):
        """Z-score normalization to focus on shape rather than absolute magnitude."""
        return (sequence - np.mean(sequence)) / (np.std(sequence) + 1e-8)

    def extract_features(self, sequence):
        """
        Extract features for KD-Tree indexing.
        Features:
        1. Trend (Slope of linear regression)
        2. Volatility (Std dev of returns)
        3. Downsampled shape (8 points)
        """
        norm_seq = self.normalize(sequence)
        
        # 1. Trend
        x = np.arange(len(norm_seq))
        slope, _ = np.polyfit(x, norm_seq, 1)
        
        # 2. Volatility (std of normalized data is 1 by definition, so we use raw returns std)
        returns = np.diff(sequence) / sequence[:-1]
        volatility = np.std(returns)
        
        # 3. Shape (Resample to 8 points)
        indices = np.linspace(0, len(norm_seq)-1, 8).astype(int)
        shape_features = norm_seq[indices]
        
        # Combine
        features = np.concatenate(([slope * 100], [volatility * 100], shape_features))
        return features

    def build_index(self):
        logging.info("Building feature index and KD-Tree...")
        feature_list = []
        for seq in self.stock_data:
            feature_list.append(self.extract_features(seq))
        
        self.features = np.array(feature_list)
        # Store original indices
        self.indices = np.arange(self.num_stocks)
        
        # Build KD-Tree
        self.kd_tree = SimpleKDTree(self.features, self.indices)
        logging.info("KD-Tree built.")

    def search(self, query_kline, top_k=3, candidate_pool_size=50):
        start_time = time.time()
        
        # 1. Preprocessing
        query_features = self.extract_features(query_kline)
        norm_query = self.normalize(query_kline)
        
        # 2. KD-Tree Search (Coarse Filter)
        candidate_indices = self.kd_tree.query(query_features, k=candidate_pool_size)
        
        # 3. DTW Reranking (Fine Filter)
        dtw_results = []
        for idx in candidate_indices:
            candidate_seq = self.stock_data[idx]
            norm_candidate = self.normalize(candidate_seq)
            
            dist = dtw_distance(norm_query, norm_candidate)
            dtw_results.append((idx, dist))
            
        # Sort by DTW distance
        dtw_results.sort(key=lambda x: x[1])
        
        final_results = dtw_results[:top_k]
        
        elapsed_ms = (time.time() - start_time) * 1000
        logging.info(f"Search completed in {elapsed_ms:.2f} ms")
        
        return final_results, elapsed_ms

def main():
    # Initialize
    searcher = StockSimilaritySearch(num_stocks=3000)
    searcher.generate_data()
    searcher.build_index()
    
    # Simulate a "Hand-Drawn" K-line
    # We simulate this by taking a random existing stock and adding some noise/distortion
    # to ensure there's a ground truth similar one, but not identical.
    logging.info("\nGenerating simulated hand-drawn K-line...")
    target_idx = np.random.randint(0, 3000)
    base_seq = searcher.stock_data[target_idx]
    
    # Add noise and warp slightly
    noise = np.random.normal(0, np.std(base_seq)*0.5, len(base_seq))
    hand_drawn_query = base_seq + noise
    
    # Log the query data
    logging.info(f"Query Sequence (Simulated Hand-Drawn, based on Stock #{target_idx}):")
    logging.info(np.array2string(hand_drawn_query, precision=2, separator=', '))
    
    # Perform Search
    logging.info("\nStarting Search...")
    results, latency = searcher.search(hand_drawn_query, top_k=3)
    
    # Log Results
    logging.info("\nSearch Results (Top 3):")
    for rank, (idx, dist) in enumerate(results, 1):
        logging.info(f"Rank {rank}: Stock Index {idx}, DTW Distance: {dist:.4f}")
        logging.info(f"Stock Data: {np.array2string(searcher.stock_data[idx], precision=2, separator=', ')}")
        
    logging.info(f"\nTotal Search Latency: {latency:.2f} ms")
    if latency < 100:
        logging.info("SUCCESS: Latency is under 100ms.")
    else:
        logging.warning("WARNING: Latency exceeded 100ms.")

if __name__ == "__main__":
    main()
