#!/usr/bin/env python3
"""
万年历 — 终端版 + Web 版 + GUI 版
====================================
用法:
    python main.py                    # 终端显示当月
    python main.py 2026               # 终端显示全年
    python main.py 2026 6             # 终端显示指定年月
    python main.py -i                 # 终端交互模式
    python main.py --web              # 启动 Web 版（浏览器打开）
    python main.py --gui              # 启动 GUI 图形界面
"""

import argparse
import sys
import webbrowser
import threading
import time


def main():
    parser = argparse.ArgumentParser(
        description="📅 万年历 — 公历/农历/节气/节日",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                终端显示当前月份
  python main.py 2026           终端显示 2026 年全年
  python main.py 2026 6         终端显示 2026 年 6 月
  python main.py -i             终端交互模式（方向键导航）
  python main.py --web          启动 Web 版并在浏览器中打开
  python main.py --gui          启动 GUI 图形界面
        """,
    )
    parser.add_argument("year", nargs="?", type=int, help="年份 (1900–2100)")
    parser.add_argument("month", nargs="?", type=int, help="月份 (1–12)")
    parser.add_argument("-i", "--interactive", action="store_true", help="终端交互模式")
    parser.add_argument("--web", action="store_true", help="启动 Web 版")
    parser.add_argument("--gui", action="store_true", help="启动 GUI 图形界面")
    parser.add_argument("--port", type=int, default=5000, help="Web 端口 (默认 5000)")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")

    args = parser.parse_args()

    year, month = args.year, args.month
    if year is not None and (year < 1900 or year > 2100):
        print(f"错误: 年份超出范围 (1900–2100): {year}")
        sys.exit(1)
    if month is not None and (month < 1 or month > 12):
        print(f"错误: 月份超出范围 (1–12): {month}")
        sys.exit(1)
    if month is not None and year is None:
        print("错误: 指定月份时必须同时指定年份")
        sys.exit(1)

    # ── Web 模式 ──
    if args.web:
        from src.webapp import run_web

        host = "127.0.0.1"
        port = args.port
        url = f"http://{host}:{port}"

        if not args.no_browser:
            def _open():
                time.sleep(0.8)
                webbrowser.open(url)
            threading.Thread(target=_open, daemon=True).start()

        run_web(host=host, port=port)
        return

    # ── GUI 模式 ──
    if args.gui:
        from src.gui import run_gui
        run_gui(year=year, month=month)
        return

    # ── 终端交互模式 ──
    if args.interactive:
        from src.tui import InteractiveCalendar
        app = InteractiveCalendar(year=year, month=month)
        app.run()
        return

    # ── 终端静态模式 ──
    if year is None:
        from src.renderer import print_current_month
        print_current_month()
        return
    if month is None:
        from src.renderer import print_year
        print_year(year)
        return

    from src.renderer import print_month
    print_month(year, month)


if __name__ == "__main__":
    main()
