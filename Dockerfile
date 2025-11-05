# OpenI 平台自动化积分获取工具 Docker 镜像（基于 Playwright）
FROM python:3.11-slim

# 设置维护者信息
LABEL maintainer="75271002@qq.com"
LABEL version="0.0.1"
LABEL description="OpenI 平台自动化积分获取工具 - 支持定时执行、日志记录、视频录制"

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    TZ=Asia/Shanghai

# 安装系统基础依赖和时区支持
RUN apt-get update && apt-get install -y \
    curl wget \
    ca-certificates \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建共享浏览器目录（供非root用户使用）
RUN mkdir -p /ms-playwright

# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install --with-deps chromium

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 创建必要的目录结构
RUN mkdir -p /app/logs \
    /app/recordings \
    /app/screenshots \
    && chown -R appuser:appuser /app /ms-playwright

# 复制项目文件
COPY login_getpoints.py ./
COPY config_getpoints.ini ./
COPY playwright_luzhi.py ./
COPY entrypoint.sh ./

# 设置启动脚本权限
RUN chmod +x /app/entrypoint.sh

# 切换非root用户
USER appuser

# 健康检查（检查日志文件是否在更新）
HEALTHCHECK --interval=5m --timeout=30s --start-period=1m --retries=3 \
    CMD test -f /app/logs/openi_automation_$(date +%Y%m%d).log || exit 1

# 数据卷（持久化日志、录制视频、数据库）
VOLUME ["/app/logs", "/app/recordings", "/app/screenshots", "/app/user_records.db"]

# 暴露端口（如果将来需要 Web 界面）
# EXPOSE 8080

# 启动命令
ENTRYPOINT ["/app/entrypoint.sh"]

# 默认参数：单次执行 + 无头模式
CMD ["--once", "--headless"]
