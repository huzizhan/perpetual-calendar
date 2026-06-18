#!/usr/bin/env python3
"""
万年历 — 终端/Web/GUI 四历法统一版
=====================================
用法:
    python main.py                      # 终端当月（农历）
    python main.py 2026                 # 终端全年
    python main.py 2026 6               # 终端指定年月
    python main.py --islamic            # 终端伊斯兰历
    python main.py --japanese 2026 6    # 终端日本和历
    python main.py --buddhist           # 终端佛历
    python main.py --web                # Web 统一版（四历法一键切换）
    python main.py -i                   # 终端交互模式
"""

import argparse
import datetime
import sys
import webbrowser
import threading
import time


def main():
    parser = argparse.ArgumentParser(
        description="📅 万年历 — 农历/伊斯兰历/日本和历/佛历",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例: python main.py --web  |  python main.py --japanese 2026 6",
    )
    parser.add_argument("year", nargs="?", type=int, help="年份")
    parser.add_argument("month", nargs="?", type=int, help="月份 (1–12)")
    parser.add_argument("-i", "--interactive", action="store_true", help="终端交互模式")
    parser.add_argument("--web", action="store_true", help="启动 Web 统一版（推荐）")
    parser.add_argument("--gui", action="store_true", help="GUI 图形界面")
    parser.add_argument("--islamic", action="store_true", help="终端伊斯兰历")
    parser.add_argument("--japanese", action="store_true", help="终端日本和历")
    parser.add_argument("--buddhist", action="store_true", help="终端佛历")
    parser.add_argument("--port", type=int, default=5000, help="Web 端口")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")

    args = parser.parse_args()
    year, month = args.year, args.month

    if year is not None and (year < 622 or year > 2100):
        print(f"错误: 年份超出范围: {year}"); sys.exit(1)
    if month is not None and (month < 1 or month > 12):
        print(f"错误: 月份超出范围 (1–12): {month}"); sys.exit(1)
    if month is not None and year is None:
        print("错误: 指定月份时必须同时指定年份"); sys.exit(1)

    # ── Web ──
    if args.web:
        from src.webapp import run_web
        host, port = "0.0.0.0", args.port
        if not args.no_browser:
            def _open(): time.sleep(0.8); webbrowser.open(f"http://127.0.0.1:{port}")
            threading.Thread(target=_open, daemon=True).start()
        run_web(host=host, port=port); return

    # ── GUI ──
    if args.gui:
        from src.gui import run_gui; run_gui(year=year, month=month); return

    # ── 终端：确定历法 ──
    cal_mode = "chinese"
    if args.islamic: cal_mode = "islamic"
    elif args.japanese: cal_mode = "japanese"
    elif args.buddhist: cal_mode = "buddhist"

    # ── 终端交互 ──
    if args.interactive:
        from src.tui import InteractiveCalendar
        InteractiveCalendar(year=year, month=month).run(); return

    # ── 终端静态 ──
    if year is None:
        y, m = datetime.date.today().year, datetime.date.today().month
    elif month is None:
        y, m = year, None
    else:
        y, m = year, month

    _print_terminal(cal_mode, y, m)


def _print_terminal(mode: str, year: int, month: int | None):
    from src.renderer import (
        print_month, print_year, print_current_month,
        print_islamic_month, print_islamic_year,
        print_japanese_month, print_japanese_year,
        print_buddhist_month, print_buddhist_year,
    )

    if mode == "islamic":
        if month is None: print_islamic_year(year)
        else: print_islamic_month(year, month)
    elif mode == "japanese":
        if month is None: print_japanese_year(year)
        else: print_japanese_month(year, month)
    elif mode == "buddhist":
        if month is None: print_buddhist_year(year)
        else: print_buddhist_month(year, month)
    else:
        if month is None: print_year(year)
        else: print_month(year, month)


if __name__ == "__main__":
    main()
