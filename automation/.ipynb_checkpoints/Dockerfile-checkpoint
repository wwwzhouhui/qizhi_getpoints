# Login Automation Docker镜像（基于 Playwright）
FROM python:3.11-slim

# 设置维护者信息
LABEL maintainer="75271002@qq.com"
LABEL version="0.1.0"
LABEL description="OpenI 登录与 CloudBrains 自动化（Playwright）"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 安装系统基础依赖
RUN apt-get update && apt-get install -y \
    curl wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

# 创建共享浏览器目录（供非root用户使用）
RUN mkdir -p /ms-playwright

# 安装 Python 依赖（Playwright）并安装 Chromium 浏览器及其依赖
RUN pip install --no-cache-dir playwright && \
    python -m playwright install --with-deps chromium

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser && \
    chown -R appuser:appuser /app /ms-playwright

# 复制自动化脚本及配置
COPY login_automation.py ./
COPY config.ini ./
COPY run_login.sh ./
RUN chmod +x /app/run_login.sh

# 切换非root用户
USER appuser

# 启动命令：运行登录自动化
ENTRYPOINT ["/app/run_login.sh"]
