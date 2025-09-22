#!/bin/bash
# tbps 项目启动脚本：初始化虚拟环境、安装依赖、启动 PostgreSQL 和 Python 应用
# 作者：王梓琛
# 前提：已安装 Docker 和 docker-compose

echo "步骤 1：检查 Docker 是否安装..."
if ! command -v docker &> /dev/null; then
    echo "错误：未找到 Docker。请先安装 Docker。"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误：未找到 docker-compose。请先安装 docker-compose。"
    exit 1
fi

echo "步骤 2：启动 PostgreSQL 和 Python 应用..."
docker-compose up -d --build

echo "步骤 3：等待数据库就绪..."
until docker-compose exec postgres pg_isready -U princhern -p 5432; do
    echo "等待 PostgreSQL 启动..."
    sleep 2
done

echo "数据库和应用已启动！连接信息："
echo "数据库主机：localhost"
echo "数据库端口：8923"
echo "数据库名：mathlib_db, wl_encodings_db"
echo "用户名：princhern"
echo "停止服务：docker-compose down"

# 可选：本地虚拟环境设置（如果不使用 Docker 运行 Python）
echo "可选：设置本地 Python 虚拟环境（仅限本地开发，未上传 .venv）..."
if ! [ -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "安装 Python 依赖..."
pip install -r requirements.txt
echo "虚拟环境已准备好，可运行 'python search-app/main_new.py'（如果不使用 Docker 运行应用）"
deactivate