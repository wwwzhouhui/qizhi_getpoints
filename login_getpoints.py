#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import configparser
import logging
import os
import random
import signal
import sys
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from playwright.async_api import async_playwright


class OpenIGetPoints:
    def __init__(self, config_file: str = "config_getpoints3.ini") -> None:
        self.config_file = config_file
        self.scheduler = None  # 存储调度器实例
        self.db_file = "user_records.db"  # SQLite数据库文件
        self._setup_logger()
        self._load_config()
        self._init_database()  # 初始化数据库

    def _setup_logger(self) -> None:
        """配置日志系统（同时输出到控制台和文件）"""
        # 创建logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

        # 清除现有的所有handler（避免重复）
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # 创建logs目录
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # 创建文件handler（记录所有日志到文件）
        today = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'openi_automation_{today}.log')

        # 使用 'a' 模式追加日志（如果文件不存在则创建）
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 创建console handler（控制台只显示INFO及以上级别）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 创建formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加handler（同时输出到文件和控制台）
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info(f"✓ 日志系统已初始化：{log_file}")

    def _load_config(self) -> None:
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在：{self.config_file}")
        cfg = configparser.ConfigParser()
        cfg.read(self.config_file, encoding="utf-8")

        self.login_url = cfg.get("login", "login_url")
        self.cloudbrains_url = cfg.get("login", "cloudbrains_url")
        self.username = cfg.get("login", "username")
        self.password = cfg.get("login", "password")

        self.username_xpath = cfg.get("xpath", "username_xpath")
        self.password_xpath = cfg.get("xpath", "password_xpath")
        self.login_button_xpath = cfg.get("xpath", "login_button_xpath")
        self.first_status_xpath = cfg.get("xpath", "first_status_xpath")
        self.debug_again_button_xpath = cfg.get("xpath", "debug_again_button_xpath")
        self.popup_close_button_xpath = cfg.get("xpath", "popup_close_button_xpath", fallback="")

        self.browser_timeout = cfg.getint("settings", "browser_timeout", fallback=120000)

        # 视频录制设置
        self.enable_video_recording = cfg.getboolean("settings", "enable_video_recording", fallback=False)
        self.video_output_dir = cfg.get("settings", "video_output_dir", fallback="./recordings")

        # Issues 页面配置（用于创建 Issue）
        self.issues_url = cfg.get("issues", "issues_url", fallback="https://openi.pcl.ac.cn/wwxiaohuihui/wwxiaohuidemo/issues")
        self.issues_create_button_xpath = cfg.get("issues", "issues_create_button_xpath", fallback="/html/body/div[2]/div[2]/div[2]/div[1]/div[3]/a")
        self.issues_new_title_input_xpath = cfg.get("issues", "issues_new_title_input_xpath", fallback="/html/body/div[2]/div[2]/div[2]/form/div[1]/div/div/div/div[1]/input")
        self.issues_submit_button_xpath = cfg.get("issues", "issues_submit_button_xpath", fallback="/html/body/div[2]/div[2]/div[2]/form/div[1]/div/div/div/div[5]/button")

        # Issue 评论配置
        self.issue_latest_link_xpath = cfg.get("issues", "issue_latest_link_xpath", fallback="/html/body/div[2]/div[2]/div[2]/div[5]/li[1]/a")
        self.issue_comment_textarea_xpath = cfg.get("issues", "issue_comment_textarea_xpath", fallback="/html/body/div[2]/div[2]/div[2]/div[3]/div[1]/div[2]/ui/div[2]/div/form/div[2]/div[1]/div[2]/div[6]")
        self.issue_comment_button_xpath = cfg.get("issues", "issue_comment_button_xpath", fallback="/html/body/div[2]/div[2]/div[2]/div[3]/div[1]/div[2]/ui/div[2]/div/form/div[4]/div/button")

        # 代码编辑配置
        self.code_edit_url = cfg.get("code", "code_edit_url", fallback="https://openi.pcl.ac.cn/wwxiaohuihui/wwxiaohuidemo/_edit/master/zz2.py")
        self.code_editor_xpath = cfg.get("code", "code_editor_xpath", fallback="/html/body/div[2]/div[2]/div[2]/form/div[2]/div[2]/div/div/div[1]/div[2]/div[1]/div[4]")
        # 代码提交按钮（创建提交）
        # 按需求更新为：/html/body/div[2]/div[2]/div[2]/div[3]/form/div[1]/div/div/div/div[5]/button
        self.code_commit_button_xpath = cfg.get(
            "code",
            "code_commit_button_xpath",
            fallback="/html/body/div[2]/div[2]/div[2]/div[3]/form/div[1]/div/div/div/div[5]/button",
        )

        # 分支合并配置
        self.branch_edit_url = cfg.get("branch", "branch_edit_url", fallback="https://openi.pcl.ac.cn/wwxiaohuihui/wwxiaohuidemo/_edit/master/zz.py")
        self.compare_base_url = cfg.get("branch", "compare_base_url", fallback="https://openi.pcl.ac.cn/wwxiaohuihui/wwxiaohuidemo/compare/master")

        # 定时执行配置
        self.auto_execute_enabled = cfg.getboolean("settings", "auto_execute_enabled", fallback=False)
        self.execute_interval = cfg.get("settings", "execute_interval", fallback="24:10")
        self.execute_on_startup = cfg.getboolean("settings", "execute_on_startup", fallback=True)

        # 关闭按钮XPath
        self.stop_button_xpath = "/html/body/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[1]/div[4]/div[2]/table/tbody/tr[1]/td[12]/div/div/div/div/a[2]"

    def _init_database(self) -> None:
        """初始化SQLite数据库和表"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # 创建表（如果不存在）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    runflag INTEGER NOT NULL,
                    createtime DATETIME NOT NULL,
                    isrun INTEGER NOT NULL,
                    updatetime DATETIME NOT NULL
                )
            ''')

            # 创建唯一索引，避免同一天同一用户重复记录
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_user_date
                ON user_records(username, DATE(createtime))
            ''')

            conn.commit()
            conn.close()
            self.logger.info(f"✓ 数据库已初始化: {self.db_file}")
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")

    def _save_run_state(self, username: str, runflag: int, createtime: str, isrun: int) -> None:
        """保存运行状态到数据库（检查重复：同一天同一用户只保存一条）"""
        try:
            import sqlite3
            from datetime import datetime

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # 获取当前时间作为 updatetime
            updatetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 检查今天是否已有该用户的记录
            cursor.execute('''
                SELECT id FROM user_records
                WHERE username = ? AND DATE(createtime) = DATE(?)
            ''', (username, createtime))

            existing_record = cursor.fetchone()

            if existing_record:
                # 更新现有记录
                record_id = existing_record[0]
                cursor.execute('''
                    UPDATE user_records
                    SET runflag = ?, isrun = ?, updatetime = ?
                    WHERE id = ?
                ''', (runflag, isrun, updatetime, record_id))
                self.logger.info(f"✓ 更新运行状态（避免重复）: ID={record_id}, username={username}, updatetime={updatetime}")
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO user_records (username, runflag, createtime, isrun, updatetime)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, runflag, createtime, isrun, updatetime))
                record_id = cursor.lastrowid
                self.logger.info(f"✓ 插入新运行状态: ID={record_id}, username={username}, runflag={runflag}, createtime={createtime}, isrun={isrun}, updatetime={updatetime}")

            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"保存运行状态到数据库失败: {e}")

    def _query_user_records(self, username: str, limit: int = 10) -> list:
        """查询用户记录"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, username, runflag, createtime, isrun, updatetime
                FROM user_records
                WHERE username = ?
                ORDER BY createtime DESC
                LIMIT ?
            ''', (username, limit))

            records = cursor.fetchall()
            conn.close()
            return records
        except Exception as e:
            self.logger.error(f"查询用户记录失败: {e}")
            return []

    def _check_today_run(self, username: str) -> bool:
        """检查今天是否已有运行记录"""
        try:
            import sqlite3
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*) FROM user_records
                WHERE username = ? AND DATE(createtime) = ?
            ''', (username, today))

            count = cursor.fetchone()[0]
            conn.close()

            return count > 0
        except Exception as e:
            self.logger.error(f"检查今日运行记录失败: {e}")
            return False

    async def _click_stop_button(self, page) -> bool:
        """点击关闭按钮（参考'再次调试'的定位方法）"""
        self.logger.info("\n开始执行关闭任务操作...")

        # 首先访问调试列表页，确保在正确的页面上
        try:
            self.logger.info("访问调试列表页...")
            await self._goto_debugjob(page)
            await asyncio.sleep(2)
        except Exception as e:
            self.logger.error(f"访问调试列表页失败: {e}")
            return False

        # 策略0: 基于首行状态的相对定位（参考'再次调试'的方法）
        self.logger.info("策略0: 基于首行状态进行相对定位（推荐）...")
        try:
            # 定位首行状态单元格
            self.logger.debug(f"首行状态 XPath: {self.first_status_xpath}")
            st_node = page.locator(f"xpath={self.first_status_xpath}").first

            # 获取状态所在的行
            row = st_node.locator("xpath=ancestor::tr[1]")

            # 在行内查找包含"停止"、"关闭"等文本的链接
            stop_texts = ['停止', '关闭', 'Stop', 'Close']

            for text in stop_texts:
                try:
                    self.logger.debug(f"  尝试查找文本：{text}")
                    rel = row.locator(f"a:has-text('{text}')")
                    rel_cnt = await rel.count()
                    self.logger.debug(f"  行内'{text}'数量：{rel_cnt}")

                    if rel_cnt > 0:
                        try:
                            await rel.first.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                        except Exception:
                            pass

                        try:
                            await rel.first.click()
                            self.logger.info(f"✓ 策略0成功：通过文本'{text}'点击关闭按钮")
                            await asyncio.sleep(2)
                            return True
                        except Exception as e1:
                            self.logger.debug(f"  直接点击失败：{e1}，尝试 evaluate...")
                            try:
                                await rel.first.evaluate("el => el.click()")
                                self.logger.info(f"✓ 策略0成功：通过 evaluate 点击'{text}'")
                                await asyncio.sleep(2)
                                return True
                            except Exception as e2:
                                self.logger.debug(f"  evaluate 点击失败：{e2}")
                except Exception as e:
                    self.logger.debug(f"  查找文本'{text}'异常：{e}")
                    continue

            # 如果文本定位失败，尝试定位行内最后一个链接（通常是操作按钮）
            self.logger.debug("  尝试定位行内最后一个链接...")
            try:
                # 获取行内第12列（操作列，参考图片）
                cell = row.locator("xpath=td[12]")
                cell_cnt = await cell.count()
                self.logger.debug(f"  第12列单元格数量：{cell_cnt}")

                if cell_cnt > 0:
                    # 查找单元格内的所有链接
                    links = cell.locator("a")
                    links_cnt = await links.count()
                    self.logger.debug(f"  第12列内链接数量：{links_cnt}")

                    if links_cnt > 0:
                        # 尝试点击最后一个链接（通常是"停止"按钮）
                        last_link = links.last
                        try:
                            await last_link.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                        except Exception:
                            pass

                        try:
                            await last_link.click()
                            self.logger.info("✓ 策略0成功：点击第12列最后一个链接")
                            await asyncio.sleep(2)
                            return True
                        except Exception as e1:
                            self.logger.debug(f"  直接点击失败：{e1}，尝试 evaluate...")
                            try:
                                await last_link.evaluate("el => el.click()")
                                self.logger.info("✓ 策略0成功：通过 evaluate 点击最后链接")
                                await asyncio.sleep(2)
                                return True
                            except Exception as e2:
                                self.logger.debug(f"  evaluate 点击失败：{e2}")

                    # 输出第12列的 HTML 以便调试
                    try:
                        html = await cell.first.evaluate("el => el.outerHTML")
                        self.logger.debug(f"  第12列HTML：{html[:300]}")
                    except Exception:
                        pass
            except Exception as e:
                self.logger.debug(f"  定位第12列失败：{e}")

            self.logger.warning("❌ 策略0失败")
        except Exception as e:
            self.logger.error(f"❌ 策略0异常: {e}")

        # 策略1: 尝试基于文本的定位（全局搜索）
        try:
            self.logger.info("策略1: 尝试基于文本定位（全局）...")
            text_selectors = [
                "a:has-text('停止')",
                "a:has-text('关闭')",
                "a:has-text('Stop')",
                "a:has-text('Close')",
                "button:has-text('停止')",
                "button:has-text('关闭')",
            ]

            for selector in text_selectors:
                try:
                    self.logger.debug(f"  尝试选择器: {selector}")
                    elements = page.locator(selector)
                    elem_count = await elements.count()

                    if elem_count > 0:
                        self.logger.debug(f"  找到 {elem_count} 个元素")
                        element = elements.first

                        try:
                            await element.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                        except Exception:
                            pass

                        try:
                            await element.click(timeout=5000)
                            self.logger.info(f"✓ 策略1成功: {selector}")
                            await asyncio.sleep(2)
                            return True
                        except Exception as e:
                            self.logger.debug(f"  点击失败：{e}")
                            continue
                except Exception as e:
                    self.logger.debug(f"  选择器异常 {selector}: {e}")
                    continue

            self.logger.warning("❌ 策略1失败")
        except Exception as e:
            self.logger.error(f"❌ 策略1异常: {e}")

        # 策略2: JavaScript 基于表格行定位
        try:
            self.logger.info("策略2: JavaScript 基于表格行定位...")
            result = await page.evaluate("""
                () => {
                    // 查找表格第一行
                    const table = document.querySelector('table');
                    if (table) {
                        const firstRow = table.querySelector('tbody tr');
                        if (firstRow) {
                            // 查找行内所有链接
                            const links = firstRow.querySelectorAll('a');

                            // 优先查找包含"停止"、"关闭"文本的链接
                            for (let link of links) {
                                const text = link.textContent.trim();
                                if (text.includes('停止') || text.includes('关闭') ||
                                    text.includes('Stop') || text.includes('Close')) {
                                    link.click();
                                    return { success: true, text: text };
                                }
                            }

                            // 如果没找到，尝试点击最后一个链接
                            if (links.length > 0) {
                                const lastLink = links[links.length - 1];
                                lastLink.click();
                                return { success: true, text: lastLink.textContent };
                            }
                        }
                    }
                    return { success: false };
                }
            """)

            if result.get('success'):
                self.logger.info(f"✓ 策略2成功，点击了: {result.get('text')}")
                await asyncio.sleep(2)
                return True

            self.logger.warning("❌ 策略2失败")
        except Exception as e:
            self.logger.error(f"❌ 策略2异常: {e}")

        # 策略3: JavaScript 查找第12列操作按钮
        try:
            self.logger.info("策略3: JavaScript 查找第12列操作按钮...")
            result = await page.evaluate("""
                () => {
                    const table = document.querySelector('table');
                    if (table) {
                        const firstRow = table.querySelector('tbody tr');
                        if (firstRow) {
                            // 获取所有单元格
                            const cells = firstRow.querySelectorAll('td');
                            // 第12列（索引11）
                            if (cells.length >= 12) {
                                const opCell = cells[11];
                                const links = opCell.querySelectorAll('a');

                                // 查找"停止"按钮
                                for (let link of links) {
                                    const text = link.textContent.trim();
                                    if (text.includes('停止') || text.includes('关闭') ||
                                        text.includes('Stop') || text.includes('Close')) {
                                        link.click();
                                        return { success: true, text: text, column: 12 };
                                    }
                                }

                                // 尝试点击最后一个链接
                                if (links.length > 0) {
                                    links[links.length - 1].click();
                                    return { success: true, text: links[links.length - 1].textContent, column: 12 };
                                }
                            }
                        }
                    }
                    return { success: false };
                }
            """)

            if result.get('success'):
                self.logger.info(f"✓ 策略3成功，点击了第{result.get('column')}列: {result.get('text')}")
                await asyncio.sleep(2)
                return True

            self.logger.warning("❌ 策略3失败")
        except Exception as e:
            self.logger.error(f"❌ 策略3异常: {e}")

        # 所有策略失败，保存截图
        self.logger.error("❌ 所有策略都失败，无法点击关闭按钮")
        try:
            await page.screenshot(path="stop_button_fail.png", full_page=True)
            self.logger.error("已保存失败截图：stop_button_fail.png")
        except Exception:
            pass

        return False

    async def _check_initial_status_and_save(self, page) -> bool:
        """检查初始状态，如果是RUNNING则保存状态并跳过启动"""
        try:
            # 访问调试列表页
            await self._goto_debugjob(page)

            # 检查状态
            status = await self._get_first_status(page)
            self.logger.info(f"当前任务状态: {status}")

            if status == "RUNNING":
                # 状态已经是RUNNING，保存状态
                today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save_run_state(
                    username=self.username,
                    runflag=1,
                    createtime=today,
                    isrun=1
                )
                self.logger.info("✓ 检测到任务已运行，跳过启动步骤")
                return True
            else:
                # 状态不是RUNNING，需要启动
                self.logger.info("检测到任务未运行，将触发启动...")
                return False
        except Exception as e:
            self.logger.error(f"检查初始状态失败: {e}")
            return False

    async def _login(self, page) -> bool:
        """执行登录操作"""
        try:
            self.logger.info(f"\n访问登录页面: {self.login_url}")
            await page.goto(self.login_url, timeout=self.browser_timeout)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(1)

            self.logger.info(f"输入用户名: {self.username}")
            await page.fill(f"xpath={self.username_xpath}", self.username)

            self.logger.info("输入密码")
            await page.fill(f"xpath={self.password_xpath}", self.password)

            self.logger.info("点击登录按钮")
            await page.click(f"xpath={self.login_button_xpath}")

            self.logger.info("等待页面加载...")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # 等待2秒，确保弹窗出现

            self.logger.info("✓ 登录操作完成")

            # 登录后处理弹框
            self.logger.info("\n检查是否有公告弹框...")
            await self._handle_announcement_popup(page)

            return True

        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _handle_announcement_popup(self, page) -> bool:
        """
        处理44.png显示的公告弹框：
        1. 勾选"不再提醒"复选框
        2. 等待倒计时（如果有）
        3. 点击绿色"关闭"按钮

        返回: 是否成功处理弹框
        """
        try:
            self.logger.info("\n" + "="*60)
            self.logger.info("开始处理公告弹框")
            self.logger.info("="*60)

            # 等待弹框出现
            await asyncio.sleep(2)

            # 步骤1: 查找并勾选"不再提醒"复选框
            self.logger.info("步骤1: 查找并勾选'不再提醒'复选框...")
            checkbox_checked = False

            # 策略1: 通过文本定位label并点击
            try:
                checkbox_labels = [
                    "label:has-text('不再提醒')",
                    "label:has-text('不再提示')",
                    "label:has-text('不再显示')",
                ]

                for label_selector in checkbox_labels:
                    label = page.locator(label_selector)
                    if await label.count() > 0:
                        self.logger.debug(f"找到复选框标签: {label_selector}")
                        await label.first.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        await label.first.click()
                        self.logger.info("✓ 已通过label点击勾选复选框")
                        checkbox_checked = True
                        break
            except Exception as e:
                self.logger.error(f"策略1失败: {e}")

            # 策略2: 直接查找checkbox input
            if not checkbox_checked:
                try:
                    checkbox_selectors = [
                        "input[type='checkbox'][name='notRemindAgain']",
                        "input[type='checkbox']",
                        ".ui.checkbox input",
                    ]

                    for selector in checkbox_selectors:
                        checkbox = page.locator(selector)
                        if await checkbox.count() > 0:
                            self.logger.debug(f"找到复选框: {selector}")
                            # 确保复选框被勾选
                            if not await checkbox.first.is_checked():
                                await checkbox.first.check(force=True)
                                self.logger.info("✓ 已直接勾选复选框")
                                checkbox_checked = True
                                break
                except Exception as e:
                    self.logger.error(f"策略2失败: {e}")

            # 策略3: 使用JavaScript强制勾选
            if not checkbox_checked:
                try:
                    await page.evaluate("""
                        () => {
                            // 查找所有checkbox
                            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
                            checkboxes.forEach(cb => {
                                cb.checked = true;
                                cb.dispatchEvent(new Event('change', { bubbles: true }));
                            });
                        }
                    """)
                    self.logger.info("✓ 已通过JavaScript强制勾选")
                    checkbox_checked = True
                except Exception as e:
                    self.logger.error(f"策略3失败: {e}")

            if checkbox_checked:
                self.logger.info("✓ 复选框勾选成功")
                await asyncio.sleep(0.5)
            else:
                self.logger.error("⚠️ 复选框勾选失败，继续尝试关闭按钮")

            # 步骤2: 检测并等待倒计时
            self.logger.info("\n步骤2: 检测倒计时...")
            countdown = None

            try:
                # 查找倒计时元素
                countdown_selectors = [
                    "span.count-down",
                    ".count-down",
                    "button span",
                ]

                for selector in countdown_selectors:
                    cd_elem = page.locator(selector)
                    if await cd_elem.count() > 0:
                        cd_text = await cd_elem.first.text_content()
                        if cd_text and cd_text.strip().isdigit():
                            countdown = int(cd_text.strip())
                            self.logger.debug(f"发现倒计时: {countdown}秒")
                            break
            except Exception as e:
                self.logger.error(f"检测倒计时失败: {e}")

            # 等待倒计时
            if countdown and countdown > 0:
                self.logger.debug(f"等待倒计时 {countdown} 秒...")
                for i in range(countdown):
                    remaining = countdown - i
                    self.logger.info(f"  剩余: {remaining}秒")
                    await asyncio.sleep(1)
            else:
                self.logger.info("未检测到倒计时，等待1秒后继续")
                await asyncio.sleep(1)

            # 步骤3: 点击"关闭"按钮
            self.logger.info("\n步骤3: 查找并点击'关闭'按钮...")
            close_clicked = False

            # 策略1: 通过文本查找按钮
            try:
                close_button_selectors = [
                    "button:has-text('关闭')",
                    "div.ui.positive.button:has-text('关闭')",
                    ".ui.button:has-text('关闭')",
                    "button:has-text('Close')",
                ]

                for selector in close_button_selectors:
                    btn = page.locator(selector)
                    if await btn.count() > 0:
                        self.logger.debug(f"找到关闭按钮: {selector}")
                        await btn.first.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        await btn.first.click()
                        self.logger.info("✓ 已点击关闭按钮")
                        close_clicked = True
                        break
            except Exception as e:
                self.logger.error(f"策略1失败: {e}")

            # 策略2: 通过CSS类查找绿色按钮
            if not close_clicked:
                try:
                    green_button_selectors = [
                        ".ui.positive.button",
                        ".ui.green.button",
                        "button.positive",
                    ]

                    for selector in green_button_selectors:
                        btn = page.locator(selector)
                        if await btn.count() > 0:
                            self.logger.debug(f"找到绿色按钮: {selector}")
                            await btn.first.click()
                            self.logger.info("✓ 已点击绿色按钮")
                            close_clicked = True
                            break
                except Exception as e:
                    self.logger.error(f"策略2失败: {e}")

            # 策略3: 使用JavaScript点击
            if not close_clicked:
                try:
                    await page.evaluate("""
                        () => {
                            // 查找包含"关闭"文本的按钮
                            const buttons = Array.from(document.querySelectorAll('button, .button'));
                            const closeBtn = buttons.find(btn =>
                                btn.textContent.includes('关闭') ||
                                btn.textContent.includes('Close')
                            );
                            if (closeBtn) {
                                closeBtn.click();
                            }
                        }
                    """)
                    self.logger.info("✓ 已通过JavaScript点击关闭按钮")
                    close_clicked = True
                except Exception as e:
                    self.logger.error(f"策略3失败: {e}")

            if close_clicked:
                self.logger.info("✓ 关闭按钮点击成功")
                await asyncio.sleep(1)

                # 等待弹框消失
                self.logger.info("等待弹框消失...")
                try:
                    # 检查弹框是否消失
                    modal_selectors = [
                        ".ui.dimmer.modals.page.visible.active",
                        ".ui.modal.visible.active",
                        ".modal.visible",
                    ]

                    for _ in range(10):
                        modal_exists = False
                        for selector in modal_selectors:
                            if await page.locator(selector).count() > 0:
                                modal_exists = True
                                break

                        if not modal_exists:
                            self.logger.info("✓ 弹框已完全消失")
                            break

                        await asyncio.sleep(0.5)
                except Exception:
                    pass
            else:
                self.logger.error("✗ 关闭按钮点击失败")

            self.logger.info("\n" + "="*60)
            self.logger.info("弹框处理完成")
            self.logger.info("="*60 + "\n")

            return close_clicked

        except Exception as e:
            self.logger.error(f"处理弹框时发生异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _goto_debugjob(self, page) -> None:
        self.logger.info(f"访问调试列表页：{self.cloudbrains_url}")
        await page.goto(self.cloudbrains_url, timeout=self.browser_timeout)
        await page.wait_for_load_state("domcontentloaded")
        try:
            title = await page.title()
            self.logger.info(f"页面标题：{title}")
        except Exception:
            pass
        try:
            await page.reload(wait_until="domcontentloaded")
        except Exception:
            pass
        await asyncio.sleep(1)

    async def _get_first_status(self, page) -> str:
        try:
            self.logger.info(f"读取首行状态，XPath：{self.first_status_xpath}")
            await page.wait_for_selector(f"xpath={self.first_status_xpath}", timeout=10000)
            loc = page.locator(f"xpath={self.first_status_xpath}").first
            txt = await loc.text_content()
            status = (txt or "").strip().upper()
            self.logger.info(f"当前第一条记录状态：{status}")
            return status
        except Exception as e:
            self.logger.error(f"读取第一条状态失败：{e}")
            return ""

    async def _click_debug_again(self, page) -> bool:
        self.logger.info(f"尝试点击'再次调试'，XPath：{self.debug_again_button_xpath}")
        try:
            selector = f"xpath={self.debug_again_button_xpath}"
            await page.wait_for_selector(selector, timeout=self.browser_timeout, state="visible")
            loc = page.locator(selector)
            cnt = await loc.count()
            self.logger.debug(f"‘再次调试’定位数量：{cnt}")
            if cnt == 0:
                self.logger.debug("未找到‘再次调试’主定位，尝试文本定位...")
            text_loc = page.locator("a:has-text('再次调试')")
            text_cnt = await text_loc.count()
            if cnt == 0:
                self.logger.debug(f"文本定位到‘再次调试’数量：{text_cnt}")
            node = loc.first if cnt > 0 else text_loc.first
            try:
                await node.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                await node.click()
                self.logger.info("已点击‘再次调试’按钮")
                return True
            except Exception as e:
                self.logger.error(f"直接点击失败：{e}，尝试 evaluate 点击...")
                try:
                    await node.evaluate("el => el.click()")
                    self.logger.info("通过 evaluate 点击成功")
                    return True
                except Exception as e2:
                    self.logger.error(f"evaluate 点击仍失败：{e2}")
                    # 回退：基于状态行相对定位尝试
                    try:
                        self.logger.debug("尝试基于首行状态所在行进行相对定位...")
                        st_node = page.locator(f"xpath={self.first_status_xpath}").first
                        row = st_node.locator("xpath=ancestor::tr[1]")
                        rel = row.locator("a:has-text('再次调试')")
                        rel_cnt = await rel.count()
                        self.logger.debug(f"行内‘再次调试’数量：{rel_cnt}")
                        if rel_cnt > 0:
                            try:
                                await rel.first.scroll_into_view_if_needed()
                            except Exception:
                                pass
                            try:
                                await rel.first.click()
                                self.logger.debug("行内定位点击成功")
                                return True
                            except Exception as e3:
                                self.logger.error(f"行内定位直接点击失败：{e3}，尝试 evaluate...")
                                try:
                                    await rel.first.evaluate("el => el.click()")
                                    self.logger.info("行内 evaluate 点击成功")
                                    return True
                                except Exception as e4:
                                    self.logger.error(f"行内 evaluate 失败：{e4}")
                        # 输出行内第11列的 outerHTML 以便排查
                        try:
                            cell = row.locator("xpath=td[11]")
                            cell_cnt = await cell.count()
                            self.logger.debug(f"行内第11列单元格数量：{cell_cnt}")
                            if cell_cnt > 0:
                                html = await cell.first.evaluate("el => el.outerHTML")
                                self.logger.info(f"第11列单元格HTML：{html[:500]}")
                        except Exception:
                            pass
                    except Exception as e_rel:
                        self.logger.error(f"相对定位尝试异常：{e_rel}")
                    # 截图以便定位
                    try:
                        await page.screenshot(path="debug_again_click_fail.png", full_page=True)
                        self.logger.error("已保存截图：debug_again_click_fail.png")
                    except Exception:
                        pass
                    return False
        except Exception as e:
            self.logger.error(f"点击‘再次调试’失败：{e}")
            try:
                await page.screenshot(path="debug_again_click_fail.png", full_page=True)
                self.logger.error("已保存截图：debug_again_click_fail.png")
            except Exception:
                pass
            return False

    async def _wait_for_status(self, page, target_status: str, timeout_sec: int = 600, interval_sec: int = 10) -> bool:
        deadline = asyncio.get_event_loop().time() + max(1, timeout_sec)
        while asyncio.get_event_loop().time() < deadline:
            st = await self._get_first_status(page)
            if st == (target_status or "").upper():
                return True
            await asyncio.sleep(max(1, interval_sec))
            try:
                await page.reload(wait_until="domcontentloaded")
            except Exception:
                pass
        return False

    async def _create_and_comment_on_issue(self, page, index: int, title: str = None) -> bool:
        """创建一个 Issue 并在创建成功后立即评论"""
        try:
            # 如果没有指定标题，则生成随机标题
            if title is None:
                title = self._generate_random_title()

            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"开始第 {index} 个任务：创建 Issue + 评论")
            self.logger.info(f"{'='*60}")

            # 进入 Issues 列表页
            self.logger.info(f"[{index}/3] 访问 Issues 列表页：{self.issues_url}")
            await page.goto(self.issues_url, timeout=self.browser_timeout)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(1)

            # 点击"创建"按钮
            create_sel = f"xpath={self.issues_create_button_xpath}"
            self.logger.info(f"[{index}/3] 点击创建按钮...")
            await page.wait_for_selector(create_sel, timeout=self.browser_timeout, state="visible")
            async with page.expect_navigation():
                await page.click(create_sel)
            await asyncio.sleep(1)
            self.logger.info(f"[{index}/3] 进入创建页面：{page.url}")

            # 填写标题
            title_sel = f"xpath={self.issues_new_title_input_xpath}"
            self.logger.info(f"[{index}/3] 填写标题：{title}")
            await page.wait_for_selector(title_sel, timeout=self.browser_timeout, state="visible")
            await page.fill(title_sel, title)

            # 点击提交按钮，创建 Issue
            submit_sel = f"xpath={self.issues_submit_button_xpath}"
            self.logger.info(f"[{index}/3] 提交创建 Issue...")
            await page.wait_for_selector(submit_sel, timeout=self.browser_timeout, state="visible")
            try:
                async with page.expect_navigation():
                    await page.click(submit_sel)
                self.logger.info(f"[{index}/3] Issue 创建成功！")
            except Exception as e:
                self.logger.error(f"[{index}/3] 提交点击异常：{e}，尝试 evaluate 点击...")
                try:
                    await page.locator(submit_sel).first.evaluate("el => el.click()")
                    await asyncio.sleep(2)
                    self.logger.info(f"[{index}/3] evaluate 提交成功")
                except Exception as e2:
                    self.logger.error(f"[{index}/3] 提交失败：{e2}")
                    try:
                        await page.screenshot(path=f"issue_create_fail_{index}.png", full_page=True)
                        self.logger.error(f"已保存失败截图：issue_create_fail_{index}.png")
                    except Exception:
                        pass
                    return False

            # 等待页面加载完成（此时应该在 Issue 详情页）
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            current_url = page.url
            self.logger.info(f"[{index}/3] 当前页面：{current_url}")
            self.logger.info(f"[{index}/3] Issue 创建完成，开始在当前页面添加评论...")

            # 滚动到页面底部，确保评论区可见
            self.logger.info(f"[{index}/3] 滚动到页面底部...")
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"[{index}/3] 滚动失败：{e}")

            # 生成随机评论内容
            comment_text = self._generate_random_comment()
            self.logger.info(f"[{index}/3] 生成评论内容：{comment_text}")

            # 定位评论区并填写内容（使用多种策略）
            comment_filled = False

            # 策略0：优先尝试配置的 XPath（最精确）
            self.logger.info(f"[{index}/3] 策略0：尝试配置的 XPath...")
            try:
                comment_textarea_sel = f"xpath={self.issue_comment_textarea_xpath}"
                self.logger.debug(f"[{index}/3] XPath: {self.issue_comment_textarea_xpath}")
                elem = page.locator(comment_textarea_sel)
                elem_count = await elem.count()
                self.logger.debug(f"[{index}/3] 找到 {elem_count} 个元素")

                if elem_count > 0:
                    target = elem.first
                    # 尝试多种输入方式

                    # 方式1：fill 方法
                    try:
                        await target.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await target.click()
                        await asyncio.sleep(0.5)
                        await target.fill("")
                        await target.fill(comment_text)
                        self.logger.info(f"[{index}/3] ✓ 配置 XPath 填写成功（fill）")
                        comment_filled = True
                    except Exception as e1:
                        self.logger.error(f"[{index}/3] fill 方法失败：{e1}")

                    # 方式2：type 方法（键盘输入）
                    if not comment_filled:
                        try:
                            await target.click()
                            await asyncio.sleep(0.3)
                            await page.keyboard.press("Control+A")
                            await page.keyboard.press("Backspace")
                            await page.keyboard.type(comment_text, delay=30)
                            self.logger.info(f"[{index}/3] ✓ 配置 XPath 填写成功（type）")
                            comment_filled = True
                        except Exception as e2:
                            self.logger.error(f"[{index}/3] type 方法失败：{e2}")

                    # 方式3：JavaScript 直接设值
                    if not comment_filled:
                        try:
                            # 使用 JavaScript 设置值，避免引号问题
                            await target.evaluate(
                                "(el, text) => { el.value = text; el.dispatchEvent(new Event('input', { bubbles: true })); }",
                                comment_text
                            )
                            self.logger.info(f"[{index}/3] ✓ 配置 XPath 填写成功（JavaScript）")
                            comment_filled = True
                        except Exception as e3:
                            self.logger.error(f"[{index}/3] JavaScript 方法失败：{e3}")
            except Exception as e:
                self.logger.error(f"[{index}/3] 策略0失败：{e}")

            # 策略1：尝试查找 textarea（最常见的评论输入框）
            if not comment_filled:
                self.logger.info(f"[{index}/3] 策略1：查找 textarea 元素...")
                try:
                    textareas = page.locator("textarea")
                    textarea_count = await textareas.count()
                    self.logger.debug(f"[{index}/3] 找到 {textarea_count} 个 textarea")

                    if textarea_count > 0:
                        target_textarea = textareas.last
                        await target_textarea.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await target_textarea.click()
                        await asyncio.sleep(0.5)
                        await target_textarea.fill("")
                        await target_textarea.fill(comment_text)
                        self.logger.info(f"[{index}/3] ✓ textarea 填写成功")
                        comment_filled = True
                except Exception as e:
                    self.logger.error(f"[{index}/3] 策略1失败：{e}")

            # 策略2：查找可编辑的 div
            if not comment_filled:
                self.logger.info(f"[{index}/3] 策略2：查找可编辑 div...")
                try:
                    editable_divs = page.locator("div[contenteditable='true']")
                    div_count = await editable_divs.count()
                    self.logger.debug(f"[{index}/3] 找到 {div_count} 个可编辑 div")

                    if div_count > 0:
                        target_div = editable_divs.last
                        await target_div.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await target_div.click()
                        await asyncio.sleep(0.5)
                        await target_div.fill("")
                        await target_div.fill(comment_text)
                        self.logger.info(f"[{index}/3] ✓ 可编辑 div 填写成功")
                        comment_filled = True
                except Exception as e:
                    self.logger.error(f"[{index}/3] 策略2失败：{e}")

            # 策略3：使用表单选择器
            if not comment_filled:
                self.logger.info(f"[{index}/3] 策略3：查找表单 textarea...")
                try:
                    form_selectors = [
                        "form textarea",
                        ".comment-form textarea",
                        "[class*='comment'] textarea",
                    ]

                    for selector in form_selectors:
                        elem = page.locator(selector)
                        if await elem.count() > 0:
                            self.logger.debug(f"[{index}/3] 找到：{selector}")
                            target = elem.last
                            await target.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            await target.click()
                            await asyncio.sleep(0.5)
                            await target.fill("")
                            await target.fill(comment_text)
                            self.logger.info(f"[{index}/3] ✓ {selector} 填写成功")
                            comment_filled = True
                            break
                except Exception as e:
                    self.logger.error(f"[{index}/3] 策略3失败：{e}")

            if not comment_filled:
                self.logger.error(f"[{index}/3] ✗ 所有策略填写评论都失败")
                try:
                    await page.screenshot(path=f"comment_fill_fail_{index}.png", full_page=True)
                    self.logger.error(f"已保存截图：comment_fill_fail_{index}.png")
                except Exception:
                    pass
                return False

            await asyncio.sleep(1)

            # 点击评论按钮提交
            self.logger.info(f"[{index}/3] 查找并点击评论按钮...")
            comment_submitted = False

            # 策略0：优先尝试配置的 XPath（最精确）
            self.logger.info(f"[{index}/3] 策略0：尝试配置的评论按钮 XPath...")
            try:
                comment_button_sel = f"xpath={self.issue_comment_button_xpath}"
                self.logger.debug(f"[{index}/3] XPath: {self.issue_comment_button_xpath}")
                btn = page.locator(comment_button_sel)
                btn_count = await btn.count()
                self.logger.debug(f"[{index}/3] 找到 {btn_count} 个按钮")

                if btn_count > 0:
                    target_btn = btn.first
                    # 尝试多种点击方式

                    # 方式1：直接 click
                    try:
                        await target_btn.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await target_btn.click()
                        self.logger.info(f"[{index}/3] ✓ 配置 XPath 点击成功（click）")
                        comment_submitted = True
                        await asyncio.sleep(2)
                    except Exception as e1:
                        self.logger.error(f"[{index}/3] click 失败：{e1}")

                    # 方式2：evaluate 点击
                    if not comment_submitted:
                        try:
                            await target_btn.evaluate("el => el.click()")
                            self.logger.info(f"[{index}/3] ✓ 配置 XPath 点击成功（evaluate）")
                            comment_submitted = True
                            await asyncio.sleep(2)
                        except Exception as e2:
                            self.logger.error(f"[{index}/3] evaluate 失败：{e2}")

                    # 方式3：dispatch click 事件
                    if not comment_submitted:
                        try:
                            await target_btn.evaluate("el => el.dispatchEvent(new MouseEvent('click', { bubbles: true }))")
                            self.logger.info(f"[{index}/3] ✓ 配置 XPath 点击成功（dispatchEvent）")
                            comment_submitted = True
                            await asyncio.sleep(2)
                        except Exception as e3:
                            self.logger.error(f"[{index}/3] dispatchEvent 失败：{e3}")
            except Exception as e:
                self.logger.error(f"[{index}/3] 策略0失败：{e}")

            # 策略1：查找包含"评论"文本的按钮
            if not comment_submitted:
                self.logger.info(f"[{index}/3] 策略1：查找包含'评论'文本的按钮...")
                try:
                    comment_buttons = page.locator("button:has-text('评论')")
                    btn_count = await comment_buttons.count()
                    self.logger.debug(f"[{index}/3] 找到 {btn_count} 个包含'评论'的按钮")

                    if btn_count > 0:
                        target_btn = comment_buttons.last
                        await target_btn.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await target_btn.click()
                        self.logger.info(f"[{index}/3] ✓ 评论提交成功")
                        comment_submitted = True
                        await asyncio.sleep(2)
                except Exception as e:
                    self.logger.error(f"[{index}/3] 策略1失败：{e}")

            # 策略2：查找提交按钮
            if not comment_submitted:
                self.logger.info(f"[{index}/3] 策略2：查找提交按钮...")
                try:
                    submit_selectors = [
                        "button[type='submit']",
                        "form button[type='submit']",
                        "button.ui.primary.button",
                    ]

                    for selector in submit_selectors:
                        buttons = page.locator(selector)
                        if await buttons.count() > 0:
                            self.logger.debug(f"[{index}/3] 找到：{selector}")
                            target_btn = buttons.last
                            await target_btn.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            await target_btn.click()
                            self.logger.info(f"[{index}/3] ✓ {selector} 点击成功")
                            comment_submitted = True
                            await asyncio.sleep(2)
                            break
                except Exception as e:
                    self.logger.error(f"[{index}/3] 策略2失败：{e}")

            if not comment_submitted:
                self.logger.error(f"[{index}/3] ✗ 评论按钮点击失败")
                try:
                    await page.screenshot(path=f"comment_submit_fail_{index}.png", full_page=True)
                    self.logger.error(f"已保存截图：comment_submit_fail_{index}.png")
                except Exception:
                    pass
                return False

            self.logger.info(f"[{index}/3] ✓✓✓ 第 {index} 个任务完成（创建 + 评论）✓✓✓\n")
            return True

        except Exception as e:
            self.logger.error(f"[{index}/3] 任务失败：{e}")
            try:
                await page.screenshot(path=f"task_fail_{index}.png", full_page=True)
                self.logger.error(f"已保存失败截图：task_fail_{index}.png")
            except Exception:
                pass
            return False

    async def _create_and_comment_batch(self, page, times: int = 3) -> bool:
        """批量创建 Issue 并评论（每次创建后立即评论）"""
        success_count = 0
        for i in range(1, times + 1):
            # 每次都生成随机标题
            result = await self._create_and_comment_on_issue(page, i, title=None)
            if result:
                success_count += 1
            await asyncio.sleep(2)

        self.logger.info(f"\n{'='*60}")
        self.logger.debug(f"批量任务完成：成功 {success_count}/{times}")
        self.logger.info(f"{'='*60}\n")
        return success_count == times

    def _generate_random_comment(self) -> str:
        """生成随机评论内容"""
        comments = [
            "这个问题确实需要优先处理，建议尽快修复。",
            "我也遇到了类似的情况，希望能得到重视。",
            "感谢反馈，我们会在下个版本中解决这个BUG。",
            "已经验证了这个问题，确认存在，正在修复中。",
            "好的，我会马上处理这个问题。",
            "这是一个重要的问题，需要团队讨论解决方案。",
            "已经提交修复代码，请测试验证。",
            "问题已复现，正在分析根本原因。",
            "谢谢提醒，这个BUG确实影响使用体验。",
            "收到，我会跟进这个问题的解决进度。",
            "已添加到待办列表，预计本周内解决。",
            "这个问题的优先级比较高，会优先处理。",
        ]
        return random.choice(comments)

    def _generate_random_title(self) -> str:
        """生成随机 Issue 标题"""
        title_prefixes = [
            "修复",
            "解决",
            "处理",
            "优化",
            "改进",
            "完善",
        ]

        issue_types = [
            "页面显示问题",
            "功能异常",
            "性能优化需求",
            "用户体验改进",
            "数据加载错误",
            "界面布局调整",
            "交互逻辑优化",
            "兼容性问题",
            "响应速度提升",
            "代码规范整改",
            "样式显示异常",
            "接口调用失败",
            "表单验证bug",
            "按钮点击无响应",
            "图片加载失败",
        ]

        priorities = [
            "",
            "【紧急】",
            "【高优先级】",
            "【待优化】",
        ]

        # 随机组合标题
        priority = random.choice(priorities)
        prefix = random.choice(title_prefixes)
        issue_type = random.choice(issue_types)

        if priority:
            return f"{priority}{prefix}{issue_type}"
        else:
            return f"{prefix}{issue_type}"

    def _generate_random_code(self) -> str:
        """生成随机代码内容"""
        code_snippets = [
            "# 优化性能\nimport time\nstart = time.time()\nprint(f'执行时间: {time.time() - start}')",
            "# 添加日志记录\nimport logging\nlogger = logging.getLogger(__name__)\nlogger.info('操作成功')",
            "# 数据验证\ndef validate_data(data):\n    if not data:\n        raise ValueError('数据不能为空')\n    return True",
            "# 异常处理\ntry:\n    result = process_data()\nexcept Exception as e:\n    print(f'处理失败: {e}')",
            "# 配置更新\nCONFIG = {\n    'timeout': 30,\n    'retry': 3,\n    'debug': True\n}",
            "# 工具函数\ndef format_output(data):\n    return f'结果: {data}'\n\nprint(format_output('测试'))",
            "# 状态检查\ndef check_status():\n    status = get_current_status()\n    return status == 'active'",
            "# 数据转换\ndef convert_format(input_data):\n    output = process(input_data)\n    return output",
            "# 缓存机制\ncache = {}\ndef get_cached(key):\n    return cache.get(key, None)",
            "# 性能监控\nimport psutil\nmem = psutil.virtual_memory()\nprint(f'内存使用: {mem.percent}%')",
            "# 字符串处理\ndef clean_text(text):\n    return text.strip().lower()\n\nresult = clean_text(' Hello World ')",
            "# 文件操作\nimport os\nif os.path.exists('data.txt'):\n    print('文件存在')",
        ]
        return random.choice(code_snippets)

    async def _commit_code_change(self, page, index: int) -> bool:
        """提交单次代码修改"""
        try:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"开始第 {index} 个代码提交任务")
            self.logger.info(f"{'='*60}")

            # 访问代码编辑页面
            self.logger.info(f"[{index}/3] 访问代码编辑页：{self.code_edit_url}")
            await page.goto(self.code_edit_url, timeout=self.browser_timeout)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            # 定位代码编辑区并获取现有内容
            editor_xpath = "/html/body/div[2]/div[2]/div[2]/form/div[2]/div[2]/div/div/div[1]/div[2]/div[1]/div[4]"
            self.logger.debug(f"[{index}/3] 定位编辑区并获取现有内容...")
            self.logger.debug(f"[{index}/3] Editor XPath: {editor_xpath}")

            editor = page.locator(f"xpath={editor_xpath}")

            # 输出定位器信息
            editor_count = await editor.count()
            self.logger.debug(f"[{index}/3] Editor 定位数量: {editor_count}")

            if editor_count > 0:
                # 获取元素的标签名和属性
                try:
                    elem_info = await editor.first.evaluate("""
                        (el) => {
                            return {
                                tagName: el.tagName,
                                className: el.className,
                                textLength: el.textContent ? el.textContent.length : 0,
                                visible: el.offsetParent !== null
                            };
                        }
                    """)
                    self.logger.debug(f"[{index}/3] Editor 元素信息: {elem_info}")
                except Exception as e:
                    self.logger.error(f"[{index}/3] 获取元素信息失败: {e}")

            # 获取现有内容
            existing_content = await editor.text_content()
            self.logger.debug(f"[{index}/3] 现有内容长度：{len(existing_content) if existing_content else 0} 字符")
            self.logger.debug(f"[{index}/3] 现有内容预览：{existing_content[:50] if existing_content else '(空)'}...")

            # 在现有内容上追加 "111"
            new_content = (existing_content or "") + "\n111"
            self.logger.info(f"[{index}/3] 追加内容：111")
            self.logger.debug(f"[{index}/3] 新内容长度：{len(new_content)} 字符")

            # 检查按钮初始状态
            commit_button_xpath = "/html/body/div[2]/div[2]/div[2]/form/div[3]/button"
            commit_btn = page.locator(f"xpath={commit_button_xpath}")

            try:
                if await commit_btn.count() > 0:
                    is_enabled_before = await commit_btn.first.is_enabled()
                    self.logger.info(f"[{index}/3] 内容更新前按钮状态：{'enabled' if is_enabled_before else 'disabled'}")
            except Exception as e:
                self.logger.error(f"[{index}/3] 检查按钮初始状态失败：{e}")

            # 方式1：尝试使用CodeMirror API直接设置内容
            self.logger.info(f"[{index}/3] 方式1：使用CodeMirror API更新内容...")
            try:
                result = await page.evaluate(
                    """
                    (newContent) => {
                        // 查找CodeMirror实例
                        const cmElement = document.querySelector('.CodeMirror');
                        if (cmElement && cmElement.CodeMirror) {
                            const cm = cmElement.CodeMirror;
                            const oldValue = cm.getValue();
                            cm.setValue(newContent);
                            // 触发change事件
                            cm.refresh();
                            return {
                                success: true,
                                oldLength: oldValue.length,
                                newLength: cm.getValue().length
                            };
                        }
                        return { success: false, error: 'CodeMirror实例未找到' };
                    }
                    """,
                    new_content
                )
                self.logger.info(f"[{index}/3] CodeMirror API结果：{result}")

                if result.get('success'):
                    self.logger.info(f"[{index}/3] ✓ 内容更新成功（CodeMirror API）")
                    await asyncio.sleep(1)

                    # 检查按钮是否变为enabled
                    if await commit_btn.count() > 0:
                        is_enabled_after = await commit_btn.first.is_enabled()
                        self.logger.info(f"[{index}/3] 内容更新后按钮状态：{'enabled' if is_enabled_after else 'disabled'}")

                        if is_enabled_after:
                            self.logger.info(f"[{index}/3] ✓✓✓ 按钮已变为enabled！")
                        else:
                            self.logger.warning(f"[{index}/3] ⚠️ 按钮仍然是disabled，尝试方式2...")
                            raise Exception("按钮未enabled，切换到方式2")
                else:
                    self.logger.error(f"[{index}/3] ⚠️ CodeMirror API失败，尝试方式2...")
                    raise Exception("CodeMirror API失败")

            except Exception as e:
                self.logger.error(f"[{index}/3] 方式1失败：{e}")

                # 方式2：点击编辑器 + 模拟键盘输入
                self.logger.info(f"[{index}/3] 方式2：点击编辑器 + 键盘输入...")
                try:
                    await editor.first.click()
                    await asyncio.sleep(0.5)

                    # 移动到内容末尾
                    await page.keyboard.press("Control+End")
                    await asyncio.sleep(0.3)

                    # 输入新内容
                    await page.keyboard.press("Enter")
                    await page.keyboard.type("111", delay=50)
                    await asyncio.sleep(0.5)

                    self.logger.info(f"[{index}/3] ✓ 内容更新成功（键盘输入）")

                    # 检查按钮是否变为enabled
                    if await commit_btn.count() > 0:
                        is_enabled_after = await commit_btn.first.is_enabled()
                        self.logger.info(f"[{index}/3] 内容更新后按钮状态：{'enabled' if is_enabled_after else 'disabled'}")

                        if is_enabled_after:
                            self.logger.info(f"[{index}/3] ✓✓✓ 按钮已变为enabled！")
                        else:
                            self.logger.warning(f"[{index}/3] ⚠️⚠️⚠️ 警告：按钮仍然是disabled！")

                except Exception as e2:
                    self.logger.error(f"[{index}/3] 方式2失败：{e2}")
                    self.logger.error(f"[{index}/3] ⚠️ 两种方式都失败，尝试继续...")

            await asyncio.sleep(1)

            # 滚动到页面底部，确保提交按钮可见
            self.logger.info(f"[{index}/3] 滚动到页面底部...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

            # 再次检查按钮状态，如果仍是disabled则等待
            self.logger.info(f"[{index}/3] 最终检查按钮状态...")
            commit_button_xpath = "/html/body/div[2]/div[2]/div[2]/form/div[3]/button"

            try:
                commit_btn = page.locator(f"xpath={commit_button_xpath}")
                if await commit_btn.count() > 0:
                    is_enabled_now = await commit_btn.first.is_enabled()
                    self.logger.info(f"[{index}/3] 当前按钮状态：{'enabled' if is_enabled_now else 'disabled'}")

                    if not is_enabled_now:
                        self.logger.info(f"[{index}/3] 按钮仍是disabled，等待变为enabled...")
                        await commit_btn.first.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)

                        # 等待按钮enabled（最多等待15秒）
                        for attempt in range(15):
                            is_enabled = await commit_btn.first.is_enabled()
                            if is_enabled:
                                self.logger.info(f"[{index}/3] ✓ 按钮已enabled，等待了{attempt}秒")
                                break
                            await asyncio.sleep(1)
                            if attempt % 3 == 0:
                                self.logger.info(f"[{index}/3] 等待按钮enabled... ({attempt}/15秒)")
                        else:
                            self.logger.warning(f"[{index}/3] ⚠️ 按钮15秒后仍未enabled，尝试继续")
                    else:
                        self.logger.info(f"[{index}/3] ✓ 按钮已经是enabled状态，无需等待")
            except Exception as e:
                self.logger.error(f"[{index}/3] 检查按钮状态失败：{e}")

            # 点击提交按钮（简化为单一策略：JavaScript强制点击）
            self.logger.info(f"[{index}/3] 点击'Commit Changes'按钮...")
            commit_clicked = False

            try:
                result = await page.evaluate("""
                    () => {
                        // 查找包含 "Commit Changes" 文本的按钮
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const commitBtn = buttons.find(btn =>
                            btn.textContent.includes('Commit Changes') ||
                            btn.textContent.includes('提交变更')
                        );
                        if (commitBtn) {
                            commitBtn.click();
                            return true;
                        }
                        return false;
                    }
                """)
                if result:
                    self.logger.info(f"[{index}/3] ✓ 提交按钮点击成功")
                    commit_clicked = True
                else:
                    self.logger.error(f"[{index}/3] ✗ 未找到提交按钮")
            except Exception as e:
                self.logger.error(f"[{index}/3] 点击失败：{e}")

            if not commit_clicked:
                self.logger.error(f"[{index}/3] ✗ 提交按钮点击失败")
                await page.screenshot(path=f"commit_button_fail_{index}.png", full_page=True)
                return False

            await asyncio.sleep(2)

            self.logger.info(f"[{index}/3] ✓✓✓ 第 {index} 个代码提交完成 ✓✓✓\n")
            return True

        except Exception as e:
            self.logger.error(f"[{index}/3] 代码提交任务失败：{e}")
            import traceback
            traceback.print_exc()
            try:
                await page.screenshot(path=f"commit_task_fail_{index}.png", full_page=True)
                self.logger.error(f"已保存失败截图：commit_task_fail_{index}.png")
            except Exception:
                pass
            return False

    async def _commit_code_batch(self, page, times: int = 3) -> bool:
        """批量提交代码修改"""
        success_count = 0
        for i in range(1, times + 1):
            result = await self._commit_code_change(page, i)
            if result:
                success_count += 1
            await asyncio.sleep(2)

        self.logger.info(f"\n{'='*60}")
        self.logger.debug(f"代码提交批量任务完成：成功 {success_count}/{times}")
        self.logger.info(f"{'='*60}\n")
        return success_count == times

    async def _create_branch_and_merge_request(self, page, index: int) -> bool:
        """创建新分支并提交合并请求"""
        try:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"开始第 {index} 个分支合并任务")
            self.logger.info(f"{'='*60}")

            # 访问代码编辑页面
            self.logger.info(f"[{index}/3] 访问代码编辑页：{self.branch_edit_url}")
            await page.goto(self.branch_edit_url, timeout=self.browser_timeout)
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            # 生成随机代码并填写到编辑区
            code_content = self._generate_random_code()
            self.logger.info(f"[{index}/3] 生成代码内容：\n{code_content[:100]}...")

            # 使用与代码提交任务相同的 XPath
            editor_xpath = "/html/body/div[2]/div[2]/div[2]/form/div[2]/div[2]/div/div/div[1]/div[2]/div[1]/div[4]"
            self.logger.debug(f"[{index}/3] 定位编辑区...")

            editor = page.locator(f"xpath={editor_xpath}")
            elem_count = await editor.count()
            self.logger.debug(f"[{index}/3] 找到 {elem_count} 个编辑区元素")

            if elem_count == 0:
                self.logger.error(f"[{index}/3] ✗ 未找到编辑区")
                return False

            # 获取现有内容
            existing_content = await editor.text_content()
            self.logger.debug(f"[{index}/3] 现有内容长度：{len(existing_content) if existing_content else 0} 字符")

            # 在现有内容上追加代码
            new_content = (existing_content or "") + "\n" + code_content
            self.logger.debug(f"[{index}/3] 新内容长度：{len(new_content)} 字符")

            # 检查按钮初始状态
            propose_xpath = "/html/body/div[2]/div[2]/div[2]/form/div[3]/button"
            propose_btn = page.locator(f"xpath={propose_xpath}")

            try:
                if await propose_btn.count() > 0:
                    is_enabled_before = await propose_btn.first.is_enabled()
                    self.logger.info(f"[{index}/3] 内容更新前按钮状态：{'enabled' if is_enabled_before else 'disabled'}")
            except Exception as e:
                self.logger.error(f"[{index}/3] 检查按钮初始状态失败：{e}")

            # 方式1：尝试使用CodeMirror API直接设置内容
            self.logger.info(f"[{index}/3] 方式1：使用CodeMirror API更新内容...")
            code_filled = False

            try:
                result = await page.evaluate(
                    """
                    (newContent) => {
                        // 查找CodeMirror实例
                        const cmElement = document.querySelector('.CodeMirror');
                        if (cmElement && cmElement.CodeMirror) {
                            const cm = cmElement.CodeMirror;
                            const oldValue = cm.getValue();
                            cm.setValue(newContent);
                            // 触发change事件
                            cm.refresh();
                            return {
                                success: true,
                                oldLength: oldValue.length,
                                newLength: cm.getValue().length
                            };
                        }
                        return { success: false, error: 'CodeMirror实例未找到' };
                    }
                    """,
                    new_content
                )
                self.logger.info(f"[{index}/3] CodeMirror API结果：{result}")

                if result.get('success'):
                    self.logger.info(f"[{index}/3] ✓ 内容更新成功（CodeMirror API）")
                    code_filled = True
                    await asyncio.sleep(1)

                    # 检查按钮是否变为enabled
                    if await propose_btn.count() > 0:
                        is_enabled_after = await propose_btn.first.is_enabled()
                        self.logger.info(f"[{index}/3] 内容更新后按钮状态：{'enabled' if is_enabled_after else 'disabled'}")

                        if is_enabled_after:
                            self.logger.info(f"[{index}/3] ✓✓✓ 按钮已变为enabled！")
                        else:
                            self.logger.warning(f"[{index}/3] ⚠️ 按钮仍然是disabled，尝试方式2...")
                            code_filled = False
                            raise Exception("按钮未enabled，切换到方式2")
                else:
                    self.logger.error(f"[{index}/3] ⚠️ CodeMirror API失败，尝试方式2...")
                    raise Exception("CodeMirror API失败")

            except Exception as e:
                self.logger.error(f"[{index}/3] 方式1失败：{e}")

                # 方式2：点击编辑器 + 模拟键盘输入
                self.logger.info(f"[{index}/3] 方式2：点击编辑器 + 键盘输入...")
                try:
                    await editor.first.click()
                    await asyncio.sleep(0.5)

                    # 移动到内容末尾
                    await page.keyboard.press("Control+End")
                    await asyncio.sleep(0.3)

                    # 输入新内容
                    await page.keyboard.press("Enter")
                    await page.keyboard.type(code_content, delay=50)
                    await asyncio.sleep(0.5)

                    self.logger.info(f"[{index}/3] ✓ 内容更新成功（键盘输入）")
                    code_filled = True

                    # 检查按钮是否变为enabled
                    if await propose_btn.count() > 0:
                        is_enabled_after = await propose_btn.first.is_enabled()
                        self.logger.info(f"[{index}/3] 内容更新后按钮状态：{'enabled' if is_enabled_after else 'disabled'}")

                        if is_enabled_after:
                            self.logger.info(f"[{index}/3] ✓✓✓ 按钮已变为enabled！")
                        else:
                            self.logger.warning(f"[{index}/3] ⚠️⚠️⚠️ 警告：按钮仍然是disabled！")

                except Exception as e2:
                    self.logger.error(f"[{index}/3] 方式2失败：{e2}")
                    code_filled = False

            if not code_filled:
                self.logger.error(f"[{index}/3] ✗ 填写代码失败")
                await page.screenshot(path=f"branch_code_fill_fail_{index}.png", full_page=True)
                return False

            await asyncio.sleep(1)

            # 滚动到页面底部，找到 radio 按钮区域
            self.logger.info(f"[{index}/3] 滚动到页面底部...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

            # 查找并点击 "为此提交创建一个新的分支" radio 按钮
            self.logger.info(f"[{index}/3] 查找 'ui radio checkbox' 并选择创建新分支...")
            radio_clicked = False
            branch_name = ""

            # 优先使用提供的 label XPath 选中“为此提交创建一个新的分支”
            try:
                radio_label_xpath = "/html/body/div[2]/div[2]/div[2]/form/div[3]/div/div[3]/div[2]/div/label"
                label_loc = page.locator(f"xpath={radio_label_xpath}")
                label_cnt = await label_loc.count()
                self.logger.debug(f"[{index}/3] 提供的 label XPath 找到 {label_cnt} 个元素")
                if label_cnt > 0:
                    await label_loc.first.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await label_loc.first.click()
                    self.logger.info(f"[{index}/3] ✓ 通过提供的 XPath 选中单选项")
                    radio_clicked = True
            except Exception as e:
                self.logger.error(f"[{index}/3] 通过提供的 XPath 选择单选项失败：{e}")

            # 策略1：查找包含特定文本的 radio
            try:
                # 尝试多种选择器
                selectors = [
                    "input[type='radio'][value='commit-to-new-branch']",
                    "input[name='commit_choice'][value='commit-to-new-branch']",
                    ".ui.radio.checkbox input[type='radio']",
                ]

                for selector in selectors:
                    radios = page.locator(selector)
                    radio_count = await radios.count()
                    self.logger.debug(f"[{index}/3] 选择器 '{selector}' 找到 {radio_count} 个元素")

                    if radio_count > 0:
                        # 尝试点击最后一个（通常是"创建新分支"）
                        target_radio = radios.last
                        try:
                            await target_radio.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            # 使用 check() 方法选中 radio
                            await target_radio.check()
                            self.logger.info(f"[{index}/3] ✓ Radio 按钮选中成功")
                            radio_clicked = True
                            break
                        except Exception as e:
                            self.logger.error(f"[{index}/3] check() 失败：{e}，尝试 click...")
                            try:
                                await target_radio.click()
                                self.logger.info(f"[{index}/3] ✓ Radio 按钮点击成功")
                                radio_clicked = True
                                break
                            except Exception as e2:
                                self.logger.error(f"[{index}/3] click 也失败：{e2}")
            except Exception as e:
                self.logger.error(f"[{index}/3] Radio 选择失败：{e}")

            # 策略2：通过 label 文本查找
            if not radio_clicked:
                self.logger.info(f"[{index}/3] 策略2：通过 label 文本查找...")
                try:
                    label_loc = page.locator("label:has-text('为此提交创建一个新的分支')")
                    if await label_loc.count() > 0:
                        await label_loc.first.click()
                        self.logger.info(f"[{index}/3] ✓ 通过 label 点击成功")
                        radio_clicked = True
                except Exception as e:
                    self.logger.error(f"[{index}/3] Label 点击失败：{e}")

            # 策略3：通过 JavaScript 强制选中
            if not radio_clicked:
                self.logger.info(f"[{index}/3] 策略3：通过 JavaScript 强制选中...")
                try:
                    await page.evaluate("""
                        () => {
                            const radios = document.querySelectorAll('input[type="radio"]');
                            if (radios.length > 1) {
                                radios[radios.length - 1].checked = true;
                                radios[radios.length - 1].dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        }
                    """)
                    self.logger.info(f"[{index}/3] ✓ JavaScript 强制选中成功")
                    radio_clicked = True
                except Exception as e:
                    self.logger.error(f"[{index}/3] JavaScript 失败：{e}")

            if not radio_clicked:
                self.logger.error(f"[{index}/3] ⚠️ Radio 选择可能失败，继续尝试提交...")

            # 读取新分支名称输入框的值（使用提供的 XPath）
            try:
                branch_input_xpath = "/html/body/div[2]/div[2]/div[2]/form/div[3]/div/div[3]/div[3]/div/input"
                input_loc = page.locator(f"xpath={branch_input_xpath}")
                input_cnt = await input_loc.count()
                self.logger.debug(f"[{index}/3] 分支输入框 XPath 找到 {input_cnt} 个元素")
                if input_cnt > 0:
                    branch_name = await input_loc.first.input_value()
                    self.logger.info(f"[{index}/3] 新分支名称：{branch_name}")
            except Exception as e:
                self.logger.error(f"[{index}/3] 读取分支名失败：{e}")

            await asyncio.sleep(1)

            # 关键：等待按钮从disabled变为enabled（参考22.png截图）
            self.logger.info(f"[{index}/3] 等待'提议文件更改'按钮从disabled变为enabled...")
            propose_xpath = "/html/body/div[2]/div[2]/div[2]/form/div[3]/button"

            try:
                propose_btn = page.locator(f"xpath={propose_xpath}")
                if await propose_btn.count() > 0:
                    # 滚动到按钮可见区域
                    await propose_btn.first.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)

                    # 等待按钮enabled（最多等待15秒）
                    self.logger.info(f"[{index}/3] 检测按钮状态...")
                    for attempt in range(15):
                        is_enabled = await propose_btn.first.is_enabled()
                        if is_enabled:
                            self.logger.info(f"[{index}/3] ✓ 按钮已enabled，等待{attempt}秒")
                            break
                        await asyncio.sleep(1)
                        if attempt % 3 == 0:
                            self.logger.info(f"[{index}/3] 等待按钮enabled... ({attempt}/15秒)")
                    else:
                        self.logger.warning(f"[{index}/3] ⚠️ 按钮15秒后仍未enabled，尝试继续")
            except Exception as e:
                self.logger.error(f"[{index}/3] 等待按钮enabled失败：{e}")

            # 点击"提议文件更改"按钮（简化为单一策略：JavaScript强制点击）
            self.logger.info(f"[{index}/3] 点击'提议文件更改'按钮...")
            propose_clicked = False

            try:
                result = await page.evaluate("""
                    () => {
                        // 查找包含 "Propose file change" 或 "提议文件更改" 文本的按钮
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const proposeBtn = buttons.find(btn =>
                            btn.textContent.includes('Propose file change') ||
                            btn.textContent.includes('提议文件更改')
                        );
                        if (proposeBtn) {
                            proposeBtn.click();
                            return true;
                        }
                        return false;
                    }
                """)
                if result:
                    self.logger.info(f"[{index}/3] ✓ '提议文件更改' 点击成功")
                    propose_clicked = True
                else:
                    self.logger.error(f"[{index}/3] ✗ 未找到'提议文件更改'按钮")
            except Exception as e:
                self.logger.error(f"[{index}/3] 点击失败：{e}")

            if not propose_clicked:
                self.logger.error(f"[{index}/3] ✗ '提议文件更改' 点击失败")
                await page.screenshot(path=f"propose_fail_{index}.png", full_page=True)
                return False

            await asyncio.sleep(3)  # 等待页面跳转

            # 等待页面跳转到合并请求页面（compare页面，参考33.png）
            self.logger.info(f"[{index}/3] 等待页面跳转到compare页面...")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            # 验证是否跳转到compare页面
            current_url = page.url
            self.logger.info(f"[{index}/3] 当前页面：{current_url}")

            if "compare" not in current_url:
                self.logger.error(f"[{index}/3] ✗ 未跳转到compare页面，当前URL：{current_url}")
                await page.screenshot(path=f"compare_fail_{index}.png", full_page=True)
                return False
            else:
                self.logger.info(f"[{index}/3] ✓ 已成功跳转到compare页面")
                if branch_name:
                    expected_url = f"{self.compare_base_url}...{branch_name}"
                    self.logger.info(f"[{index}/3] 期望URL：{expected_url}")

            # 点击"创建合并请求"按钮（compare页面，参考33.png/55.png）
            self.logger.info(f"[{index}/3] 点击'创建合并请求'按钮...")
            merge_clicked = False

            # 策略1：优先使用提供的XPath（参考55.png）
            try:
                merge_xpath = "/html/body/div[2]/div[2]/div[2]/div[2]/button"
                merge_btn = page.locator(f"xpath={merge_xpath}")
                merge_count = await merge_btn.count()
                self.logger.debug(f"[{index}/3] XPath找到 {merge_count} 个按钮")

                if merge_count > 0:
                    await merge_btn.first.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await merge_btn.first.click()
                    self.logger.info(f"[{index}/3] ✓ '创建合并请求' XPath点击成功")
                    merge_clicked = True
            except Exception as e:
                self.logger.error(f"[{index}/3] XPath点击失败：{e}")

            # 策略2：JavaScript强制点击（fallback）
            if not merge_clicked:
                try:
                    result = await page.evaluate("""
                        () => {
                            // 查找所有可点击元素（button和a标签）
                            const buttons = Array.from(document.querySelectorAll('button, a'));
                            const mergeBtn = buttons.find(btn => {
                                const text = btn.textContent.trim();
                                return text.includes('创建合并请求') ||
                                       text.includes('创建并合并请求') ||
                                       (text.includes('合并') && text.includes('请求'));
                            });
                            if (mergeBtn) {
                                mergeBtn.click();
                                return true;
                            }
                            return false;
                        }
                    """)
                    if result:
                        self.logger.info(f"[{index}/3] ✓ '创建合并请求' JavaScript点击成功")
                        merge_clicked = True
                    else:
                        self.logger.error(f"[{index}/3] ✗ JavaScript未找到'创建合并请求'按钮")
                except Exception as e:
                    self.logger.error(f"[{index}/3] JavaScript点击失败：{e}")

            if not merge_clicked:
                self.logger.error(f"[{index}/3] ✗ '创建合并请求' 点击失败")
                await page.screenshot(path=f"merge_fail_{index}.png", full_page=True)
                return False

            await asyncio.sleep(2)

            # 等待页面加载完成（跳转到PR创建表单页面，参考44.png）
            self.logger.info(f"[{index}/3] 等待跳转到PR创建表单页面...")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            # 点击"创建合并请求"按钮（PR表单页面，参考44.png，简化为单一策略：JavaScript强制点击）
            self.logger.info(f"[{index}/3] 点击最终'创建合并请求'按钮...")
            pr_clicked = False

            try:
                result = await page.evaluate("""
                    () => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const prBtn = buttons.find(btn =>
                            btn.textContent.includes('创建合并请求') ||
                            btn.textContent.includes('Create Pull Request') ||
                            btn.textContent.includes('提交')
                        );
                        if (prBtn) {
                            prBtn.click();
                            return true;
                        }
                        return false;
                    }
                """)
                if result:
                    self.logger.info(f"[{index}/3] ✓ '创建合并请求' 最终提交成功")
                    pr_clicked = True
                else:
                    self.logger.error(f"[{index}/3] ✗ 未找到'创建合并请求'按钮")
            except Exception as e:
                self.logger.error(f"[{index}/3] 点击失败：{e}")

            if not pr_clicked:
                self.logger.error(f"[{index}/3] ✗ '创建合并请求' 最终提交失败")
                await page.screenshot(path=f"pr_fail_{index}.png", full_page=True)
                return False

            await asyncio.sleep(2)

            self.logger.info(f"[{index}/3] ✓✓✓ 第 {index} 个分支合并任务完成 ✓✓✓\n")
            return True

        except Exception as e:
            self.logger.error(f"[{index}/3] 分支合并任务失败：{e}")
            try:
                await page.screenshot(path=f"branch_merge_fail_{index}.png", full_page=True)
                self.logger.error(f"已保存失败截图：branch_merge_fail_{index}.png")
            except Exception:
                pass
            return False

    async def _create_branch_and_merge_batch(self, page, times: int = 3) -> bool:
        """批量创建分支并提交合并请求"""
        success_count = 0
        for i in range(1, times + 1):
            result = await self._create_branch_and_merge_request(page, i)
            if result:
                success_count += 1
            await asyncio.sleep(2)

        self.logger.info(f"\n{'='*60}")
        self.logger.debug(f"分支合并批量任务完成：成功 {success_count}/{times}")
        self.logger.info(f"{'='*60}\n")
        return success_count == times

    async def run(self, headless: bool = False) -> bool:
        """执行单次完整任务流程"""
        execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"开始执行任务 [{execution_id}]")
        self.logger.info(f"{'='*60}\n")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=headless,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                    ]
                )

                # 创建上下文，根据配置启用视频录制
                context_options = {
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                }

                # 如果启用了视频录制，添加录制参数
                if self.enable_video_recording:
                    import os
                    os.makedirs(self.video_output_dir, exist_ok=True)
                    context_options["record_video_dir"] = self.video_output_dir
                    context_options["record_video_size"] = {"width": 1920, "height": 1080}
                    context_options["viewport"] = {"width": 1920, "height": 1080}
                    self.logger.info(f"✓ 视频录制已启用，保存目录：{self.video_output_dir}")
                    self.logger.info(f"✓ 视频分辨率：1920x1080")

                context = await browser.new_context(**context_options)
                page = await context.new_page()

                try:
                    ok = await self._login(page)
                    if not ok:
                        self.logger.error("登录失败")
                        return False

                    # 访问调试列表页
                    await self._goto_debugjob(page)

                    # 获取任务状态
                    status = await self._get_first_status(page)
                    self.logger.info(f"当前任务状态: {status}")

                    # 根据状态决定是否触发"再次调试"
                    if status == "STOPPED":
                        self.logger.info("任务状态为STOPPED，触发'再次调试'...")
                        clicked = await self._click_debug_again(page)
                        if not clicked:
                            self.logger.error("'再次调试'点击失败")
                            return False
                        await asyncio.sleep(5)
                        try:
                            await page.reload(wait_until="domcontentloaded")
                        except Exception:
                            pass
                        self.logger.info("等待状态变为 RUNNING...")
                        ok = await self._wait_for_status(page, target_status="RUNNING", timeout_sec=600, interval_sec=10)
                        if not ok:
                            self.logger.error("等待RUNNING状态超时")
                            return False
                        self.logger.info("✓ 任务已变为RUNNING状态")
                    elif status == "RUNNING":
                        self.logger.info("✓ 任务已经处于RUNNING状态")
                    else:
                        self.logger.error(f"未知状态：{status}")
                        return False

                    # 保存运行状态
                    try:
                        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        self._save_run_state(
                            username=self.username,
                            runflag=1,
                            createtime=today,
                            isrun=1
                        )
                    except Exception as e:
                        self.logger.error(f"保存RUNNING状态失败: {e}")

                    # 确保任务已经是RUNNING后，休眠5秒后开始执行批量任务
                    self.logger.info("\n任务已RUNNING，休眠 5 秒后开始执行批量操作...")
                    await asyncio.sleep(5)

                    # 批量创建 Issue 并评论（3次）
                    self.logger.info("\n" + "="*60)
                    self.logger.info("开始批量Issue创建与评论任务...")
                    self.logger.info("="*60)
                    issue_result = await self._create_and_comment_batch(page, times=3)
                    self.logger.info(f"\n✓ Issue 创建与评论结果：{'全部成功' if issue_result else '部分失败'}")

                    # 批量提交代码修改（3次）
                    self.logger.info("\n" + "="*60)
                    self.logger.info("开始批量代码提交任务...")
                    self.logger.info("="*60)
                    await asyncio.sleep(2)
                    code_result = await self._commit_code_batch(page, times=3)
                    self.logger.info(f"\n✓ 代码提交结果：{'全部成功' if code_result else '部分失败'}")

                    # 批量创建分支并提交合并请求（3次）
                    self.logger.info("\n" + "="*60)
                    self.logger.info("开始批量分支合并任务...")
                    self.logger.info("="*60)
                    await asyncio.sleep(2)
                    branch_result = await self._create_branch_and_merge_batch(page, times=3)
                    self.logger.info(f"\n✓ 分支合并结果：{'全部成功' if branch_result else '部分失败'}")

                    # 所有批量任务完成后，执行关闭操作
                    self.logger.info("\n" + "="*60)
                    self.logger.info("所有批量任务已完成，开始执行关闭任务操作...")
                    self.logger.info("="*60)
                    await asyncio.sleep(2)
                    stop_result = await self._click_stop_button(page)

                    # 输出最终结果
                    self.logger.info(f"\n{'='*60}")
                    self.logger.info(f"任务 [{execution_id}] 执行完成")
                    self.logger.info(f"{'='*60}")
                    self.logger.info(f"Issue创建: {'✓' if issue_result else '✗'}")
                    self.logger.info(f"代码提交: {'✓' if code_result else '✗'}")
                    self.logger.info(f"分支合并: {'✓' if branch_result else '✗'}")
                    self.logger.info(f"任务关闭: {'✓' if stop_result else '✗'}")
                    self.logger.info(f"{'='*60}\n")

                    # 如果启用了视频录制，提示保存
                    if self.enable_video_recording:
                        self.logger.info("\n正在保存视频...")
                        await asyncio.sleep(2)
                        self.logger.info(f"✓ 视频已保存到：{self.video_output_dir}")
                        self.logger.info("  视频格式：WebM（可用 VLC、Chrome 浏览器播放）")
                        self.logger.info("  如需转换为 MP4，可使用 ffmpeg：")
                        self.logger.info(f"    ffmpeg -i {self.video_output_dir}/<视频文件名>.webm output.mp4")

                    # 任务完成，保持浏览器打开一段时间以便查看
                    self.logger.info("\n任务完成，保持浏览器打开 30 秒以便查看...")
                    await asyncio.sleep(30)

                    return issue_result and code_result and branch_result and stop_result

                finally:
                    # finally 块只负责清理资源
                    try:
                        await browser.close()
                        self.logger.info("浏览器已关闭")
                    except Exception as e:
                        self.logger.error(f"关闭浏览器失败: {e}")

        except Exception as e:
            self.logger.error(f"任务执行异常 [{execution_id}]：{e}")
            import traceback
            traceback.print_exc()
            return False

    async def start_scheduler(self, bot_instance=None, headless: bool = False):
        """启动定时调度器（每日执行版本：24小时 + 5-20分钟随机延迟）"""
        if not bot_instance:
            bot_instance = self

        # 创建并存储调度器实例
        self.scheduler = AsyncIOScheduler()

        # 启动时立即执行一次（如果启用）
        if self.execute_on_startup:
            self.scheduler.add_job(
                self._execute_with_reschedule,
                id='openi_auto_execute',
                args=[headless],
                next_run_time=datetime.now()
            )
        else:
            # 如果不立即执行，则随机安排一个执行时间
            next_run = self._calculate_next_run_time()
            self.scheduler.add_job(
                self._execute_with_reschedule,
                id='openi_auto_execute',
                args=[headless],
                next_run_time=next_run
            )

        self.scheduler.start()

        self.logger.info(f"{'='*60}")
        self.logger.info("定时调度器已启动（每日执行模式）")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"下次执行时间：{self._format_next_run()}")
        self.logger.info(f"启动时立即执行：{'是' if self.execute_on_startup else '否'}")
        self.logger.info(f"执行间隔：每24小时 + 5-20分钟随机延迟")
        self.logger.info(f"{'='*60}")
        self.logger.info("\n⚠️ 程序将持续运行以执行定时任务")
        self.logger.info("按 Ctrl+C 可以优雅退出\n")

        try:
            # 保持主线程运行
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("\n正在关闭调度器...")
            self.scheduler.shutdown()
            self.logger.info("调度器已关闭")

    def _calculate_next_run_time(self, base_time=None):
        """计算下一次执行时间：24小时后再加5-20分钟随机延迟"""
        if base_time is None:
            base_time = datetime.now()

        # 固定间隔24小时 + 5-20分钟随机延迟
        random_minutes = random.randint(5, 20)
        next_run = base_time + timedelta(hours=24, minutes=random_minutes)

        self.logger.info(f"计算下次执行时间：24小时 + {random_minutes}分钟随机延迟")
        self.logger.info(f"当前时间：{base_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"下次执行：{next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        return next_run

    def _format_next_run(self):
        """格式化显示下次执行时间"""
        if self.execute_on_startup:
            return "立即执行"
        else:
            next_time = self._calculate_next_run_time()
            return next_time.strftime("%Y-%m-%d %H:%M:%S")

    async def _execute_with_reschedule(self, headless: bool = False):
        """执行任务并在完成后重新调度"""
        try:
            # 执行实际任务
            result = await self.run(headless=headless)

            # 如果执行成功，调度下一次执行
            if result:
                next_run_time = self._calculate_next_run_time()
                self.logger.info(f"✓ 任务执行成功，下次执行时间：{next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                # 如果执行失败，也继续调度（使用较短间隔重试）
                self.logger.warning("⚠️ 任务执行失败，将在30分钟后重试")
                next_run_time = datetime.now() + timedelta(minutes=30)

        except Exception as e:
            # 如果出现异常，记录错误并继续调度
            self.logger.error(f"❌ 任务执行异常：{e}")
            import traceback
            traceback.print_exc()
            # 异常后等待5分钟重试
            next_run_time = datetime.now() + timedelta(minutes=5)

        # 重新调度下一次执行
        if self.scheduler and self.scheduler.running:
            # 移除当前任务
            try:
                if 'openi_auto_execute' in self.scheduler.get_jobs():
                    self.scheduler.remove_job('openi_auto_execute')
            except Exception as e:
                self.logger.error(f"移除任务失败：{e}")

            # 添加下一次执行
            try:
                self.scheduler.add_job(
                    self._execute_with_reschedule,
                    id='openi_auto_execute',
                    args=[headless],
                    next_run_time=next_run_time
                )
            except Exception as e:
                self.logger.error(f"重新调度失败：{e}")


def setup_signal_handlers(logger_instance=None):
    """设置信号处理器用于优雅退出"""
    if not logger_instance:
        logger_instance = logging.getLogger(__name__)

    def signal_handler(signum, frame):
        logger_instance.info(f"\n收到信号 {signum}，准备退出...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """主函数，支持命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="启智平台自动积分获取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
  python login_getpoints.py                    # 手动执行一次
  python login_getpoints.py --auto             # 使用配置文件的自动模式
  python login_getpoints.py --auto --headless  # 自动模式+无头浏览器
  python login_getpoints.py --once --headless  # 单次执行+无头浏览器
        """
    )

    parser.add_argument(
        '--auto',
        action='store_true',
        help='启用自动定时执行模式（使用配置文件中的设置）'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='单次执行模式（忽略配置文件中的自动执行设置）'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='以无头模式运行浏览器（不显示浏览器窗口）'
    )

    args = parser.parse_args()

    # 设置日志记录器
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 设置信号处理器
    setup_signal_handlers(logger)

    try:
        bot = OpenIGetPoints()

        # 优先级：--once > --auto > 默认（单次执行）
        if args.once:
            logger.info("=" * 60)
            logger.info("执行模式：单次执行")
            logger.info("=" * 60)
            success = await bot.run(headless=args.headless)
            print("\n执行结果：", "成功" if success else "失败")
            return success
        elif args.auto or bot.auto_execute_enabled:
            # 自动模式
            logger.info("=" * 60)
            logger.info("执行模式：自动定时执行")
            logger.info("=" * 60)
            await bot.start_scheduler(bot_instance=bot, headless=args.headless)
        else:
            # 默认：单次执行
            logger.info("=" * 60)
            logger.info("执行模式：单次执行（配置文件未启用自动执行）")
            logger.info("=" * 60)
            success = await bot.run(headless=args.headless)
            print("\n执行结果：", "成功" if success else "失败")
            return success

    except KeyboardInterrupt:
        logger.info("\n用户中断，程序退出")
        return False
    except Exception as e:
        logger.error(f"\n程序执行异常：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(main())
