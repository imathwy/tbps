# 使用官方 Python 3.10 镜像（可根据 main_new.py 需求调整版本）
FROM python:3.17

# 设置工作目录
WORKDIR /app

# 复制并安装 requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制 search-app 目录
COPY search-app/ .

# 默认启动命令
CMD ["python", "main_new.py"]