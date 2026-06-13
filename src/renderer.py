"""
终端渲染器 — 使用 Rich 库绘制万年历
"""

import calendar
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import Box, MINIMAL, SIMPLE_HEAVY
from rich.align import Align
from rich.style import Style
from rich.color import Color

from .lunar import (
    solar_to_lunar,
    lunar_date_str,
    year_sexagenary,
    year_zodiac,
    lunar_festival,
    solar_festival,
    LunarDate,
)
from .solar_terms import get_solar_terms_for_month, SolarTerm

console = Console()

# 颜色方案
COLOR_SUNDAY = "red"
COLOR_SATURDAY = "blue"
COLOR_TODAY_BG = "bright_green"
COLOR_FESTIVAL = "bright_yellow"
COLOR_SOLAR_TERM = "bright_cyan"
COLOR_LUNAR = "dim"
COLOR_HEADER = "bold white"
COLOR_TITLE = "bold yellow"
COLOR_WEEKDAY = "bold cyan"


def render_month(
    year: int,
    month: int,
    highlight_today: bool = True,
) -> Table:
    """
    渲染单个月份的万年历。
    返回 rich Table 对象。
    """
    # 获取该月的日历矩阵
    cal = calendar.Calendar(firstweekday=0)  # 周一作为每周第一天
    month_days = cal.monthdayscalendar(year, month)

    # 计算本月节气
    solar_terms = get_solar_terms_for_month(year, month)
    term_map: dict[int, str] = {}  # day -> term_name
    for st in solar_terms:
        term_map[st.day] = st.name

    # 干支纪年 + 生肖
    sexagenary = year_sexagenary(year)
    zodiac = year_zodiac(year)

    # 表头
    title = f"[bold yellow]{year}年 {month}月[/bold yellow]  [dim]{sexagenary}{zodiac}年[/dim]"

    table = Table(
        title=title,
        box=SIMPLE_HEAVY,
        show_header=True,
        header_style=COLOR_WEEKDAY,
        title_justify="center",
        expand=False,
        padding=(1, 2),
    )

    # 星期标题
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    for i, wd in enumerate(weekdays):
        style = COLOR_SUNDAY if i == 6 else (COLOR_SATURDAY if i == 5 else "")
        table.add_column(wd, justify="center", style=style, width=10)

    # 今天日期（用于高亮）
    import datetime
    today = datetime.date.today()

    # 计算该月所有农历信息
    lunar_cache: dict[int, tuple[str, Optional[str]]] = {}  # day -> (lunar_str, festival)
    for week in month_days:
        for day in week:
            if day == 0:
                continue
            ld = solar_to_lunar(year, month, day)
            lunar_str = lunar_date_str(ld)
            # 获取农历日名称（只取日期部分，如"初一"）
            short_lunar = lunar_str.split("月")[1] if "月" in lunar_str else lunar_str
            festival = lunar_festival(ld) or solar_festival(month, day)
            lunar_cache[day] = (short_lunar, festival)

    # 填充行
    for week_idx, week in enumerate(month_days):
        row_cells = []
        for day_idx, day in enumerate(week):
            if day == 0:
                row_cells.append("")
                continue

            is_today = highlight_today and (
                year == today.year and month == today.month and day == today.day
            )
            is_weekend = day_idx >= 5  # 周六日

            # 构建单元格文本
            cell_lines = []

            # 公历日期
            solar_day_str = str(day)
            if is_today:
                solar_day_str = f"[bold black on bright_green] {day:2d} [/bold black on bright_green]"
            elif is_weekend:
                color = COLOR_SUNDAY if day_idx == 6 else COLOR_SATURDAY
                solar_day_str = f"[{color}]{day:2d}[/{color}]"
            else:
                solar_day_str = f" {day:2d} "

            cell_lines.append(solar_day_str)

            # 农历日期
            short_lunar, festival = lunar_cache.get(day, ("", None))
            if short_lunar:
                if short_lunar in ("初一", "十五"):
                    lunar_style = f"[bold bright_cyan]{short_lunar}[/bold bright_cyan]"
                else:
                    lunar_style = f"[dim]{short_lunar}[/dim]"
                cell_lines.append(lunar_style)

            # 节气高亮
            term_name = term_map.get(day)
            if term_name:
                cell_lines.append(f"[bold bright_cyan]╎{term_name}[/bold bright_cyan]")

            # 节日高亮
            if festival:
                cell_lines.append(f"[bold bright_yellow]●{festival}[/bold bright_yellow]")

            cell_text = "\n".join(cell_lines)
            row_cells.append(cell_text)

        table.add_row(*row_cells)

    return table


