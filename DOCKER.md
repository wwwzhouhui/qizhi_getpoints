# Docker 部署指南

本文档介绍如何使用 Docker 部署和运行 OpenI 平台自动化积分获取工具。

## 📋 前置要求

### 必需软件
- **Docker**: 20.10.0 或更高版本
- **Docker Compose**: 1.29.0 或更高版本（可选，推荐）

### 系统要求
- **内存**: 至少 2GB 可用内存
- **磁盘**: 至少 5GB 可用空间（用于镜像和浏览器）
- **CPU**: 2核或更多（推荐）

### 配置准备
- 已配置好的 `config_getpoints.ini` 文件（包含账号密码）

## 🚀 快速开始

### 方法1: ��用 Docker Compose（推荐）

#### 1. 构建镜像
```bash
# 在项目目录下执行
docker-compose build
```

#### 2. 启动容器（单次执行模式）
```bash
docker-compose up
```

#### 3. 启动容器（自动定时模式）
编辑 `docker-compose.yml` 文件，修改 command 行：
```yaml
# 将这一行：
command: ["--once", "--headless"]

# 改为：
command: ["--auto", "--headless"]
```

然后启动：
```bash
docker-compose up -d
```

#### 4. 查看日志
```bash
# 实时查看日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100
```

#### 5. 停止容器
```bash
# 停止容器
docker-compose stop

# 停止并删除容器
docker-compose down
```

### 方法2: 直接使用 Docker

#### 1. 构建镜像
```bash
docker build -t openi-getpoints:0.0.1 .
```

#### 2. 运行容器（单次执行）
```bash
docker run --rm \
  -v $(pwd)/config_getpoints.ini:/app/config_getpoints.ini:ro \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/recordings:/app/recordings \
  -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/user_records.db:/app/user_records.db \
  openi-getpoints:0.0.1 --once --headless
```

#### 3. 运行容器（自动定时模式）
```bash
docker run -d \
  --name openi-automation \
  --restart unless-stopped \
  -v $(pwd)/config_getpoints.ini:/app/config_getpoints.ini:ro \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/recordings:/app/recordings \
  -v $(pwd)/screenshots:/app/screenshots \
  -v $(pwd)/user_records.db:/app/user_records.db \
  openi-getpoints:0.0.1 --auto --headless
```

#### 4. 查看容器状态
```bash
# 查看运行中的容器
docker ps

# 查看所有容器（包括已停止的）
docker ps -a

# 查看容器详细信息
docker inspect openi-automation
```

#### 5. 查看日志
```bash
# 实时查看日志
docker logs -f openi-automation

# 查看最近100行日志
docker logs --tail=100 openi-automation
```

#### 6. 进入容器（调试）
```bash
docker exec -it openi-automation /bin/bash
```

#### 7. 停止和删除容器
```bash
# 停止容器
docker stop openi-automation

# 删除容器
docker rm openi-automation
```

## 📝 命令行参数说明

容器启动时可以传递以下参数：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--once` | 单次执行模式（执行一次后退出） | `--once` |
| `--auto` | 自动定时模式（持续运行，定时执行） | `--auto` |
| `--headless` | 无头浏览器模式（不显示浏览器窗口） | `--headless` |

### 常用组合

```bash
# 单次执行 + 无头模式（默认）
command: ["--once", "--headless"]

# 自动定时 + 无头模式
command: ["--auto", "--headless"]

# 单次执行 + 有界面（需要 X11 支持）
command: ["--once"]
```

## 📂 数据持久化

### 挂载的目录和文件

| 宿主机路径 | 容器路径 | 说明 | 是否必需 |
|------------|----------|------|----------|
| `./config_getpoints.ini` | `/app/config_getpoints.ini` | 配置文件（只读） | ✅ 必需 |
| `./logs/` | `/app/logs/` | 日志文件目录 | ⭕ 推荐 |
| `./recordings/` | `/app/recordings/` | 录制视频目录 | ⭕ 可选 |
| `./screenshots/` | `/app/screenshots/` | 失败截图目录 | ⭕ 推荐 |
| `./user_records.db` | `/app/user_records.db` | SQLite数据库 | ⭕ 推荐 |

### 数据备份

```bash
# 备份日志
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/

# 备份数据库
cp user_records.db user_records-backup-$(date +%Y%m%d).db

