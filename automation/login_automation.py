#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版：登录 -> 访问 cloudbrains -> 点击“再次调试”
运行方式：python login_automation.py
依赖：Playwright（async），配置来自 config.ini
"""

import asyncio
import configparser
import os
from playwright.async_api import async_playwright
from datetime import datetime, time as dtime


class OpenISimple:
    def __init__(self, config_file: str = "config.ini") -> None:
        self.config_file = config_file
        self._load_config()

    def _load_config(self) -> None:
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在：{self.config_file}")
        cfg = configparser.ConfigParser()
        cfg.read(self.config_file, encoding="utf-8")

        # 登录与页面 URL
        self.login_url = cfg.get("login", "login_url")
        self.cloudbrains_url = cfg.get("login", "cloudbrains_url")
        self.username = cfg.get("login", "username")
        self.password = cfg.get("login", "password")

        # XPath 选择器
        self.username_xpath = cfg.get("xpath", "username_xpath")
        self.password_xpath = cfg.get("xpath", "password_xpath")
        self.login_button_xpath = cfg.get("xpath", "login_button_xpath")
        self.search_input_xpath = cfg.get("xpath", "search_input_xpath")
        self.debug_again_button_xpath = cfg.get("xpath", "debug_again_button_xpath")
        # 任务状态首行 XPath
        self.first_status_xpath = \
            "/html/body/div[2]/div[2]/div[2]/div/div[2]/div[2]/div[1]/div[3]/table/tbody/tr[1]/td[4]/div/div/span"
        # 弹窗关闭兜底（可选）
        self.popup_close_button_xpath = cfg.get("xpath", "popup_close_button_xpath", fallback="")

        # 设置
        self.browser_timeout = cfg.getint("settings", "browser_timeout", fallback=120000)

    async def _login(self, page) -> bool:
        print("访问登录页...")
        await page.goto(self.login_url, timeout=self.browser_timeout)
        await page.wait_for_load_state("domcontentloaded")

        print("填写用户名/密码并点击登录...")
        await page.fill(f"xpath={self.username_xpath}", self.username)
        await page.fill(f"xpath={self.password_xpath}", self.password)
        await page.click(f"xpath={self.login_button_xpath}")

        # 等待跳转或登录成功的可见线索
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(1)
        return True

    async def _close_popup_minimal(self, page) -> None:
        """最小化弹窗关闭：尝试点击 close/关闭/确定 等。失败不抛异常。"""
        selectors = [
            "div.ui.positive.button:has-text('Close')",
            "text=关闭",
            "text=确定",
            "text=知道了",
            "button:has-text('关闭')",
            "button:has-text('确定')",
            "button:has-text('知道了')",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0 and await loc.first.is_visible():
                    # 处理倒计时（如果存在）
                    try:
                        cd = loc.first.locator("span.count-down")
                        if await cd.count() > 0:
                            txt = (await cd.first.text_content() or "").strip()
                            if txt.isdigit():
                                n = int(txt)
                                print(f"检测到倒计时：{n}秒，等待...")
                                for i in range(n, 0, -1):
                                    await asyncio.sleep(1)
                    except Exception:
                        pass
                    await loc.first.click()
                    await asyncio.sleep(0.5)
                    print("已尝试关闭弹窗")
                    break
            except Exception:
                continue

    async def _wait_and_close_modal(self, page) -> None:
        """
        等待并关闭包含倒计时的公告弹窗：
        - 优先定位 Fomantic 的 Close 按钮 div.ui.positive.button:has-text('Close')
        - 如有 span.count-down，按其中数字等待；否则在遮罩存在时兜底等待10秒
        - 点击关闭并等待遮罩消失
        失败不抛异常
        """
        try:
            # 是否存在遮罩/模态层
            overlay_selectors = [
                ".ui.dimmer.modals.page.transition.visible.active",
                ".ui.dimmer.modals.page.animating.transition.fade.in",
                ".ui.dimmer.modals.page.visible.active",
                ".modal:visible",
            ]
            def overlay_locator():
                return page.locator(", ".join(overlay_selectors))

            # 查找 Close 按钮
            close_btn = page.locator("div.ui.positive.button:has-text('Close')")
            if await close_btn.count() == 0 and await overlay_locator().count() == 0:
                return  # 无弹窗

            # 读取倒计时（优先从按钮内）
            countdown = None
            try:
                cd = close_btn.first.locator("span.count-down")
                if await cd.count() > 0:
                    txt = (await cd.first.text_content() or "").strip()
                    if txt.isdigit():
                        countdown = int(txt)
            except Exception:
                pass

            # 如果无法读取数字，但可见遮罩，兜底等待10秒
            if countdown is None and await overlay_locator().count() > 0:
                countdown = 10

            if countdown and countdown > 0:
                print(f"检测到弹窗倒计时：{countdown}秒，等待...")
                for _ in range(countdown):
                    await asyncio.sleep(1)

            # 倒计时结束后点击关闭
            if await close_btn.count() > 0 and await close_btn.first.is_visible():
                try:
                    await close_btn.first.click()
                except Exception:
                    try:
                        await close_btn.first.evaluate("el => el.click()")
                    except Exception:
                        pass

            # 等待遮罩消失
            try:
                for _ in range(20):
                    if await overlay_locator().count() == 0:
                        break
                    await asyncio.sleep(0.5)
            except Exception:
                pass
        except Exception:
            pass

    async def _goto_cloudbrains(self, page) -> None:
        print(f"访问 cloudbrains: {self.cloudbrains_url}")
        await page.goto(self.cloudbrains_url, timeout=self.browser_timeout)
        await page.wait_for_load_state("domcontentloaded")
        # 刷新一次以确保公告弹窗出现（若有）
        try:
            await page.reload(wait_until="domcontentloaded")
        except Exception:
            pass
        await asyncio.sleep(1)
        await self._close_popup_minimal(page)

    async def _get_first_status(self, page) -> str:
        """读取第一条记录的状态文本，返回大写状态，如 RUNNING/STOPPED。失败返回空字符串。"""
        try:
            # 先确保弹窗关闭（按需等待倒计时）
            await self._wait_and_close_modal(page)
            await page.wait_for_selector(f"xpath={self.first_status_xpath}", timeout=10000)
            txt = await page.locator(f"xpath={self.first_status_xpath}").first.text_content()
            status = (txt or "").strip().upper()
            print(f"当前第一条记录状态：{status}")
            return status
        except Exception as e:
            print(f"读取第一条状态失败：{e}")
            return ""

    async def _monitor_and_act(self, page) -> None:
        """
        定时任务：
        - 若第一条状态为 RUNNING：休眠 30 秒并继续轮询；
        - 若为 STOPPED：触发点击‘再次调试’，随后继续轮询；
        - 其他状态：每 30 秒轮询一次。
        """
        while True:
            # 每次轮询前，优先处理弹窗（等待倒计时后关闭）
            await self._wait_and_close_modal(page)
            status = await self._get_first_status(page)
            if not status:
                # 状态不可读，尝试刷新后重试
                try:
                    await page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                await asyncio.sleep(5)
                continue

            if status == "RUNNING":
                print("任务运行中，休眠 30 秒后继续检测...")
                await asyncio.sleep(30)
                try:
                    await page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass
                await self._close_popup_minimal(page)
                continue

            if status == "STOPPED":
                # 判断是否处于工作时间段
                if self._within_work_windows():
                    print("任务已停止（工作时间段），尝试点击‘再次调试’...")
                    # 点击前再次确保弹窗关闭
                    await self._wait_and_close_modal(page)
                    clicked = await self._click_debug_again(page)
                    if clicked:
                        print("已触发‘再次调试’，休眠 10 秒后继续监控...")
                        await asyncio.sleep(10)
                        try:
                            await page.reload(wait_until="domcontentloaded")
                        except Exception:
                            pass
                        await self._close_popup_minimal(page)
                    else:
                        print("‘再次调试’点击失败，10 秒后重试...")
                        await asyncio.sleep(10)
                else:
                    print("当前非工作时间段（允许时间：08:00-12:00, 13:00-17:00, 19:00-23:59），不触发‘再次调试’。")
                    await asyncio.sleep(30)
                    try:
                        await page.reload(wait_until="domcontentloaded")
                    except Exception:
                        pass
                    await self._close_popup_minimal(page)
                continue

            # 其他状态（例如 QUEUED、FAILED 等），每 30 秒轮询一次
            print("状态非 RUNNING/STOPPED，休眠 30 秒后继续检测...")
            await asyncio.sleep(30)
            try:
                await page.reload(wait_until="domcontentloaded")
            except Exception:
                pass
            await self._close_popup_minimal(page)
            continue

    def _within_work_windows(self) -> bool:
        """判断当前本地时间是否在工作时间段内。"""
        now = datetime.now().time()
        windows = [
            (dtime(8, 0, 0), dtime(12, 0, 0)),
            (dtime(13, 0, 0), dtime(17, 0, 0)),
            (dtime(19, 0, 0), dtime(23, 59, 59)),  # 19:00 - 23:59:59
        ]
        for start, end in windows:
            if start <= now <= end:
                return True
        return False

        

    async def _click_debug_again(self, page) -> bool:
        print("点击‘再次调试’...")
        try:
            await page.wait_for_selector(f"xpath={self.debug_again_button_xpath}", timeout=self.browser_timeout)
            await page.click(f"xpath={self.debug_again_button_xpath}")
            print("已点击‘再次调试’")
            return True
        except Exception as e:
            print(f"点击‘再次调试’失败：{e}")
            return False

    async def run(self, headless: bool = False) -> bool:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                ok = await self._login(page)
                if not ok:
                    print("登录失败")
                    return False

                await asyncio.sleep(1)
                await self._goto_cloudbrains(page)
                # 进入轮询监控任务状态，并在 STOPPED 时触发‘再次调试’
                await self._monitor_and_act(page)
                return True
            finally:
                # 给少量时间观察
                await asyncio.sleep(2)
                await browser.close()


async def main():
    bot = OpenISimple()
    success = await bot.run(headless=False)
    print("执行结果：", "成功" if success else "失败")


if __name__ == "__main__":
    asyncio.run(main())
