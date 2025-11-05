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

# 修复挂载目录权限（解决NAS等环境下的权限问题）
echo "检查并修复目录权限..."
echo "------------------------------------------------------------"

# 创建必要的目录（如果不存在）
mkdir -p /app/logs /app/recordings /app/screenshots || true

# 修复目录所有者为 appuser:appuser
chown -R appuser:appuser /app/logs /app/recordings /app/screenshots || true

# 修复数据库文件权限（如果存在）
if [ -f /app/user_records.db ]; then
    chown appuser:appuser /app/user_records.db || true
fi

echo "✓ 权限修复完成"
echo "  /app/logs -> $(ls -ld /app/logs | awk '{print $3":"$4}')"
echo "  /app/recordings -> $(ls -ld /app/recordings | awk '{print $3":"$4}')"
echo "  /app/screenshots -> $(ls -ld /app/screenshots | awk '{print $3":"$4}')"
echo "============================================================"

# 检查配置文件
if [ ! -f /app/config_getpoints.ini ]; then
    echo "错误: 配置文件 config_getpoints.ini 不存在"
    exit 1
fi

# 运行自动化脚本（传递所有参数）
echo "启动参数: $@"
echo "============================================================"

# 使用 gosu 切换到 appuser 运行（保持 PID 1）
exec gosu appuser python3 /app/login_getpoints.py "$@"
