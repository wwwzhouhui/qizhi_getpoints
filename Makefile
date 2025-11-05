.PHONY: help build up down restart logs ps exec clean backup test

# 默认目标：显示帮助
help:
	@echo "OpenI 平台自动化积分获取工具 - Docker 命令"
	@echo ""
	@echo "使用方法: make [目标]"
	@echo ""
	@echo "可用目标:"
	@echo "  build          - 构建 Docker 镜像"
	@echo "  up             - 启动容器（前台运行）"
	@echo "  up-d           - 启动容器（后台运行）"
	@echo "  down           - 停止并删除容器"
	@echo "  restart        - 重启容器"
	@echo "  logs           - 查看实时日志"
	@echo "  logs-tail      - 查看最近100行日志"
	@echo "  ps             - 查看容器状态"
	@echo "  stats          - 查看资源使用情况"
	@echo "  exec           - 进入容器 Shell"
	@echo "  clean          - 清理容器和镜像"
	@echo "  backup         - 备份日志和数据库"
	@echo "  test           - 测试运行（单次执行）"
	@echo "  auto           - 自动定时模式运行"
	@echo "  rebuild        - 完全重新构建（无缓存）"
	@echo "  health         - 检查容器健康状态"

# 构建镜像
build:
	@echo "📦 构建 Docker 镜像..."
	docker-compose build

# 完全重新构建（无缓存）
rebuild:
	@echo "🔨 完全重新构建镜像（无缓存）..."
	docker-compose build --no-cache

# 启动容器（前台）
up:
	@echo "🚀 启动容器（前台运行）..."
	docker-compose up

# 启动容器（后台）
up-d:
	@echo "🚀 启动容器（后台运行）..."
	docker-compose up -d

# 停止并删除容器
down:
	@echo "⏹️  停止并删除容器..."
	docker-compose down

# 重启容器
restart:
	@echo "🔄 重启容器..."
	docker-compose restart

# 查看实时日志
logs:
	@echo "📋 查看实时日志..."
	docker-compose logs -f

# 查看最近100行日志
logs-tail:
	@echo "📋 查看最近100行日志..."
	docker-compose logs --tail=100

# 查看容器状态
ps:
	@echo "📊 查看容器状态..."
	docker-compose ps

# 查看资源使用
stats:
	@echo "📈 查看资源使用情况..."
	docker stats openi-automation

# 进入容器
exec:
	@echo "🔧 进入容器 Shell..."
	docker-compose exec openi-automation /bin/bash

# 清理容器和镜像
clean:
	@echo "🧹 清理容器和镜像..."
	docker-compose down
	docker image prune -f
	@echo "✅ 清理完成"

# 深度清理（包括数据卷）
clean-all:
	@echo "⚠️  警告：这将删除所有数据（日志、录制、数据库）！"
	@read -p "确认继续？[y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf logs/* recordings/* screenshots/* user_records.db; \
		echo "✅ 深度清理完成"; \
	else \
		echo "❌ 取消操作"; \
	fi

# 备份日志和数据库
backup:
	@echo "💾 备份日志和数据库..."
	@mkdir -p backups
	@tar -czf backups/logs-$$(date +%Y%m%d-%H%M%S).tar.gz logs/ 2>/dev/null || true
	@cp user_records.db backups/user_records-$$(date +%Y%m%d-%H%M%S).db 2>/dev/null || true
	@tar -czf backups/recordings-$$(date +%Y%m%d-%H%M%S).tar.gz recordings/ 2>/dev/null || true
	@echo "✅ 备份完成，保存在 backups/ 目录"

# 测试运行（单次执行）
test:
	@echo "🧪 测试运行（单次执行模式）..."
	docker run --rm \
		-v $$(pwd)/config_getpoints.ini:/app/config_getpoints.ini:ro \
		-v $$(pwd)/logs:/app/logs \
		-v $$(pwd)/screenshots:/app/screenshots \
		openi-getpoints:0.0.1 --once --headless

# 自动定时模式
auto:
	@echo "⏰ 启动自动定时模式..."
	@sed -i 's/command: \["--once", "--headless"\]/command: ["--auto", "--headless"]/' docker-compose.yml
	docker-compose up -d
	@echo "✅ 自动定时模式已启动"
	@echo "💡 使用 'make logs' 查看日志"

# 切换回单次模式
once:
	@echo "🔄 切换回单次执行模式..."
	@sed -i 's/command: \["--auto", "--headless"\]/command: ["--once", "--headless"]/' docker-compose.yml
	docker-compose restart
	@echo "✅ 已切换为单次执行模式"

# 健康检查
health:
	@echo "🏥 检查容器健康状态..."
	@docker inspect --format='健康状态: {{.State.Health.Status}}' openi-automation 2>/dev/null || echo "容器未运行"
	@echo ""
	@docker inspect --format='{{range .State.Health.Log}}时间: {{.Start}}, 退出码: {{.ExitCode}}{{"\n"}}{{end}}' openi-automation 2>/dev/null || true

# 查看版本信息
version:
	@echo "📌 版本信息:"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"
	@docker run --rm openi-getpoints:0.0.1 python3 --version 2>/dev/null || echo "镜像未构建"

# 安装（首次使用）
install: build
	@echo "✅ 镜像构建完成"
	@echo ""
	@echo "📝 下一步:"
	@echo "1. 确保 config_getpoints.ini 文件已正确配置"
	@echo "2. 运行 'make test' 进行测试"
	@echo "3. 运行 'make up-d' 启动服务"
	@echo "4. 运行 'make logs' 查看日志"
