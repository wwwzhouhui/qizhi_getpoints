#!/bin/bash
set -e

# 显示版本信息
echo "============================================================"
echo "OpenI 平台自动化积分获取工具 v0.0.1"
echo "============================================================"
echo "工作目录: $(pwd)"
echo "Python 版本: $(python --version)"
echo "Playwright 版本: $(python -c 'import playwright; print(playwright.__version__)' 2>/dev/null || echo '未安装')"
echo "时区: $TZ"
echo "当前时间: $(date)"
echo "============================================================"

# 检查配置文件
if [ ! -f /app/config_getpoints.ini ]; then
    echo "错误: 配置文件 config_getpoints.ini 不存在"
    exit 1
fi

# 运行自动化脚本（传递所有参数）
echo "启动参数: $@"
echo "============================================================"
exec python3 /app/login_getpoints.py "$@"
