#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Playwright 录制启动脚本

功能：
1. 创建带视频录制功能的浏览器
2. 调用 login_getpoints.py 的主逻辑进行操作
3. 自动录制整个过程为视频

使用方法：
1. 直接运行本脚本：python3 playwright_luzhi.py
2. 脚本会自动录制 login_getpoints.py 的操作过程
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

# 导入主脚本的类
import sys
sys.path.insert(0, os.path.dirname(__file__))
from login_getpoints import OpenIGetPoints


class RecordingBot:
    def __init__(self, config_file: str = "config_getpoints.ini", output_dir: str = "./recordings"):
        """
        初始化录制机器人

        Args:
            config_file: 配置文件路径
            output_dir: 视频输出目录
        """
        self.config_file = config_file
        self.output_dir = output_dir

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

    async def run_with_recording(self, headless: bool = False):
        """
        运行任务并录制视频

        Args:
            headless: 是否无头模式
        """
        # 生成视频文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"openi_automation_{timestamp}.webm"
        video_path = os.path.join(self.output_dir, video_filename)

        print("="*60)
        print("Playwright 录制启动脚本 v1.0")
        print("="*60)
        print(f"配置文件: {self.config_file}")
        print(f"视频保存: {video_path}")
        print(f"录制模式: {'无头模式' if headless else '有界面模式'}")
        print(f"视频分辨率: 1920x1080")
        print("="*60)
        print()

        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )

            # 创建上下文，启用视频录制
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                record_video_dir=self.output_dir,
                record_video_size={"width": 1920, "height": 1080},
                viewport={"width": 1920, "height": 1080}
            )

            page = await context.new_page()

            print("✓ 浏览器已启动，开始录制")
            print()

            try:
                # 创建主脚本实例（但不使用它的 run 方法）
                bot = OpenIGetPoints(self.config_file)

                # 执行登录
                ok = await bot._login(page)
                if not ok:
                    print("登录失败")
                    return False

                # 访问调试列表页
                await bot._goto_debugjob(page)

                status = await bot._get_first_status(page)
                if status == "STOPPED":
                    clicked = await bot._click_debug_again(page)
                    if not clicked:
                        print("'再次调试'点击失败")
                        return False
                    await asyncio.sleep(5)
                    try:
                        await page.reload(wait_until="domcontentloaded")
                    except Exception:
                        pass
                    print("等待状态变为 RUNNING...")
                    ok = await bot._wait_for_status(page, target_status="RUNNING", timeout_sec=600, interval_sec=10)
                    print(f"等待结果：{ok}")

                    if ok:
                        # 状态变为 RUNNING 后，休眠 5 秒，然后批量创建 Issue 并评论
                        print("检测到 RUNNING 状态，休眠 5 秒后开始批量任务...")
                        await asyncio.sleep(5)
                        issue_result = await bot._create_and_comment_batch(page, times=3)
                        print(f"\nIssue 创建与评论结果：{'全部成功' if issue_result else '部分失败'}")

                        # 批量提交代码修改
                        print("\n开始批量代码提交任务...")
                        await asyncio.sleep(2)
                        code_result = await bot._commit_code_batch(page, times=3)
                        print(f"\n代码提交结果：{'全部成功' if code_result else '部分失败'}")

                        # 批量创建分支并提交合并请求
                        print("\n开始批量分支合并任务...")
                        await asyncio.sleep(2)
                        branch_result = await bot._create_branch_and_merge_batch(page, times=3)
                        print(f"\n分支合并结果：{'全部成功' if branch_result else '部分失败'}")

                        print(f"\n{'='*60}")
                        print(f"所有任务完成 - Issue: {'✓' if issue_result else '✗'} | 代码: {'✓' if code_result else '✗'} | 分支: {'✓' if branch_result else '✗'}")
                        print(f"{'='*60}")

                    return ok
                elif status == "RUNNING":
                    print("已处于 RUNNING 状态")
                    # 休眠 5 秒后批量创建 Issue 并评论
                    print("休眠 5 秒后开始批量任务...")
                    await asyncio.sleep(5)
                    issue_result = await bot._create_and_comment_batch(page, times=3)
                    print(f"\nIssue 创建与评论结果：{'全部成功' if issue_result else '部分失败'}")

                    # 批量提交代码修改
                    print("\n开始批量代码提交任务...")
                    await asyncio.sleep(2)
                    code_result = await bot._commit_code_batch(page, times=3)
                    print(f"\n代码提交结果：{'全部成功' if code_result else '部分失败'}")

                    # 批量创建分支并提交合并请求
                    print("\n开始批量分支合并任务...")
                    await asyncio.sleep(2)
                    branch_result = await bot._create_branch_and_merge_batch(page, times=3)
                    print(f"\n分支合并结果：{'全部成功' if branch_result else '部分失败'}")

                    print(f"\n{'='*60}")
                    print(f"所有任务完成 - Issue: {'✓' if issue_result else '✗'} | 代码: {'✓' if code_result else '✗'} | 分支: {'✓' if branch_result else '✗'}")
                    print(f"{'='*60}")

                    return True
                else:
                    print(f"状态非 STOPPED/RUNNING：{status}")
                    return False

            finally:
                print("\n任务完成，正在保存视频...")
                await asyncio.sleep(2)

                # 关闭页面和上下文以保存视频
                await page.close()
                await context.close()
                await browser.close()

                print(f"\n✓ 视频已保存到：{video_path}")
                print("\n提示：WebM 格式可用 VLC、Chrome 浏览器播放")
                print("如需转换为 MP4，可使用命令：")
                print(f"  ffmpeg -i {video_path} -c:v libx264 -crf 23 -c:a aac {video_path.replace('.webm', '.mp4')}")


async def main():
    # 创建录制机器人
    bot = RecordingBot(
        config_file="config_getpoints.ini",
        output_dir="./recordings"
    )

    # 运行并录制（非无头模式，可看到操作过程）
    success = await bot.run_with_recording(headless=False)

    print("\n执行结果：", "成功" if success else "失败")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序异常：{e}")
        import traceback
        traceback.print_exc()
