#!/bin/bash
set -e

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 1. 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3。请先安装 Python 3。"
    exit 1
fi

# 2. 安装依赖
echo "[INFO] 正在检查并安装依赖..."
pip install -r requirements.txt

# 3. 启动服务
echo "[INFO] 正在启动服务..."

# 3.1 启动数据 API (端口 5001)
echo "[INFO] 启动数据 API (Port 5001)..."
# 使用子 shell 进入 data 目录启动，以免影响当前目录
(cd data && python3 app.py) > data_api.log 2>&1 &
DATA_PID=$!
echo "数据 API PID: $DATA_PID"

# 3.2 启动相似度匹配 API (端口 5002)
echo "[INFO] 启动相似度匹配 API (Port 5002)..."
python3 similarity_web.py > similarity_api.log 2>&1 &
SIM_PID=$!
echo "相似度匹配 API PID: $SIM_PID"

# 3.3 启动前端服务 (端口 8000)
echo "[INFO] 启动前端服务 (Port 8000)..."
# 使用 python http.server 启动前端
(cd frontend && python3 -m http.server 8000) > frontend.log 2>&1 &
FRONT_PID=$!
echo "前端服务 PID: $FRONT_PID"

# 3.4 启动股票跟踪服务
echo "[INFO] 启动股票跟踪服务..."
(cd data && python3 stock_tracker.py) > tracker.log 2>&1 &
TRACKER_PID=$!
echo "股票跟踪服务 PID: $TRACKER_PID"

echo "========================================="
echo "所有服务已启动！"
echo "前端访问地址: http://localhost:8000"
echo "数据 API 日志: data_api.log"
echo "相似度 API 日志: similarity_api.log"
echo "前端日志: frontend.log"
echo "跟踪服务日志: tracker.log"
echo "按 Ctrl+C 停止所有服务"
echo "========================================="

# 捕获 Ctrl+C 信号并关闭所有子进程
trap "kill $DATA_PID $SIM_PID $FRONT_PID $TRACKER_PID; exit" INT

# 等待任意子进程结束（保持脚本运行）
wait
