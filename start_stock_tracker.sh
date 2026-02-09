#!/bin/bash

# 启动股票数据跟踪服务

echo "正在启动股票数据跟踪服务..."

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "错误: 虚拟环境不存在，请先创建虚拟环境"
    echo "运行命令: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 安装必要的依赖
echo "检查并安装必要的依赖..."
pip install -r requirements.txt

# 启动股票数据跟踪服务
echo "启动股票数据跟踪服务..."
echo "功能："
echo "1. 持续抓取所有股票数据到本地数据库"
echo "2. 当用户搜索新股票时，自动抓取并保存数据"
echo "3. 每天早中晚各刷新一次所有股票数据"
echo "4. 所有数据请求优先从本地数据库获取"
cd data
python stock_tracker.py
