#!/bin/bash
# 快速启动脚本

set -e

echo "============================================================"
echo "OpenI 平台自动化积分获取工具 - 快速启动"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Docker
echo -e "${BLUE}[1/5]${NC} 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker 未安装${NC}"
    echo ""
    echo "请先安装 Docker:"
    echo "  Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
    echo "  或访问: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker 已安装${NC}"

# 检查配置文件
echo -e "${BLUE}[2/5]${NC} 检查配置文件..."
if [ ! -f "config_getpoints.ini" ]; then
    echo -e "${RED}✗ 配置文件 config_getpoints.ini 不存在${NC}"
    echo ""
    echo "请先创建并配置 config_getpoints.ini 文件"
    echo "参考 README.md 中的配置说明"
    exit 1
fi
echo -e "${GREEN}✓ 配置文件存在${NC}"

# 创建必要的目录
echo -e "${BLUE}[3/5]${NC} 创建必要的目录..."
mkdir -p logs recordings screenshots
echo -e "${GREEN}✓ 目录创建完成${NC}"

# 构建镜像
echo -e "${BLUE}[4/5]${NC} 构建 Docker 镜像..."
echo "（首次构建可能需要几分钟，请耐心等待）"
if docker-compose build > /tmp/docker-build.log 2>&1; then
    echo -e "${GREEN}✓ 镜像构建成功${NC}"
else
    echo -e "${RED}✗ 镜像构建失败${NC}"
    echo "错误日志: cat /tmp/docker-build.log"
    exit 1
fi

# 选择运行模式
echo -e "${BLUE}[5/5]${NC} 选择运行模式..."
echo ""
echo "请选择运行模式:"
echo "  1) 测试运��（单次执行，前台显示日志）"
echo "  2) 正式运行（单次执行，后台运行）"
echo "  3) 自动模式（定时执行，后台持续运行）"
echo ""
read -p "请输入选项 [1-3]: " -n 1 -r
echo

case $REPLY in
    1)
        echo ""
        echo -e "${GREEN}▶ 启动测试运行模式...${NC}"
        echo ""
        docker-compose up
        ;;
    2)
        echo ""
        echo -e "${GREEN}▶ 启动后台运行模式...${NC}"
        docker-compose up -d
        echo ""
        echo -e "${GREEN}✓ 容器已启动${NC}"
        echo ""
        echo "查看日志: docker-compose logs -f"
        echo "停止容器: docker-compose down"
        ;;
    3)
        echo ""
        echo -e "${GREEN}▶ 启动自动定时模式...${NC}"
        # 修改 docker-compose.yml 为自动模式
        sed -i 's/command: \["--once", "--headless"\]/command: ["--auto", "--headless"]/' docker-compose.yml
        docker-compose up -d
        echo ""
        echo -e "${GREEN}✓ 自动定时模式已启动${NC}"
        echo ""
        echo "程序将每 24 小时自动执行一次任务"
        echo "查看日志: docker-compose logs -f"
        echo "停止容器: docker-compose down"
        ;;
    *)
        echo ""
        echo -e "${RED}无效的选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo -e "${GREEN}✅ 快��启动完成！${NC}"
echo "============================================================"
echo ""
echo "常用命令:"
echo "  查看日志:       docker-compose logs -f"
echo "  查看容器状态:   docker-compose ps"
echo "  停止容器:       docker-compose down"
echo "  重启容器:       docker-compose restart"
echo "  查看资源使用:   docker stats openi-automation"
echo ""
echo "更多命令请运行: make help"
echo ""
