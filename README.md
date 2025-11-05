# OpenI 平台自动化积分获取工具

基于 Playwright 的 Python 自动化脚本，用于在 OpenI 平台上自动执行各种操作以获取积分。支持多账号配置，操作包括调试任务管理、Issue 创建与评论、代码提交、分支合并请求等。

## 📋 目录

- [功能概览](#功能概览)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [Docker 部署](#docker-部署推荐)
- [多账号配置](#多账号配置)
- [配置文件详解](#配置文件详解)
- [使用说明](#使用说明)
- [常见问题](#常见问题)
- [免责声明](#免责声明)

## ✨ 功能概览

### 核心功能

1. **自动登录与弹框处理**
   - 自动登录 OpenI 平台
   - 智能处理登录后的公告弹框（自动勾选"不再提醒"、等待倒计时、点击关闭）

2. **调试任务管理**
   - 访问 CloudBrains 调试任务列表
   - 检测首条任务状态（STOPPED/RUNNING）
   - 自动触发"再次调试"操作
   - 等待任务状态变为 RUNNING

3. **Issue 操作（3次）**
   - 创建新 Issue（随机生成标题和内容）
   - 在创建的 Issue 下立即添加评论（随机评论内容）
   - 批量执行 3 次

4. **代码提交（3次）**
   - 直接在 master 分支上编辑代码文件（zz2.py）
   - 追加代码内容（"111"）
   - 提交变更��� master 分支
   - 批量执行 3 次

5. **分支合并请求（3次）**
   - 在新分支上编辑代码文件（zz.py）
   - 添加随机代码内容
   - 创建新分支并提交
   - 自动创建 Pull Request（合并请求）
   - 批量执行 3 次

6. **任务关闭操作（新增）**
   - 所有批量任务完成后，自动关闭 RUNNING 状态的任务
   - 智能定位"停止"按钮（基于首行状态相对定位）
   - 多策略容错机制确保关闭成功

### 技术特点

- ✅ **CodeMirror 编辑器支持**：正确触发表单验证事件，确保代码编辑生效
- ✅ **智能按钮状态检测**：自动等待按钮从 disabled 变为 enabled
- ✅ **多策略容错机制**：XPath定位 + 文本定位 + JavaScript强制点击
- ✅ **智能元素定位**：基于首行状态的相对定位，参考"再次调试"的成功经验
- ✅ **完整执行流程**：11步完整任务流程，包括任务启动和关闭
- ✅ **详细日志系统**：双重日志输出（控制台+文件），按日期自动轮转
- ✅ **数据库状态管理**：SQLite记录运行状态，避免重复执行
- ✅ **失败截图保存**：每个失败步骤自动保存截图便于调试
- ✅ **配置文件驱动**：所有 URL、XPath、参数可配置
- ✅ **定时执行支持**：支持自动定时执行模式（随机间隔）

## 🔧 环境要求

- **Python**: 3.8+
- **操作系统**: Linux / macOS / Windows (WSL2)
- **依赖库**:
  - playwright (异步浏览器自动化)
  - asyncio (异步 IO)

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install playwright

# 安装 Playwright 浏览器（Chromium）
playwright install chromium
```

### 2. 配置文件

复制并编辑配置文件：

```bash
cp config_getpoints.ini my_config.ini
# 编辑 my_config.ini，填写你的账号信息和项目路径
```

**最小配置示例**：

```ini
[login]
login_url = https://openi.pcl.ac.cn/user/login
cloudbrains_url = https://openi.pcl.ac.cn/你的用户名/你的项目名/debugjob?debugListType=all
username = 你的用户名或邮箱
password = 你的密码

[issues]
issues_url = https://openi.pcl.ac.cn/你的用户名/你的项目名/issues

[code]
code_edit_url = https://openi.pcl.ac.cn/你的用户名/你的项目名/_edit/master/zz2.py

[branch]
branch_edit_url = https://openi.pcl.ac.cn/你的用户名/你的项目名/_edit/master/zz.py
compare_base_url = https://openi.pcl.ac.cn/你的用户名/你的项目名/compare/master
```

#### 创建项目

 参考截图如下

![image-20251104234609033](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20251104234609033.png)

 其中zz.py 、zz2.py 随便填写内容。 

![image-20251104234704428](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20251104234704428.png)

![image-20251104234736823](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20251104234736823.png)

#### 创建云脑任务

![image-20251104234918558](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20251104234918558.png)

云脑任务链接如下：

https://openi.pcl.ac.cn/wwdahuihui/wwxiaohuidemo3/debugjob?debugListType=all

### 3. 运行脚本

```bash
# 使用默认配置文件（config_getpoints.ini）
python3 login_getpoints.py

# 使用自定义配置文件
# 需要修改代码中的 config_file 参数
```

## 🐳 Docker 部署（推荐）

Docker 部署方式提供了更好的隔离性和可移植性，适合在服务器上长期运行。

### 快速启动

#### 1. 安装 Docker
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh

# 验证安装
docker --version
docker-compose --version
```

#### 2. 构建并运行
```bash
# 方式1: 使用 Makefile（推荐）
make install     # 首次安装，构建镜像
make test        # 测试运行（单次执行）
make up-d        # 启动服务（后台运行）
make logs        # 查看日志

# 方式2: 使用 Docker Compose
docker-compose build                    # 构建镜像
docker-compose up -d                    # 启动服务
docker-compose logs -f                  # 查看日志

# 方式3: 使用 Docker 命令
docker build -t openi-getpoints:0.0.1 .
docker run --rm \
  -v $(pwd)/config_getpoints.ini:/app/config_getpoints.ini:ro \
  -v $(pwd)/logs:/app/logs \
  openi-getpoints:0.0.1 --once --headless
```

#### 3. 测试配置
```bash
# 运行配置测试脚本
./docker-test.sh
```

### Docker 运行模式

#### 单次执行模式
```bash
# 执行一次后自动退出
make test
# 或
docker-compose up
```

#### 自动定时模式
```bash
# 后台持续运行，定时执行任务
make auto
# 或编辑 docker-compose.yml:
# command: ["--auto", "--headless"]
docker-compose up -d
```

### 常用命令

| 命令 | 说明 |
|------|------|
| `make help` | 显示所有可用命令 |
| `make build` | 构建镜像 |
| `make up` | 启动容器（前台） |
| `make up-d` | 启动容器（后台） |
| `make logs` | 查看实时日志 |
| `make logs-tail` | 查看最近100行日志 |
| `make restart` | 重启容器 |
| `make down` | 停止容器 |
| `make ps` | 查看容器状态 |
| `make stats` | 查看资源使用 |
| `make exec` | 进入容器Shell |
| `make backup` | 备份日志和数据 |
| `make clean` | 清理容器和镜像 |

### 数据持久化

Docker 部署会自动挂载以下目录：

```
宿主机              →  容器内
./config_getpoints.ini  →  /app/config_getpoints.ini  (配置文件)
./logs/                 →  /app/logs/                 (日志目录)
./recordings/           →  /app/recordings/           (录制视频)
./screenshots/          →  /app/screenshots/          (失败截图)
./user_records.db       →  /app/user_records.db       (数据库)
```

### 监控和维护

```bash
# 查看容器状态
docker ps

# 查看资源使用
docker stats openi-automation

# 查看容器日志
docker logs -f openi-automation

# 查看应用日志
tail -f logs/openi_automation_$(date +%Y%m%d).log

# 健康检查
docker inspect --format='{{.State.Health.Status}}' openi-automation

# 备份数据
make backup
```

### 故障排查

详细的 Docker 部署指南、故障排查和最佳实践，请参考：
📚 **[Docker 部署完整指南](DOCKER.md)**

## 👥 多账号配置

本工具支持多个 OpenI 账号，通过不同的配置文件管理。

### 配置文件命名规范

推荐使用以下命名方式：

```
config_getpoints.ini                    # 默认配置（账号1）
config_getpoints_账号名.ini             # 账号2
config_getpoints_20251104.ini           # 按日期标识的配置
config_getpoints_备用账号.ini           # 按用途标识的配置
```

### 多账号配置示例

项目提供了两个配置文件示例：

#### 账号1: `config_getpoints.ini`
```ini
[login]
username = wwdahuihui
cloudbrains_url = https://openi.pcl.ac.cn/wwdahuihui/wwxiaohuidemo3/debugjob?debugListType=all
issues_url = https://openi.pcl.ac.cn/wwdahuihui/wwxiaohuidemo3/issues
```

#### 账号2: `config_getpoints 20251104.ini`
```ini
[login]
username = 75271002@qq.com
cloudbrains_url = https://openi.pcl.ac.cn/wwxiaohuihui/wwxiaohuidemo/debugjob?debugListType=all
issues_url = https://openi.pcl.ac.cn/wwxiaohuihui/wwxiaohuidemo/issues
```

### 切换账号

**方法1: 重命名配置文件**（推荐）

```bash
# 使用账号1
cp config_getpoints.ini config_getpoints.ini.backup
cp config_account1.ini config_getpoints.ini
python3 login_getpoints.py

# 切换到账号2
cp config_getpoints.ini.backup config_getpoints.ini
cp config_account2.ini config_getpoints.ini
python3 login_getpoints.py
```

**方法2: 修改代码指定配置文件**

编辑 `login_getpoints.py` 第 12 行：

```python
# 原来：
def __init__(self, config_file: str = "config_getpoints.ini") -> None:

# 改为：
def __init__(self, config_file: str = "config_getpoints_账号2.ini") -> None:
```

**方法3: 使用软链接**（Linux/macOS）

```bash
# 创建多个配置文件
config_account1.ini
config_account2.ini

# 创建软链接指向当前使用的配置
ln -sf config_account1.ini config_getpoints.ini
python3 login_getpoints.py

# 切换账号
ln -sf config_account2.ini config_getpoints.ini
python3 login_getpoints.py
```

### 新增账号步骤

1. **复制配置模板**
   ```bash
   cp config_getpoints.ini config_new_account.ini
   ```

2. **修改账号信息**
   编辑 `config_new_account.ini`：
   ```ini
   [login]
   username = 新账号用户名
   password = 新账号密码
   cloudbrains_url = https://openi.pcl.ac.cn/新用户名/新项目名/debugjob?debugListType=all
   ```

3. **修改项目路径**
   替换所有 URL 中的用户名和项目名：
   ```ini
   [issues]
   issues_url = https://openi.pcl.ac.cn/新用户名/新项目名/issues
   
   [code]
   code_edit_url = https://openi.pcl.ac.cn/新用户名/新项目名/_edit/master/zz2.py
   
   [branch]
   branch_edit_url = https://openi.pcl.ac.cn/新用户名/新项目名/_edit/master/zz.py
   compare_base_url = https://openi.pcl.ac.cn/新用户名/新项目名/compare/master
   ```

4. **验证XPath**（可选）
   - 如果页面结构不同，可能需要调整 XPath
   - 使用浏览器开发者工具复制元素的 XPath

5. **测试运行**
   ```bash
   python3 login_getpoints.py
   ```

## 📝 配置文件详解

### 完整配置文件结构

```ini
[login]
# 登录页面URL（通常固定）
login_url = https://openi.pcl.ac.cn/user/login

# 调试任务列表页URL（需替换用户名和项目名）
cloudbrains_url = https://openi.pcl.ac.cn/用户名/项目名/debugjob?debugListType=all

# 登录账号（可以是用户名或邮箱）
username = 你的用户名

# 登录密码
password = 你的密码

[xpath]
# 登录页面元素定位（一般不需要修改）
username_xpath = /html/body/div[2]/div[2]/div/div/div[2]/div/div[2]/div/div[2]/div/form/div[1]/div/input
password_xpath = /html/body/div[2]/div[2]/div/div/div[2]/div/div[2]/div/div[2]/div/form/div[2]/div/input[1]
login_button_xpath = /html/body/div[2]/div[2]/div/div/div[2]/div/div[2]/div/div[2]/div/form/div[5]/button

# 调试任务页面元素定位
first_status_xpath = /html/body/div[2]/div[2]/div[2]/div[1]/div[2]/div[2]/div/div[3]/table/tbody/tr/td[3]/div/div/span
debug_again_button_xpath = /html/body/div[2]/div[2]/div[2]/div[1]/div[2]/div[2]/div/div[4]/div[2]/table/tbody/tr/td[11]/div/div/div/div/a[1]

# 弹窗关闭按钮（可选）
popup_close_button_xpath = /html/body/div[5]/div/div[3]

[settings]
# 浏览器超时时间（毫秒）
browser_timeout = 120000

[issues]
# Issues列表页URL（需替换用户名和项目名）
issues_url = https://openi.pcl.ac.cn/用户名/项目名/issues

# Issues页面元素定位（一般不需要修改）
issues_create_button_xpath = /html/body/div[2]/div[2]/div[2]/div[1]/div[3]/a
issues_new_title_input_xpath = /html/body/div[2]/div[2]/div[2]/form/div[1]/div/div/div/div[1]/input
issues_submit_button_xpath = /html/body/div[2]/div[2]/div[2]/form/div[1]/div/div/div/div[5]/button

# Issue评论元素定位
issue_latest_link_xpath = /html/body/div[2]/div[2]/div[2]/div[5]/li[1]/a
issue_comment_textarea_xpath = /html/body/div[2]/div[2]/div[2]/div[3]/div[1]/div[2]/ui/div[2]/div/form/div[2]/div[1]/div[2]/div[6]
issue_comment_button_xpath = /html/body/div[2]/div[2]/div[2]/div[3]/div[1]/div[2]/ui/div[2]/div/form/div[4]/div/button

[code]
# 代码编辑页URL（用于直接提交到master分支）
# 需替换用户名、项目名、文件名（zz2.py）
code_edit_url = https://openi.pcl.ac.cn/用户名/项目名/_edit/master/zz2.py

# 代码编辑器元素定位（一般不需要修改）
code_editor_xpath = /html/body/div[2]/div[2]/div[2]/form/div[2]/div[2]/div/div/div[1]/div[2]/div[1]/div[4]
code_commit_button_xpath = /html/body/div[2]/div[2]/div[2]/form/div[3]/button

[branch]
# 分支编辑页URL（用于创建新分支并提交PR）
# 需替换用户名、项目名、文件名（zz.py）
branch_edit_url = https://openi.pcl.ac.cn/用户名/项目名/_edit/master/zz.py

# Compare页面基础URL（用于构建compare页面URL）
# 格式：{compare_base_url}...{branch_name}
compare_base_url = https://openi.pcl.ac.cn/用户名/项目名/compare/master
```

### 配置项说明

| 配置项 | 必填 | 说明 | 示例 |
|-------|------|------|------|
| `login_url` | ✅ | 登录页面URL | `https://openi.pcl.ac.cn/user/login` |
| `cloudbrains_url` | ✅ | 调试任务列表页 | `https://openi.pcl.ac.cn/用户名/项目名/debugjob?debugListType=all` |
| `username` | ✅ | 登录用户名或邮箱 | `user@example.com` |
| `password` | ✅ | 登录密码 | `your_password` |
| `issues_url` | ✅ | Issues列表页 | `https://openi.pcl.ac.cn/用户名/项目名/issues` |
| `code_edit_url` | ✅ | 代码编辑页（master分支） | `https://openi.pcl.ac.cn/用户名/项目名/_edit/master/zz2.py` |
| `branch_edit_url` | ✅ | 分支编辑页 | `https://openi.pcl.ac.cn/用户名/项目名/_edit/master/zz.py` |
| `compare_base_url` | ✅ | Compare页基础URL | `https://openi.pcl.ac.cn/用户名/项目名/compare/master` |
| `browser_timeout` | ⭕ | 浏览器超时时间（毫秒） | `120000` |
| 其他 xpath 配置 | ⭕ | 元素定位路径（通常不需要修改） | - |

### URL 替换规则

所有 URL 中需要替换的部分：

```
https://openi.pcl.ac.cn/用户名/项目名/...
                      ↑       ↑
                      |       └─ 你的项目名称（如 wwxiaohuidemo）
                      └───────── 你的 OpenI 用户名（如 wwxiaohuihui）
```

**示例**：
- 原始：`https://openi.pcl.ac.cn/wwxiaohuihui/wwxiaohuidemo/issues`
- 替换为：`https://openi.pcl.ac.cn/你的用户名/你的项目名/issues`

### 定时执行配置（新增）

在 `[settings]` 段中新增了以下配置项：

```ini
[settings]
# 浏览器设置
browser_timeout = 120000

# 视频录制设置
enable_video_recording = false
video_output_dir = ./recordings

# 定时执行设置（新增）
auto_execute_enabled = false        # 是否启用自动定时执行
execute_interval = 24:10            # 执行间隔：24小时+10分钟
execute_on_startup = true           # 启动时立即执行一次
```

| 配置项 | 说明 | 默认值 | 可选值 |
|--------|------|--------|--------|
| `auto_execute_enabled` | 是否启用自动定时执行模式 | false | true/false |
| `execute_interval` | 执行间隔时间 | 24:10 | HH:MM 格式 |
| `execute_on_startup` | 启动时是否立即执行一次 | true | true/false |

**说明**：
- 启用定时执行后，程序将每 24小时10分钟自动执行一次任务
- 启动时立即执行一次，方便测试和首次运行
- 定时模式下程序会持续运行，按 Ctrl+C 可优雅退出

## 📖 使用说明

### 命令行参数（新增）

程序支持以下命令行参数：

```bash
python3 login_getpoints.py [选项]
```

**可用选项**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `--auto` | 启用自动定时执行模式（使用配置文件中的设置） | `python3 login_getpoints.py --auto` |
| `--once` | 单次执行模式（忽略配置文件中的自动执行设置） | `python3 login_getpoints.py --once` |
| `--headless` | 以无头模式运行浏览器（不显示浏览器窗口） | `python3 login_getpoints.py --headless` |
| `-h, --help` | 显示帮助信息并退出 | `python3 login_getpoints.py --help` |

**参数优先级**：
`--once` > `--auto` > 默认（单次执行）

**使用示例**：

```bash
# 1. 手动执行一次（默认模式）
python3 login_getpoints.py

# 2. 无头模式执行一次（不显示浏览器）
python3 login_getpoints.py --headless

# 3. 强制单次执行（忽略配置文件中的 auto_execute_enabled）
python3 login_getpoints.py --once

# 4. 启用自动模式（需要配置文件中 auto_execute_enabled=true）
python3 login_getpoints.py --auto

# 5. 自动模式 + 无头浏览器
python3 login_getpoints.py --auto --headless

# 6. 显示帮助信息
python3 login_getpoints.py --help
```

### 执行模式说明（新增）

#### 1. 单次执行模式
- 执行一次完整任务流程
- 执行完成后程序退出
- 适合手动触发或测试
- 默认模式（不启用自动执行时）

#### 2. 自动定时模式
- 启动时立即执行一次（如果启用）
- 每隔 24小时10分钟自动执行
- 持续在后台运行
- 按 `Ctrl+C` 优雅退出
- 任务执行失败会记录日志但不影响下次执行

**启动方式**：
- 命令行：`python3 login_getpoints.py --auto`
- 配置文件：在 `config_getpoints.ini` 中设置 `auto_execute_enabled = true`

### 基本使用

```bash
# 1. 确保配置文件正确
vim config_getpoints.ini

# 2. 运行脚本（非无头模式，可看到浏览器操作）
python3 login_getpoints.py
```

### 执行流程

脚本会按以下顺序自动执行完整的任务流程：

```
1. 登录 OpenI 平台
   └─ 自动填写用户名和密码
   └─ 处理登录后的公告弹框（勾选"不再提醒"并关闭）
   ↓
2. 访问调试列表页，检测任务状态
   └─ 访问 CloudBrains 调试任务列表
   └─ 读取首条任务的状态信息
   ↓
3. 任务状态处理
   ├─ 如果是 STOPPED → 触发"再次调试" → 等待变为 RUNNING
   └─ 如果是 RUNNING → 直接继续执行后续任务
   ↓
4. 保存运行状态到数据库
   └─ 记录任务开始时间和状态信息（避免重复执行）
   ↓
5. 休眠 5 秒
   └─ 等待系统稳定后开始批量操作
   ↓
6. 批量创建 Issue + 评论（3次）
   ├─ 第1次：创建随机标题 Issue → 添加随机评论
   ├─ 第2次：创建随机标题 Issue → 添加随机评论
   └─ 第3次：创建随机标题 Issue → 添加随机评论
   ↓
7. 批量代码提交（3次）
   ├─ 第1次：编辑 zz2.py → 追加 "111" → 提交到 master
   ├─ 第2次：编辑 zz2.py → 追加 "111" → 提交到 master
   └─ 第3次：编辑 zz2.py → 追加 "111" → 提交到 master
   ↓
8. 批量分支合并请求（3次）
   ├─ 第1次：编辑 zz.py → 添加随机代码 → 创建新分支 → 提交PR
   ├─ 第2次：编辑 zz.py → 添加随机代码 → 创建新分支 → 提交PR
   └─ 第3次：编辑 zz.py → 添加随机代码 → 创建新分支 → 提交PR
   ↓
9. ⭐ 执行关闭任务操作（点击"停止"按钮）
   └─ 返回调试列表页
   └─ 智能定位首行任务的"停止"按钮
   └─ 点击"停止"按钮关闭 RUNNING 任务
   ↓
10. 输出最终结果统计
   ├─ Issue创建: ✓/✗
   ├─ 代码提交: ✓/✗
   ├─ 分支合并: ✓/✗
   └─ 任务关闭: ✓/✗
   ↓
11. 保持浏览器打开 30 秒后自动关闭
   └─ 便于查看最终执行结果
   └─ 自动清理资源并退出
```

**执行时间说明**：
- 整个流程大约需要 **5-10 分钟**（取决于网络速度）
- Issue创建：每次约30-60秒
- 代码提交：每次约20-40秒
- 分支合并：每次约40-80秒

### 日志输出

脚本会输出详细的操作日志，包含完整的执行流程：

```
============================================================
开始执行任务 [20251105_142659]
============================================================

✓ 登录操作完成
✓ 弹框已完全消失
当前任务状态: RUNNING
✓ 任务已经处于RUNNING状态

任务已RUNNING，休眠 5 秒后开始执行批量操作...

============================================================
开始批量Issue创建与评论任务...
============================================================
✓✓✓ 第 1 个任务完成（创建 + 评论）✓✓✓
✓✓✓ 第 2 个���务完成（创建 + 评论）✓✓✓
✓✓✓ 第 3 个任务完成（创建 + 评论）✓✓✓
✓ Issue 创建与评论结果：全部成功

============================================================
开始批量代码提交任务...
============================================================
✓✓✓ 第 1 个代码提交完成 ✓✓✓
✓✓✓ 第 2 个代码提交完成 ✓✓✓
✓✓✓ 第 3 个代码提交完成 ✓✓✓
✓ 代码提交结果：全部成功

============================================================
开始批量分支合并任务...
============================================================
✓✓✓ 第 1 个分支合并任务完成 ✓✓✓
✓✓✓ 第 2 个分支合并任务完成 ✓✓✓
✓✓✓ 第 3 个分支合并任务完成 ✓✓✓
✓ 分支合并结果：全部成功

============================================================
所有批量任务已完成，开始执行关闭任务操作...
============================================================
策略0: 基于首行状态进行相对定位（推荐）...
✓ 策略0成功：通过 evaluate 点击'停止'

============================================================
任务 [20251105_142659] 执行完成
============================================================
Issue创建: ✓
代码提交: ✓
分支合并: ✓
任务关闭: ✓
============================================================

任务完成，保持浏览器打开 30 秒以便查看...
```

### 失败时的截图

如果某个步骤失败，脚本会自动保存截图到当前目录：

```
debug_again_click_fail.png        # 点击"再次调试"失败
issue_create_fail_1.png          # Issue创建失败（第1次）
comment_fill_fail_1.png          # 评论填写失败（第1次）
comment_submit_fail_1.png        # 评论提交失败（第1次）
commit_button_fail_1.png         # 代码提交按钮失败（第1次）
commit_task_fail_1.png           # 代码提交任务失败（第1次）
branch_code_fill_fail_1.png      # 分支代码填写失败（第1次）
propose_fail_1.png               # "提议文件更改"点击失败（第1次）
merge_fail_1.png                 # "创建合并请求"点击失败（第1次）
pr_fail_1.png                    # PR最终提交失败（第1次）
branch_merge_fail_1.png          # 分支合并任务失败（第1次）
stop_button_fail.png             # 点击"停止"按钮失败（新增）
```

### 无头模式运行

如果需要在服务器上无界面运行：

编辑 `login_getpoints.py` 最后一行：

```python
# 原来：
success = await bot.run(headless=False)

# 改为：
success = await bot.run(headless=True)
```

### 视频录制功能 📹

工具支持两种方式录制操作过程：

#### 方法1：使用 playwright_luzhi.py（推荐）

这是一个独立的录制脚本，会自动录制整个操作过程。

**使用步骤**：

```bash
# 直接运行录制脚本
python3 playwright_luzhi.py
```

**特点**：
- ✅ 独立运行，不影响原脚本
- ✅ 自动录制整个过程
- ✅ 视频保存在 `./recordings/` 目录
- ✅ 自动添加时间戳命名：`openi_automation_20251104_123456.webm`

**输出示例**：
```
============================================================
Playwright 录制启动脚本 v1.0
============================================================
配置文件: config_getpoints.ini
视频保存: ./recordings/openi_automation_20251104_143025.webm
录制模式: 有界面模式
============================================================

✓ 浏览器已启动，开始录制
...
✓ 视频已保存到：./recordings/openi_automation_20251104_143025.webm

提示：WebM 格式可用 VLC、Chrome 浏览器播放
如需转换为 MP4，可使用命令：
  ffmpeg -i ./recordings/openi_automation_20251104_143025.webm output.mp4
```

#### 方法2：在配置文件中启用录制

修改 `config_getpoints.ini`：

```ini
[settings]
browser_timeout = 120000

# 启用视频录制
enable_video_recording = true
video_output_dir = ./recordings
```

然后正常运行主脚本：

```bash
python3 login_getpoints.py
```

**特点**：
- ✅ 无需额外脚本
- ✅ 配置简单
- ✅ 可随时开关

#### 视频格式说明

- **默认格式**: WebM（体积小，质量好）
- **分辨率**: 1920x1080
- **播放方式**:
  - Chrome 浏览器（直接拖入即可播放）
  - VLC Media Player
  - ffplay（命令行）

#### 转换为 MP4 格式

如果需要 MP4 格式（兼容性更好），可使用 ffmpeg 转换：

```bash
# 安装 ffmpeg（如果未安装）
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows: 从 https://ffmpeg.org 下载

# 转换命令
ffmpeg -i recordings/openi_automation_20251104_143025.webm output.mp4

# 高质量转换（保持原始质量）
ffmpeg -i recordings/openi_automation_20251104_143025.webm -c:v libx264 -crf 18 -c:a aac -b:a 192k output.mp4

# 压缩转换（体积更小）
ffmpeg -i recordings/openi_automation_20251104_143025.webm -c:v libx264 -crf 23 -c:a aac -b:a 128k output.mp4
```

#### 录制目录结构

```
qizhi_getpoints/
├── recordings/                                    # 视频保存目录
│   ├── openi_automation_20251104_143025.webm     # 录制的视频
│   ├── openi_automation_20251104_150132.webm
│   └── ...
├── login_getpoints.py
└── playwright_luzhi.py                            # 录制脚本
```

## ❓ 常见问题

### 1. 登录失败

**现象**: 提示"登录失败"

**解决方案**:
- 检查 `config_getpoints.ini` 中的 `username` 和 `password` 是否正确
- 检查网络连接
- 查看是否需要验证码（当前不支持验证码）

### 2. XPath 定位失败

**现象**: 提示"未找到元素"或"定位数量为0"

**解决方案**:
1. 使用浏览器开发者工具（F12）检查元素
2. 右键元素 → 复制 → XPath
3. 更新配置文件中对应的 xpath 配置

### 3. 按钮一直是 disabled 状态

**现象**: 日志显示"按钮15秒后仍未enabled"

**原因**: CodeMirror 编辑器内容更新未触发表单验证

**解决方案**:
- 当前版本已修复此问题（使用 CodeMirror API + 键盘输入）
- 如仍有问题，检查是否使用了最新版本代码

### 4. 多个相同的 Issue

**现象**: 创建了重复的 Issue

**说明**: 这是正常的，脚本会创建3个 Issue（每次随机标题）

**调整方法**: 修改代码第 1693、1718 行的 `times=3` 参数

### 5. 浏览器一直不关闭

**现象**: 脚本执行完成后浏览器还开着

**说明**: 这是设计行为，方便查看执行结果（当前版本保持30秒）

**调整方法**: 修改代码第 2174 行的等待时间：

```python
# 原来：保持30秒
await asyncio.sleep(30)

# 改为：保持10分钟
await asyncio.sleep(600)

# 或者：立即关闭
await asyncio.sleep(5)
```

### 6. 如何修改任务执行次数

编辑 `login_getpoints.py`：

```python
# 第2128行：Issue创建与评论次数（默认3次）
issue_result = await self._create_and_comment_batch(page, times=3)

# 第2136行：代码提交次数（默认3次）
code_result = await self._commit_code_batch(page, times=3)

# 第2144行：分支合并次数（默认3次）
branch_result = await self._create_branch_and_merge_batch(page, times=3)
```

将 `times=3` 改为你想要的次数（例如 `times=5` 表示执行5次）。

### 7. 项目文件不存在

**现象**: 提示找不到 `zz.py` 或 `zz2.py` 文件

**解决方案**:
1. 在你的 OpenI 项目中创建这两个文件
2. 或者修改配置文件中的文件名：

```ini
[code]
code_edit_url = https://openi.pcl.ac.cn/用户名/项目名/_edit/master/你的文件.py

[branch]
branch_edit_url = https://openi.pcl.ac.cn/用户名/项目名/_edit/master/另一个文件.py
```

### 8. 定时任务不执行（新增）

**现象**: 启用自动模式后，程序启动一次就退出了

**解决方案**:
1. 确认是否使用了正确的启动方式：
   ```bash
   # 正确：启用自动模式
   python3 login_getpoints.py --auto

   # 或者：启用配置文件中的 auto_execute_enabled
   ```

2. 检查 `config_getpoints.ini` 配置：
   ```ini
   [settings]
   auto_execute_enabled = true    # 必须设为 true
   ```

3. 查看日志确认调度器状态：
   ```
   ============================================================
   执行模式：自动定时执行
   ============================================================
   定时调度器已启动
   ============================================================
   执行间隔：24小时10分钟 (1450分钟)
   启动时立即执行：是
   ============================================================
   ```

### 9. 定时模式下程序无法退出（新增）

**现象**: 按 Ctrl+C 后程序无响应

**解决方案**:
1. 确认已按下 `Ctrl+C` 并等待程序响应（可能需要等待几秒钟）
2. 程序会优雅退出，正在关闭调度器...
3. 如果长时间无响应，可以强制结束进程：
   ```bash
   # 查找进程
   ps aux | grep login_getpoints.py

   # 强制结束
   kill -9 <PID>
   ```

### 10. 定时任务间隔时间不对（新增）

**现象**: 程序没有按照 24小时+10分钟执行

**说明**: 当前版本间隔时间固定为 24小时10分钟（1450分钟），暂不支持自定义

**解决方案**: 如需修改间隔时间，可编辑 `login_getpoints.py` 第 1754 行：

```python
# 当前：1450 分钟 = 24*60 + 10
interval_minutes = 24 * 60 + 10  # 1450 分钟

# 修改为其他间隔（例如 12小时）：
interval_minutes = 12 * 60  # 720 分钟
```

## 📂 项目结构

```
qizhi_getpoints/
├── login_getpoints.py              # 主脚本
├── playwright_luzhi.py             # 视频录制脚本
├── config_getpoints.ini            # 默认配置文件（账号1）
├── config_getpoints 20251104.ini   # 备用配置文件（账号2）
├── README.md                       # 项目文档
├── DOCKER.md                       # Docker 部署完整指南（新增）
├── requirements.txt                # Python 依赖
├── Dockerfile                      # Docker 镜像构建文件（新增）
├── docker-compose.yml              # Docker Compose 配置（新增）
├── .dockerignore                   # Docker 构建忽略文件（新增）
├── Makefile                        # 常用命令快捷方式（新增）
├── docker-test.sh                  # Docker 配置测试脚本（新增）
├── recordings/                     # 视频录制输出目录（自动创建）
│   └── openi_automation_*.webm    # 录制的视频文件
├── logs/                          # 日志输出目录
│   └── openi_automation_*.log     # 按日期命名的日志文件
├── screenshots/                    # 失败截图保存目录（自动创建）
│   ├── debug_again_click_fail.png
│   ├── issue_create_fail_*.png
│   ├── stop_button_fail.png       # 关闭按钮失败截图（新增）
│   └── ...
└── user_records.db                 # SQLite 数据库（运行时生成）
```

## 📝 日志系统（新增 v2.2）

### 日志输出特性

程序现在支持**双重日志输出**：
1. **控制台输出**：显示 INFO 级别及以上日志（简洁，便于实时查看）
2. **文件输出**：记录 DEBUG 级别及以上所有日志（详细，便于故障排查）

### 日志文件位置

- **目录**：`./logs/`
- **文件命名**：`openi_automation_YYYYMMDD.log`
- **示例**：`logs/openi_automation_20251105.log`

### 日志格式

```
时间 - 级别 - 消息
HH:MM:SS - INFO - 具体日志内容
```

**示例**：
```
10:34:19 - INFO - 定时调度器已启动（随机间隔模式）
10:34:19 - INFO - 下次执行时间：立即执行
10:34:20 - INFO - 开始执行任务 [20251105_103419]
10:34:20 - INFO - 访问登录页面: https://openi.pcl.ac.cn/user/login
10:34:22 - INFO - 输入用户名: 75271002@qq.com
```

### 查看日志的方法

#### 1. 实时查看控制台输出
```bash
# 程序运行时直接查看控制台
python3 login_getpoints.py --auto --headless
```

#### 2. 查看日志文件
```bash
# 查看最新日志
cat logs/openi_automation_20251105.log

# 实时跟踪日志（Linux/macOS）
tail -f logs/openi_automation_20251105.log

# 查看最后100行
tail -100 logs/openi_automation_20251105.log

# 搜索特定内容
grep "登录失败" logs/openi_automation_20251105.log
```

#### 3. 日志轮转说明

- **按日期自动轮转**：每天生成新的日志文件
- **文件名格式**：`openi_automation_YYYYMMDD.log`
- **长期保存**：日志文件不会自动删除，需要手动管理
- **手动清理**：
  ```bash
  # 删除7天前的日志
  find logs/ -name "openi_automation_*.log" -mtime +7 -delete

  # 手动清空当日日志
  > logs/openi_automation_$(date +%Y%m%d).log
  ```

### 日志级别说明

| 级别 | 控制台输出 | 文件输出 | 用途 |
|------|------------|----------|------|
| DEBUG | ❌ | ✅ | 详细的调试信息 |
| INFO | ✅ | ✅ | 一般操作信息 |
| WARNING | ✅ | ✅ | 警告信息 |
| ERROR | ✅ | ✅ | 错误信息 |
| CRITICAL | ✅ | ✅ | 严重错误 |

### 日志文件示例

**完整日志内容示例**：
```log
10:33:47 - INFO - ✓ 日志已保存到: /path/to/logs/openi_automation_20251105.log
10:34:19 - INFO - ============================================================
10:34:19 - INFO - 定时调度器已启动（随机间隔模式）
10:34:19 - INFO - ============================================================
10:34:19 - INFO - 下次执行时间：立即执行
10:34:19 - INFO - 启动时立即执行：是
10:34:19 - INFO - 随机间隔范围：5分钟 - 25小时
10:34:19 - INFO - ============================================================
10:34:19 - INFO -
⚠️ 程序将持续运行以执行定时任务
10:34:19 - INFO - 按 Ctrl+C 可以优雅退出
10:34:19 - INFO -
============================================================
10:34:19 - INFO - 开始执行任务 [20251105_103419]
10:34:19 - INFO - ============================================================
10:34:20 - INFO - 访问登录页面: https://openi.pcl.ac.cn/user/login
10:34:20 - INFO - 随机选择间隔：20分钟
10:34:22 - INFO - 输入用户名: 75271002@qq.com
10:34:22 - INFO - 输入密码
10:34:22 - INFO - 点击登录按钮
10:34:24 - INFO - ✓ 登录操作完成
10:34:24 - INFO - ✓ 弹框已完全消失
10:34:30 - INFO - ✓ 任务执行成功，下次执行时间：2025-11-05 10:54:30
```

## 🔄 更新日志

### v0.0.1 (2025-11-05) - 当前版本
- ✅ **新增任务关闭功能（步骤6）**
  - 所有批量任务完成后自动关闭 RUNNING 状态的任务
  - 智能定位"停止"按钮（基于首行状态相对定位）
  - 多策略容错机制确保关闭成功
  - 参考"再次调试"的成功定位经验
- ✅ **修复执行流程顺序问题**
  - 确保 RUNNING 状态的任务也会执行所有批量操作
  - 统一 STOPPED 和 RUNNING 状态的处理流程
  - 任务关闭移至所有批量操作完成后执行
  - 完整的 11 步执行流程保证
- ✅ **改进元素定位策略**
  - 基于首行状态的相对定位（推荐策略）
  - 多文本匹配（停止、关闭、Stop、Close）
  - JavaScript 强制点击作为最终回退
  - 详细的定位过程日志输出
- ✅ **完善文档和日志**
  - 更新 README 文档执行流程说明
  - 新增 stop_button_fail.png 失败截图类型
  - 详细的操作步骤说明和时间统计
  - 更正代码行号引用（适配最新代码结构）

### v2.2 (2025-11-05)
- ✅ **新增自动定时执行功能**
  - 支持每 24小时+10分钟自动执行一次
  - 支持配置文件启用/禁用自动模式
  - 支持启动时立即执行一次
  - **新增随机间隔执行模式**
    - 随机间隔选项：5分钟、8分钟、10分钟、20分钟、30分钟、1-5小时
    - 最大间隔不超过25小时
    - 每次执行后动态计算下次执行时间
- ✅ **新增命令行参数支持**
  - `--auto`：启用自动定时模式
  - `--once`：强制单次执行
  - `--headless`：无头浏览器模式
- ✅ **新增任务调度器**
  - 使用 APScheduler 实现异步调度
  - 避免并发执行（max_instances=1）
  - 支持错过执行合并（coalesce=True）
  - 5分钟容错时间
- ✅ **新增日志系统（重要更新）**
  - **双重日志输出**：控制台 + 文件
  - 控制台显示 INFO 级别（简洁，便于实时查看）
  - 文件记录 DEBUG 级别（详细，便于故障排查）
  - 按日期自动轮转日志文件
  - 日志文件位置：`logs/openi_automation_YYYYMMDD.log`
  - 支持日志实时跟踪和搜索
- ✅ **新增优雅退出机制**
  - 支持 Ctrl+C 优雅关闭调度器
  - 支持信号处理器（SIGINT, SIGTERM）
  - 等待当前任务完成后退出
- ✅ **改进日志输出**
  - 新增任务执行 ID 跟踪
  - 清晰的执行模式标识
  - 详细的调度器状态显示
  - 随机间隔计算日志提示
- ✅ **新增技术特性**
  - 异步调度器支持
  - 线程安全的事件循环
  - 改进的错误处理和异常捕获
  - 动态重新调度机制

### v2.1 (2025-11-04)
- ✅ 新增视频录制功能（两种方式）
- ✅ 新增独立录制脚本 playwright_luzhi.py
- ✅ 支持通过配置文件启用/禁用录制
- ✅ 自动保存 WebM 格式视频（1920x1080）
- ✅ 提供 ffmpeg 转换 MP4 说明

### v2.0 (2025-11-04)
- ✅ 重构代码，所有 URL 改为从配置文件读取
- ✅ 支持多账号配置管理
- ✅ 修复 CodeMirror 编辑器内容更新问题
- ✅ 简化按钮点击策略（XPath + JavaScript fallback）
- ✅ 添加详细的按钮状态日志输出
- ✅ 改进错误处理和失败截图保存

### v1.0
- ✅ 基础功能实现：登录、调试任务、Issue、代码提交、PR

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 免责声明

本项目仅用于学习与自动化实践目的，请遵守目标网站的使用条款与相关法律法规。

使用本工具造成的任何后果由使用者自行承担，作者不承担任何法律责任。

请合理使用自动化工具，避免对平台造成不必要的负担。

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至项目维护者

---

**Happy Coding! 🎉**
