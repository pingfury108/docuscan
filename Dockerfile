# 使用官方Python运行时作为父镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

RUN pip install --no-cache-dir -r requirements.lock

# 暴露端口
EXPOSE 8000

WORKDIR /app

# 启动命令
CMD ["python", "-m", "uvicorn", "docuscan.main:app", "--host", "0.0.0.0", "--port", "8000"]
