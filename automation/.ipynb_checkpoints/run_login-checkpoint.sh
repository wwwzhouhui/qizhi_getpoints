#!/usr/bin/env bash
set -euo pipefail

# 在容器中以无头模式运行登录与CloudBrains自动化
python3 - <<'PY'
import asyncio
from login_automation import OpenISimple

async def main():
    bot = OpenISimple()
    ok = await bot.run(headless=True)
    print('执行结果：', '成功' if ok else '失败')

asyncio.run(main())
PY