def render_year(
    year: int,
    highlight_today: bool = True,
) -> list[Table]:
    """渲染全年 12 个月"""
    tables = []
    for month in range(1, 13):
        tables.append(render_month(year, month, highlight_today))
    return tables


def print_month(year: int, month: int) -> None:
    """在终端打印单月日历"""
    table = render_month(year, month)
    console.print(table)
    _print_legend()


def print_year(year: int) -> None:
    """在终端打印全年日历（3 列 × 4 行布局）"""
    from rich.columns import Columns

    tables = render_year(year)

    # 分组，每行 3 个月
    for row_start in range(0, 12, 3):
        row_tables = tables[row_start:row_start + 3]
        console.print(Columns(row_tables, equal=True, expand=False))
        console.print()

    _print_legend()


def _print_legend() -> None:
    """打印图例"""
    legend = (
        "[dim]"
        "┃ [bright_green]绿底[/bright_green]=今天  "
        "[dim]初一/十五[/dim]=朔望  "
        "[bright_cyan]╎[/bright_cyan]=节气  "
        "[bright_yellow]●[/bright_yellow]=节日  "
        "[red]红[/red]/[blue]蓝[/blue]=周末"
        "[/dim]"
    )
    console.print(legend)
    console.print()


def print_current_month() -> None:
    """打印当前月份"""
    import datetime
    today = datetime.date.today()
    print_month(today.year, today.month)


# ─── 伊斯兰历 ──────────────────────────────────────────────

def render_islamic_month(year: int, month: int, highlight_today: bool = True) -> Table:
    from .islamic import gregorian_to_islamic, islamic_festival, islamic_month_special, ISLAMIC_MONTH_NAMES_CN
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    solar_terms = get_solar_terms_for_month(year, month)
    term_map: dict[int, str] = {t.day: t.name for t in solar_terms}
    import datetime as _dt
    today = _dt.date.today()
    hijri_year = gregorian_to_islamic(year, month, 1).year
    title = f"[bold yellow]{year}年 {month}月[/bold yellow]  [dim]伊斯兰历 {hijri_year} AH[/dim]"
    table = Table(title=title, box=SIMPLE_HEAVY, show_header=True, header_style=COLOR_WEEKDAY, title_justify="center", expand=False, padding=(1, 2))
    for i, wd in enumerate(["一","二","三","四","五","六","日"]):
        table.add_column(wd, justify="center", style=COLOR_SUNDAY if i==6 else (COLOR_SATURDAY if i==5 else ""), width=10)
    for week in month_days:
        row_cells = []
        for col_idx, day in enumerate(week):
            if day == 0: row_cells.append(""); continue
            is_today = highlight_today and (year==today.year and month==today.month and day==today.day)
            idate = gregorian_to_islamic(year, month, day)
            cell_lines = []
            if is_today: cell_lines.append(f"[bold black on bright_green] {day:2d} [/bold black on bright_green]")
            elif col_idx==6: cell_lines.append(f"[{COLOR_SUNDAY}]{day:2d}[/{COLOR_SUNDAY}]")
            elif col_idx==5: cell_lines.append(f"[{COLOR_SATURDAY}]{day:2d}[/{COLOR_SATURDAY}]")
            else: cell_lines.append(f" {day:2d} ")
            mname = ISLAMIC_MONTH_NAMES_CN[idate.month-1][:4]
            lunar_text = f"{mname}{idate.day}"
            if idate.day in (1,10,15): lunar_text = f"[bold bright_cyan]{lunar_text}[/bold bright_cyan]"
            else: lunar_text = f"[dim]{lunar_text}[/dim]"
            cell_lines.append(lunar_text)
            ifest = islamic_festival(idate)
            tname = term_map.get(day)
            if tname: cell_lines.append(f"[bold bright_cyan]╎{tname}[/bold bright_cyan]")
            if ifest: cell_lines.append(f"[bold bright_yellow]●{ifest}[/bold bright_yellow]")
            cell_text = "\n".join(cell_lines)
            row_cells.append(cell_text)
        table.add_row(*row_cells)
    return table

