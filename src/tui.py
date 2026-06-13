"""
交互式终端万年历 (TUI)
支持方向键翻月、快捷键跳转。
"""

import datetime
from typing import Optional

from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table

from .renderer import render_month
from .lunar import year_sexagenary, year_zodiac


class InteractiveCalendar:
    """交互式万年历"""

    def __init__(self, year: Optional[int] = None, month: Optional[int] = None):
        today = datetime.date.today()
        self.year = year or today.year
        self.month = month or today.month
        self.today = today
        self.running = False

    def run(self) -> None:
        """启动交互模式"""
        self.running = True
        self._print_header()

        with Live(
            self._build_layout(),
            refresh_per_second=10,
            screen=True,
        ) as live:
            while self.running:
                try:
                    key = self._get_key()
                    if key == "q" or key == "\x1b":
                        self.running = False
                    elif key == "right" or key == "l":
                        self._next_month()
                    elif key == "left" or key == "h":
                        self._prev_month()
                    elif key == "up" or key == "k":
                        self._next_year()
                    elif key == "down" or key == "j":
                        self._prev_year()
                    elif key == "t":
                        self._go_today()
                    elif key == "y":
                        self._prompt_year()
                    elif key == "m":
                        self._prompt_month()
                    elif key == "a":
                        self._print_annual()
                        break

                    live.update(self._build_layout())
                except (EOFError, KeyboardInterrupt):
                    self.running = False
                    break

    def _get_key(self) -> str:
        """读取键盘输入"""
        import sys
        import tty
        import termios

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                # 可能的转义序列
                extra = sys.stdin.read(2)
                if extra == "[A":
                    return "up"
                elif extra == "[B":
                    return "down"
                elif extra == "[C":
                    return "right"
                elif extra == "[D":
                    return "left"
                else:
                    return "\x1b"  # ESC
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    def _next_month(self) -> None:
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1

    def _prev_month(self) -> None:
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1

    def _next_year(self) -> None:
        self.year += 1

    def _prev_year(self) -> None:
        self.year -= 1

    def _go_today(self) -> None:
        self.year = self.today.year
        self.month = self.today.month

    def _prompt_year(self) -> None:
        self.running = False
        try:
            import sys
            # 临时恢复终端
            sys.stdout.write("\r\n跳转到年份: ")
            sys.stdout.flush()
            val = input()
            y = int(val)
            if 1900 <= y <= 2100:
                self.year = y
        except (ValueError, EOFError):
            pass
        self.running = True

    def _prompt_month(self) -> None:
        self.running = False
        try:
            import sys
            sys.stdout.write("\r\n跳转到月份 (1-12): ")
            sys.stdout.flush()
            val = input()
            m = int(val)
            if 1 <= m <= 12:
                self.month = m
        except (ValueError, EOFError):
            pass
        self.running = True

    def _print_annual(self) -> None:
        """打印全年日历（退出交互模式）"""
        self.running = False
        from .renderer import print_year
        print_year(self.year)

    def _build_layout(self) -> Layout:
        """构建 Rich Layout"""
        layout = Layout()

        # 标题栏
        sexagenary = year_sexagenary(self.year)
        zodiac = year_zodiac(self.year)
        header_text = Text()
        header_text.append("📅  ", style="")
        header_text.append(f"  {self.year}年 {self.month}月  ", style="bold bright_yellow")
        header_text.append(f"({sexagenary}{zodiac}年)", style="dim")
        header_text.append("\n")
        header_text.append(
            "←→ 翻月  ↑↓ 翻年  [t]今天  [y]跳转年  [m]跳转月  [a]全年视图  [q]退出",
            style="dim italic",
        )

        layout.split(
            Layout(Align.center(header_text), size=4, name="header"),
            Layout(name="calendar"),
        )

        # 日历表
        table = render_month(self.year, self.month, highlight_today=True)

        # 今日信息
        today_info = Text()
        today_info.append(f"今天是: {self.today.year}年{self.today.month}月{self.today.day}日  ", style="bold")
        today_info.append(f"星期{'一二三四五六日'[self.today.weekday()]}", style="bold cyan")

        calendar_panel = Panel(
            Align.center(table),
            title=today_info,
            border_style="bright_blue",
        )
        layout["calendar"].update(calendar_panel)

        return layout

    def _print_header(self) -> None:
        """打印启动信息"""
        pass