# 备份录制视频
tar -czf recordings-backup-$(date +%Y%m%d).tar.gz recordings/
```

## 🔧 配置说明

### 修改配置文件

1. 编辑宿主机上的 `config_getpoints.ini`
2. 重启容器以应用更改：
   ```bash
   docker-compose restart
   # 或
   docker restart openi-automation
   ```

### 环境变量

可以在 `docker-compose.yml` 中设置环境变量：

```yaml
environment:
  - TZ=Asia/Shanghai          # 时区设置
  - PYTHONUNBUFFERED=1        # Python 输出不缓冲
```

## 📊 监控和日志

### 查看容器资源使用
```bash
# 实时查看资源使用情况
docker stats openi-automation

# 查看容器详细信息
docker inspect openi-automation
```

### 日志管理

#### 查看应用日志
```bash
# 应用日志位于挂载的 logs 目录
tail -f logs/openi_automation_$(date +%Y%m%d).log

# 搜索特定内容
grep "错误" logs/openi_automation_*.log
```

#### 查看 Docker 容器日志
```bash
# 实时跟踪
docker-compose logs -f

# 查看最近的日志
docker-compose logs --tail=100

# 查看特定时间范围
docker-compose logs --since "2025-11-05T10:00:00"
```

### 健康检查

容器内置健康检查功能，每5分钟检查一次：

```bash
# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' openi-automation

# 查看健康检查日志
docker inspect --format='{{json .State.Health}}' openi-automation | jq
```

## 🐛 故障排查

### 问题1: 容器无法启动

**症状**: 容器启动后立即退出

**解决方案**:
```bash
# 查看容器日志
docker logs openi-automation

# 检查配置文件是否存在
ls -la config_getpoints.ini

# 检查配置文件权限
chmod 644 config_getpoints.ini
```

### 问题2: 配置文件找不到

**症状**: 日志显示 "错误: 配置文件 config_getpoints.ini 不存在"

**解决方案**:
```bash
# 确认配置文件在项目目录
ls config_getpoints.ini

# 确认 docker-compose.yml 中的挂载路径正确
cat docker-compose.yml | grep config_getpoints.ini
```

### 问题3: 浏览器无法启动

**症状**: 日志显示 Playwright 浏览器错误

**解决方案**:
```bash
# 重新构建镜像（确保安装了浏览器）
docker-compose build --no-cache

# 增加内存限制
# 编辑 docker-compose.yml，增加内存限制到 3GB
```

### 问题4: 日志文件不更新

**症状**: logs 目录下没有新的日志文件

**解决方案**:
```bash
# 检查目录权限
ls -la logs/

# 创建日志目录（如果不存在）
mkdir -p logs && chmod 755 logs

# 检查容器内的日志
docker exec openi-automation ls -la /app/logs/
```

### 问题5: 容器占用资源过高

**症状**: CPU 或内存使用率过高

**解决方案**:
```bash
# 查看资源使用
docker stats openi-automation

# 调整资源限制（编辑 docker-compose.yml）
# 减少 CPU 和内存限制
```

## 🔄 更新和维护

### 更新镜像
```bash
# 1. 停止容器
docker-compose down

# 2. 拉取最新代码
git pull

# 3. 重新构建镜像
docker-compose build --no-cache

# 4. 启动容器
docker-compose up -d
```

### 清理旧镜像
```bash
# 查看所有镜像
docker images

# 删除旧版本镜像
docker rmi openi-getpoints:old-version

# 清理未使用的镜像
docker image prune -a
```

### 清理容器和卷
```bash
# 停止并删除容器
docker-compose down

# 删除所有相关卷（⚠️ 会删除数据）
docker-compose down -v

# 清理未使用的容器
docker container prune
```

## 🔐 安全建议

1. **配置文件保护**
   ```bash
   # 设置配置文件为只读
   chmod 400 config_getpoints.ini
   ```

2. **非 root 用户运行**
   - 容器内已使用非 root 用户 `appuser` 运行应用

3. **网络隔离**
   - 如需更高安全性，可配置自定义网络：
   ```yaml
   networks:
     openi-network:
       driver: bridge
       ipam:
         config:
           - subnet: 172.28.0.0/16
   ```

4. **定期更新**
   - 定期更新 Docker 镜像和基础镜像
   - 定期更新 Python 依赖包

## 📞 技术支持

如遇到问题，请提供以下信息：

```bash
# 1. Docker 版本
docker --version
docker-compose --version

# 2. 容器状态
docker ps -a

# 3. 容器日志
docker logs openi-automation --tail=50

# 4. 系统信息
uname -a
free -h
df -h
```

## 📚 参考资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Playwright 文档](https://playwright.dev/python/)
- [项目 README](README.md)

---

**版本**: v0.0.1
**更新日期**: 2025-11-05