def print_islamic_month(year: int, month: int) -> None:
    console.print(render_islamic_month(year, month)); _print_islamic_legend()

def print_islamic_year(year: int) -> None:
    from rich.columns import Columns
    for i in range(0,12,3): console.print(Columns([render_islamic_month(year,m) for m in range(i+1,i+4)], equal=True, expand=False)); console.print()
    _print_islamic_legend()

def _print_islamic_legend():
    console.print("[dim]┃ [bright_green]绿底[/bright_green]=今天  [bright_cyan]1/10/15[/bright_cyan]=特殊日  [bright_cyan]╎[/bright_cyan]=节气  [bright_yellow]●[/bright_yellow]=节日[/dim]\n")


# ─── 日本和历 ──────────────────────────────────────────────

def render_japanese_month(year: int, month: int, highlight_today: bool = True) -> Table:
    from .japanese import gregorian_to_japanese, japanese_holiday, rokuyo_name, month_wareki_name
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    solar_terms = get_solar_terms_for_month(year, month)
    term_map: dict[int, str] = {t.day: t.name for t in solar_terms}
    import datetime as _dt
    today = _dt.date.today()
    jd_ref = gregorian_to_japanese(year, month, 15)
    wm = month_wareki_name(month)
    title = f"[bold yellow]{year}年 {month}月[/bold yellow]  [dim]{jd_ref.era_name}和历  {wm}[/dim]"
    table = Table(title=title, box=SIMPLE_HEAVY, show_header=True, header_style=COLOR_WEEKDAY, title_justify="center", expand=False, padding=(1, 2))
    for i, wd in enumerate(["一","二","三","四","五","六","日"]):
        table.add_column(wd, justify="center", style=COLOR_SUNDAY if i==6 else (COLOR_SATURDAY if i==5 else ""), width=10)
    for week in month_days:
        row_cells = []
        for col_idx, day in enumerate(week):
            if day == 0: row_cells.append(""); continue
            is_today = highlight_today and (year==today.year and month==today.month and day==today.day)
            jd = gregorian_to_japanese(year, month, day)
            cell_lines = []
            if is_today: cell_lines.append(f"[bold black on bright_green] {day:2d} [/bold black on bright_green]")
            elif col_idx==6: cell_lines.append(f"[{COLOR_SUNDAY}]{day:2d}[/{COLOR_SUNDAY}]")
            elif col_idx==5: cell_lines.append(f"[{COLOR_SATURDAY}]{day:2d}[/{COLOR_SATURDAY}]")
            else: cell_lines.append(f" {day:2d} ")
            era_text = jd.short_str()
            if jd.is_gannen: era_text = f"[bold bright_cyan]{era_text}[/bold bright_cyan]"
            else: era_text = f"[dim]{era_text}[/dim]"
            cell_lines.append(era_text)
            holiday = japanese_holiday(month, day)
            tname = term_map.get(day)
            if tname: cell_lines.append(f"[bold bright_cyan]╎{tname}[/bold bright_cyan]")
            if holiday: cell_lines.append(f"[bold bright_yellow]●{holiday}[/bold bright_yellow]")
            elif not tname:
                ry = rokuyo_name(_dt.date(year, month, day))
                cell_lines.append(f"[bold]{ry}[/bold]" if ry in ("大安","仏滅") else f"[dim]{ry}[/dim]")
            cell_text = "\n".join(cell_lines); row_cells.append(cell_text)
        table.add_row(*row_cells)
    return table

