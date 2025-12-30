# 使用官方 Python 3.11 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖（添加 dos2unix 处理 Windows 行尾符问题）
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    dos2unix \
    --fix-missing \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制项目文件
COPY . .

# 转换启动脚本的行尾符并设置权限（处理 Windows CRLF 问题）
RUN dos2unix /app/scripts/docker-entrypoint.sh && \
    chmod +x /app/scripts/docker-entrypoint.sh

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 设置启动脚本为入口点
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

