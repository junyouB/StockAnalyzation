#!/bin/bash

# 股票分析系统启动脚本
# 功能：启动后端API服务和前端HTTP服务器

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检查虚拟环境
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}虚拟环境不存在，正在创建...${NC}"
    python3 -m venv "$PROJECT_DIR/venv"
    echo -e "${GREEN}虚拟环境创建成功${NC}"
fi

# 激活虚拟环境
source "$PROJECT_DIR/venv/bin/activate"

# 安装依赖
echo -e "${YELLOW}检查并安装依赖...${NC}"
pip install -q -r "$PROJECT_DIR/requirements.txt"
echo -e "${GREEN}依赖安装完成${NC}"

# 检查端口占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 杀死占用端口的进程
kill_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}端口 $1 被占用，正在释放...${NC}"
        lsof -Pi :$1 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# 释放端口
kill_port 5001
kill_port 8000

# 启动后端API服务
echo -e "${GREEN}启动后端API服务 (端口: 5001)...${NC}"
cd "$PROJECT_DIR/data"
python app.py &
BACKEND_PID=$!
echo -e "${GREEN}后端服务PID: $BACKEND_PID${NC}"

# 等待后端服务启动
sleep 3

# 检查后端是否启动成功
if ! check_port 5001; then
    echo -e "${RED}后端服务启动失败，请检查日志${NC}"
    exit 1
fi
echo -e "${GREEN}后端API服务启动成功！${NC}"

# 启动前端HTTP服务器
echo -e "${GREEN}启动前端HTTP服务器 (端口: 8000)...${NC}"
cd "$PROJECT_DIR"
python3 -m http.server 8000 &
FRONTEND_PID=$!
echo -e "${GREEN}前端服务PID: $FRONTEND_PID${NC}"

# 等待前端服务启动
sleep 2

# 检查前端是否启动成功
if ! check_port 8000; then
    echo -e "${RED}前端服务启动失败，请检查日志${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo -e "${GREEN}前端HTTP服务器启动成功！${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  股票分析系统启动成功！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  前端页面: ${YELLOW}http://localhost:8000/frontend/${NC}"
echo -e "  后端API:  ${YELLOW}http://localhost:5001${NC}"
echo ""
echo -e "  ${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo ""

# 捕获Ctrl+C信号
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

trap cleanup INT TERM

# 保持脚本运行
wait
