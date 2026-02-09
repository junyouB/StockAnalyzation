import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.cluster import DBSCAN

class CurveAnalyzer:
    """
    曲线分析器，用于图像反向拟合、导数计算、异常检测和数据压缩
    """
    
    def __init__(self, threshold=0.1):
        """
        初始化曲线分析器
        
        Args:
            threshold: 导数差异阈值，超过此值的点会被标记为异常
        """
        self.threshold = threshold
    
    def fit_curve(self, x, y, model='polynomial', degree=3):
        """
        拟合曲线
        
        Args:
            x: x坐标数据
            y: y坐标数据
            model: 拟合模型类型，可选'polynomial'(多项式)或'exp'(指数)
            degree: 多项式拟合的阶数
            
        Returns:
            拟合函数和拟合参数
        """
        if model == 'polynomial':
            # 多项式拟合
            params = np.polyfit(x, y, degree)
            def fitted_func(x_val):
                return np.polyval(params, x_val)
            return fitted_func, params
        
        elif model == 'exp':
            # 指数拟合
            def exp_func(x_val, a, b, c):
                return a * np.exp(b * x_val) + c
            
            try:
                params, _ = curve_fit(exp_func, x, y)
                return exp_func, params
            except:
                # 如果指数拟合失败，使用多项式拟合
                return self.fit_curve(x, y, model='polynomial', degree=3)
        
        else:
            raise ValueError("Unsupported model type. Choose 'polynomial' or 'exp'")
    
    def calculate_derivative(self, func, x, h=1e-5):
        """
        数值计算导数
        
        Args:
            func: 函数
            x: x坐标
            h: 步长
            
        Returns:
            导数数组
        """
        return (func(x + h) - func(x - h)) / (2 * h)
    
    def detect_anomalies(self, derivatives):
        """
        检测导数异常
        
        Args:
            derivatives: 导数数组
            
        Returns:
            异常点索引列表
        """
        anomalies = []
        for i in range(1, len(derivatives)):
            if abs(derivatives[i] - derivatives[i-1]) > self.threshold:
                anomalies.append(i)
        return anomalies
    
    def compress_data(self, x, y, anomalies, compression_ratio=0.5):
        """
        压缩数据
        
        Args:
            x: x坐标数据
            y: y坐标数据
            anomalies: 异常点索引
            compression_ratio: 压缩比例
            
        Returns:
            压缩后的数据点
        """
        # 保留异常点
        anomaly_points = [(x[i], y[i]) for i in anomalies]
        
        # 计算需要保留的正常点数量
        total_points = len(x)
        normal_points_to_keep = int((total_points - len(anomalies)) * compression_ratio)
        
        # 均匀采样正常点
        normal_indices = [i for i in range(total_points) if i not in anomalies]
        if len(normal_indices) > normal_points_to_keep:
            step = len(normal_indices) // normal_points_to_keep
            sampled_normal_indices = normal_indices[::step]
        else:
            sampled_normal_indices = normal_indices
        
        # 保留正常点
        normal_points = [(x[i], y[i]) for i in sampled_normal_indices]
        
        # 合并并按x排序
        all_points = anomaly_points + normal_points
        all_points.sort(key=lambda p: p[0])
        
        # 分离x和y
        compressed_x = [p[0] for p in all_points]
        compressed_y = [p[1] for p in all_points]
        
        return np.array(compressed_x), np.array(compressed_y)
    
    def analyze_curve(self, x, y, model='polynomial', degree=3, compression_ratio=0.5):
        """
        完整的曲线分析流程
        
        Args:
            x: x坐标数据
            y: y坐标数据
            model: 拟合模型类型
            degree: 多项式拟合阶数
            compression_ratio: 压缩比例
            
        Returns:
            分析结果字典
        """
        # 拟合曲线
        fitted_func, params = self.fit_curve(x, y, model, degree)
        
        # 计算拟合值
        fitted_y = fitted_func(x)
        
        # 计算导数
        derivatives = self.calculate_derivative(fitted_func, x)
        
        # 检测异常点
        anomalies = self.detect_anomalies(derivatives)
        
        # 压缩数据
        compressed_x, compressed_y = self.compress_data(x, y, anomalies, compression_ratio)
        
        # 计算拟合误差
        mse = np.mean((y - fitted_y) ** 2)
        rmse = np.sqrt(mse)
        
        return {
            'original_x': x,
            'original_y': y,
            'fitted_y': fitted_y,
            'derivatives': derivatives,
            'anomalies': anomalies,
            'compressed_x': compressed_x,
            'compressed_y': compressed_y,
            'fitted_func': fitted_func,
            'params': params,
            'error': {
                'mse': mse,
                'rmse': rmse
            },
            'compression_info': {
                'original_points': len(x),
                'compressed_points': len(compressed_x),
                'compression_ratio': len(compressed_x) / len(x)
            }
        }
    
    def plot_results(self, analysis_results):
        """
        绘制分析结果
        
        Args:
            analysis_results: 分析结果字典
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 绘制原始数据、拟合曲线和异常点
        ax1.scatter(analysis_results['original_x'], analysis_results['original_y'], 
                   label='Original Data', s=10, alpha=0.5)
        ax1.plot(analysis_results['original_x'], analysis_results['fitted_y'], 
                 label='Fitted Curve', color='red', linewidth=2)
        
        # 标记异常点
        if analysis_results['anomalies']:
            anomaly_x = [analysis_results['original_x'][i] for i in analysis_results['anomalies']]
            anomaly_y = [analysis_results['original_y'][i] for i in analysis_results['anomalies']]
            ax1.scatter(anomaly_x, anomaly_y, label='Anomalies', color='green', s=50, marker='x')
        
        # 绘制压缩后的数据
        ax1.scatter(analysis_results['compressed_x'], analysis_results['compressed_y'], 
                   label='Compressed Data', color='purple', s=30, marker='o', facecolors='none')
        
        ax1.set_title('Curve Fitting and Data Compression')
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.legend()
        ax1.grid(True)
        
        # 绘制导数
        ax2.plot(analysis_results['original_x'], analysis_results['derivatives'], 
                 label='Derivative', color='blue', linewidth=2)
        
        # 标记异常点对应的导数位置
        if analysis_results['anomalies']:
            anomaly_derivative_x = [analysis_results['original_x'][i] for i in analysis_results['anomalies']]
            anomaly_derivative_y = [analysis_results['derivatives'][i] for i in analysis_results['anomalies']]
            ax2.scatter(anomaly_derivative_x, anomaly_derivative_y, 
                       label='Derivative Anomalies', color='red', s=50, marker='x')
        
        ax2.set_title('Derivative Analysis')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Derivative')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()

# 示例用法
if __name__ == '__main__':
    # 生成示例数据
    x = np.linspace(0, 10, 100)
    y = np.sin(x) + 0.1 * np.random.randn(100)
    
    # 添加一些异常点
    y[20] += 0.5
    y[50] -= 0.5
    y[80] += 0.4
    
    # 创建分析器
    analyzer = CurveAnalyzer(threshold=0.2)
    
    # 分析曲线
    results = analyzer.analyze_curve(x, y, model='polynomial', degree=5, compression_ratio=0.3)
    
    # 打印结果
    print(f"原始数据点数量: {results['compression_info']['original_points']}")
    print(f"压缩后数据点数量: {results['compression_info']['compressed_points']}")
    print(f"实际压缩比例: {results['compression_info']['compression_ratio']:.2f}")
    print(f"异常点数量: {len(results['anomalies'])}")
    print(f"异常点索引: {results['anomalies']}")
    print(f"拟合误差 (RMSE): {results['error']['rmse']:.4f}")
    
    # 绘制结果
    analyzer.plot_results(results)