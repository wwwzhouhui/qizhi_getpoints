# OpenI 积分自动化获取工具

> 基于 Playwright 的 OpenI 平台自动化积分获取工具，支持定时执行、多账号配置、视频录制等完整功能

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Playwright](https://img.shields.io/badge/playwright-1.45+-green.svg)
![Docker](https://img.shields.io/badge/docker-latest-blue.svg)

---

## 项目介绍

OpenI 积分自动化获取工具是一个专业的 OpenI 平台自动化脚本，基于 Playwright 浏览器自动化框架，能够自动完成登录、调试任务管理、Issue 操作、代码提交、PR 操作等一系列操作，帮助用户快速获取 OpenI 平台积分。

### 核心特性

- **自动登录**: 支持账号密码自动登录 OpenI 平台
- **调试任务管理**: 自动启动调试任务、等待完成、查看状态、再次调试（支持配置次数）
- **Issue 操作**: 自动创建 Issue、在最新 Issue 发表评论（支持配置次数）
- **代码提交**: 自动编辑代码文件并提交到 master 分支（支持配置次数）
- **PR 操作**: 自动创建新分支、编辑代码、提交 PR、关闭关联 Issue（支持配置次数）
- **定时执行**: 基于 APScheduler 的定时任务支持，可配置执行间隔
- **视频录制**: 可选的视频录制功能，记录自动化操作过程
- **多账号支持**: 支持多账号配置，实现批量自动化
- **Docker 部署**: 完整的 Docker 容器化部署方案
- **日志系统**: 双输出日志（控制台 + 文件），支持按日轮转

---

## 功能清单

| 功能名称 | 功能说明 | 技术栈 | 状态 |
|---------|---------|--------|------|
| 自动登录 | 账号密码自动登录 | Playwright | ✅ 稳定 |
| 调试任务管理 | 启动/等待/查看/再次调试 | Playwright + XPath | ✅ 稳定 |
| Issue 操作 | 创建 Issue / 发表评论 | Playwright | ✅ 稳定 |
| 代码提交 | 编辑并提交到 master | Playwright | ✅ 稳定 |
| PR 操作 | 创建分支/编辑代码/提交 PR | Playwright | ✅ 稳定 |
| 定时执行 | APScheduler 定时任务 | APScheduler | ✅ 稳定 |
| 视频录制 | 记录操作过程 | Playwright video | ✅ 稳定 |
| 多账号配置 | 批量自动化支持 | INI 配置 | ✅ 稳定 |
| Docker 部署 | 容器化一键部署 | Docker + Compose | ✅ 稳定 |
| 日志系统 | 控制台 + 文件双输出 | Python logging | ✅ 稳定 |

---

## 技术架构

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 主要开发语言 |
| Playwright | 1.45+ | 浏览器自动化框架 |
| APScheduler | 3.10+ | 定时任务调度 |
| Docker | latest | 容器化部署 |
| configparser | - | INI 配置文件解析 |

### 执行流程

```
1. 自动登录 OpenI 平台
   ↓
2. 调试任务管理（可配置次数）
   - 启动调试任务
   - 等待完成
   - 查看状态
   - 再次调试
   ↓
3. Issue 操作（可配置次数）
   - 创建新 Issue
   - 在最新 Issue 发表评论
   ↓
4. 代码提交（可配置次数）
   - 编辑代码文件
   - 提交到 master 分支
   ↓
5. PR 操作（可配置次数）
   - 创建新分支
   - 编辑代码
   - 提交 PR
   - 关闭关联 Issue
   ↓
6. 任务完成，生成日志
```

---

## 安装说明

### 环境要求

- Python 3.8+
- pip 包管理器
- Docker / Docker Compose（可选，推荐使用）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 安装 Playwright 浏览器

```bash
playwright install chromium
```

---

## 使用说明

### 方式一：Docker 部署（推荐）

#### 1. 配置环境变量

编辑 `config_getpoints.ini` 文件，配置你的 OpenI 账号信息：

```ini
[login]
login_url = https://openi.pcl.ac.cn/user/login
cloudbrains_url = https://openi.pcl.ac.cn/zhouhui/wwwdemo/debugjob?debugListType=all
username = your_email@example.com
password = your_password

[settings]
# 浏览器超时时间（毫秒）
browser_timeout = 120000

# 视频录制设置
enable_video_recording = false
video_output_dir = ./recordings

# 定时执行设置
auto_execute_enabled = false
execute_interval = 24:10
execute_on_startup = true
```

#### 2. 使用 Docker Compose

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 3. 使用 Docker 命令

```bash
# 构建镜像
docker build -t openi-getpoints:0.0.1 .

# 运行容器
docker run -d \
  --name openi-automation \
  -v $(pwd)/config_getpoints.ini:/app/config_getpoints.ini:ro \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/recordings:/app/recordings \
  -v $(pwd)/screenshots:/app/screenshots \
  -e TZ=Asia/Shanghai \
  openi-getpoints:0.0.1 --once --headless

# 查看日志
docker logs -f openi-automation

# 停止容器
docker stop openi-automation
```

### 方式二：本地部署

#### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

#### 2. 配置文件

编辑 `config_getpoints.ini`，参考 Docker 部署的配置说明。

#### 3. 运行脚本

**单次执行（有界面，用于调试）**：

```bash
python login_getpoints.py
```

**单次执行（无头模式）**：

```bash
python login_getpoints.py --once --headless
```

**定时执行（无头模式）**：

```bash
python login_getpoints.py --auto --headless
```

---

## 配置说明

### 配置文件结构

`config_getpoints.ini` 包含以下配置节：

| 配置节 | 说明 |
|--------|------|
| `[login]` | 登录配置：URL、用户名、密码 |
| `[xpath]` | XPath 选择器：登录按钮、状态元素等 |
| `[settings]` | 浏览器设置：超时、视频录制、定时执行 |
| `[issues]` | Issue 操作：URL、按钮、输入框 XPath |
| `[code]` | 代码提交：编辑页面 URL、XPath |
| `[branch]` | PR 操作：分支编辑 URL、Compare 页面 URL |

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--auto` | 启用定时执行模式 | `python login_getpoints.py --auto` |
| `--once` | 单次执行模式 | `python login_getpoints.py --once` |
| `--headless` | 无头模式（无浏览器界面） | `python login_getpoints.py --once --headless` |

### 操作次数配置

在代码中可以配置各项操作的执行次数：

```python
# 调试任务次数
DEBUG_AGAIN_TIMES = 3

# Issue 操作次数
ISSUE_OPERATIONS = 3

# 代码提交次数
CODE_COMMIT_TIMES = 3

# PR 操作次数
PR_OPERATIONS = 3
```

---

## 项目结构

```
qizhi_getpoints/
├── login_getpoints.py         # 主程序入口
├── playwright_luzhi.py        # Playwright 录制脚本
├── automation/                # 自动化模块
│   ├── login_automation.py    # 登录自动化逻辑
│   └── Dockerfile            # 模块 Docker 配置
├── requirements.txt           # Python 依赖
├── config_getpoints.ini       # 配置文件
├── Dockerfile                 # 主 Docker 配置
├── docker-compose.yml         # Docker Compose 配置
├── README.md                  # 项目文档
├── logs/                      # 日志目录
│   └── openi_automation_YYYYMMDD.log
├── recordings/                # 视频录制目录
├── screenshots/               # 失败截图目录
└── user_records.db            # 用户记录数据库
```

---

## 开发指南

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 配置环境变量
cp config_getpoints.ini.example config_getpoints.ini
vim config_getpoints.ini

# 运行（有界面模式，便于调试）
python login_getpoints.py
```

### Docker 开发

```bash
# 构建镜像
docker build -t openi-getpoints:0.0.1 .

# 运行容器（挂载配置文件）
docker run -it --rm \
  -v $(pwd)/config_getpoints.ini:/app/config_getpoints.ini:ro \
  openi-getpoints:0.0.1 --once

# 查看日志
docker logs -f openi-automation
```

### 添加新功能

1. 在 `automation/` 目录下创建新模块
2. 在 `config_getpoints.ini` 中添加配置节
3. 在 `login_getpoints.py` 中调用新模块
4. 更新文档和配置示例

---

## 常见问题

<details>
<summary>Q: Docker 容器无法启动？</summary>

A: 检查以下几点：
1. 确认 `config_getpoints.ini` 配置文件存在且格式正确
2. 检查 Docker 守护进程是否运行：`docker ps`
3. 查看容器日志：`docker-compose logs -f`
4. 确认端口没有被占用（本工具不暴露端口，但需确认网络正常）
</details>

<details>
<summary>Q: Playwright 浏览器安装失败？</summary>

A: 尝试以下解决方案：
1. 使用国内镜像：`PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ playwright install chromium`
2. 手动下载浏览器并解压到指定目录
3. 使用 Docker 部署，浏览器已预装在镜像中
</details>

<details>
<summary>Q: 登录失败或验证码问题？</summary>

A:
1. 检查 `config_getpoints.ini` 中的用户名密码是否正确
2. 确认 OpenI 平台登录 URL 未发生变化
3. 如遇验证码，可暂时使用有界面模式手动处理
4. 检查 XPath 选择器是否与实际页面匹配
</details>

<details>
<summary>Q: 定时任务不执行？</summary>

A:
1. 检查 `config_getpoints.ini` 中 `auto_execute_enabled` 是否为 `true`
2. 确认 `execute_interval` 格式正确（HH:MM）
3. 查看日志文件确认定时器是否启动
4. 确认命令行参数中包含 `--auto`
</details>

<details>
<summary>Q: 视频录制功能无法使用？</summary>

A:
1. 确认 `config_getpoints.ini` 中 `enable_video_recording` 为 `true`
2. 检查 `video_output_dir` 目录是否存在且有写入权限
3. Docker 部署时确认 `recordings` 目录已挂载
4. 视频文件可能较大，注意磁盘空间
</details>

<details>
<summary>Q: 如何配置多账号？</summary>

A: 目前支持多账号配置方式：
1. 复制多份 `config_getpoints.ini`，分别配置不同账号
2. 运行多个容器或进程，挂载不同配置文件
3. 或在代码中实现多账号轮询逻辑
</details>

<details>
<summary>Q: XPath 选择器失效怎么办？</summary>

A:
1. OpenI 平台页面结构可能发生变化，需要更新 XPath
2. 使用浏览器开发者工具（F12）检查元素路径
3. 使用相对 XPath 而非绝对路径，提高稳定性
4. 在代码中添加元素等待和重试逻辑
</details>

<details>
<summary>Q: 日志文件过大如何处理？</summary>

A:
1. 日志文件按日轮转，自动创建 `openi_automation_YYYYMMDD.log`
2. 可定期清理旧日志文件
3. Docker 部署时配置了日志大小限制（max-size: 10m）
4. 可在代码中添加日志压缩功能
</details>

<details>
<summary>Q: 如何调试自动化脚本？</summary>

A:
1. 使用有界面模式运行（不添加 `--headless` 参数）
2. 在 `config_getpoints.ini` 中设置 `enable_video_recording = true`
3. 查看日志文件中的详细输出
4. 使用 Playwright Inspector 调试：`PWDEBUG=1 python login_getpoints.py`
</details>

<details>
<summary>Q: 如何适配其他项目？</summary>

A:
1. 修改 `config_getpoints.ini` 中的 URL 和 XPath
2. 根据目标项目页面结构调整选择器
3. 修改代码中的操作逻辑（如调试任务、Issue 等）
4. 充分测试各项功能
</details>

---

## 技术交流群

欢迎加入技术交流群，分享你的使用心得和反馈建议：

![技术交流群](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/20260612_104427_com.tencent.mm.jpg)

---

## 作者联系

- **微信**: laohaibao2025
- **邮箱**: 75271002@qq.com

![微信二维码](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Screenshot_20260123_095617_com.tencent.mm.jpg)

---

## 打赏

如果这个项目对你有帮助，欢迎请我喝杯咖啡 ☕

**微信支付**

![微信支付](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20250914152855543.png)

---

## Star History

如果觉得项目不错，欢迎点个 Star ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=wwwzhouhui/qizhi_getpoints&type=Date)](https://star-history.com/#wwwzhouhui/qizhi_getpoints&Date)

---

## License

MIT License

---

## 免责声明

本项目仅供学习和研究使用，请勿用于商业用途或违反 OpenI 平台服务条款的行为。因使用本项目造成的任何后果，由使用者自行承担。

---

**Enjoy automating your OpenI points collection! 🚀✨**