def print_japanese_month(year: int, month: int) -> None:
    console.print(render_japanese_month(year, month)); _print_japanese_legend()

def print_japanese_year(year: int) -> None:
    from rich.columns import Columns
    for i in range(0,12,3): console.print(Columns([render_japanese_month(year,m) for m in range(i+1,i+4)], equal=True, expand=False)); console.print()
    _print_japanese_legend()

def _print_japanese_legend():
    console.print("[dim]┃ [bright_green]绿底[/bright_green]=今天  [bright_cyan]元年[/bright_cyan]=年号起始  [bright_cyan]╎[/bright_cyan]=节气  [bright_yellow]●[/bright_yellow]=祝日  六曜=先勝/友引/先負/仏滅/大安/赤口[/dim]\n")


# ─── 佛历 ──────────────────────────────────────────────────

def render_buddhist_month(year: int, month: int, highlight_today: bool = True) -> Table:
    from .buddhist import gregorian_to_buddhist, thai_holiday, thai_month_name, thai_month_short
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    solar_terms = get_solar_terms_for_month(year, month)
    term_map: dict[int, str] = {t.day: t.name for t in solar_terms}
    import datetime as _dt
    today = _dt.date.today()
    bd = gregorian_to_buddhist(year, month, 15)
    tm = thai_month_name(month)
    title = f"[bold yellow]{year}年 {month}月[/bold yellow]  [dim]BE {bd.year}  {tm}[/dim]"
    table = Table(title=title, box=SIMPLE_HEAVY, show_header=True, header_style=COLOR_WEEKDAY, title_justify="center", expand=False, padding=(1, 2))
    for i, wd in enumerate(["一","二","三","四","五","六","日"]):
        table.add_column(wd, justify="center", style=COLOR_SUNDAY if i==6 else (COLOR_SATURDAY if i==5 else ""), width=10)
    for week in month_days:
        row_cells = []
        for col_idx, day in enumerate(week):
            if day == 0: row_cells.append(""); continue
            is_today = highlight_today and (year==today.year and month==today.month and day==today.day)
            bd = gregorian_to_buddhist(year, month, day)
            cell_lines = []
            if is_today: cell_lines.append(f"[bold black on bright_green] {day:2d} [/bold black on bright_green]")
            elif col_idx==6: cell_lines.append(f"[{COLOR_SUNDAY}]{day:2d}[/{COLOR_SUNDAY}]")
            elif col_idx==5: cell_lines.append(f"[{COLOR_SATURDAY}]{day:2d}[/{COLOR_SATURDAY}]")
            else: cell_lines.append(f" {day:2d} ")
            cell_lines.append(f"[dim]BE {bd.year}[/dim]")
            holiday = thai_holiday(month, day)
            tname = term_map.get(day)
            if tname: cell_lines.append(f"[bold bright_cyan]╎{tname}[/bold bright_cyan]")
            if holiday: cell_lines.append(f"[bold bright_yellow]●{holiday}[/bold bright_yellow]")
            cell_text = "\n".join(cell_lines); row_cells.append(cell_text)
        table.add_row(*row_cells)
    return table

def print_buddhist_month(year: int, month: int) -> None:
    console.print(render_buddhist_month(year, month)); _print_buddhist_legend()

def print_buddhist_year(year: int) -> None:
    from rich.columns import Columns
    for i in range(0,12,3): console.print(Columns([render_buddhist_month(year,m) for m in range(i+1,i+4)], equal=True, expand=False)); console.print()
    _print_buddhist_legend()

def _print_buddhist_legend():
    console.print("[dim]┃ [bright_green]绿底[/bright_green]=今天  [bright_cyan]╎[/bright_cyan]=节气  [bright_yellow]●[/bright_yellow]=泰国佛节  BE=พุทธศักราช[/dim]\n")
