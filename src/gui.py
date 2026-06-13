"""
万年历 GUI — 基于 tkinter 的可视化万年历
支持鼠标翻月、跳转、农历/节气/节日显示。
"""

import datetime
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

from .lunar import (
    solar_to_lunar,
    lunar_date_str,
    year_sexagenary,
    year_zodiac,
    lunar_festival,
    solar_festival,
    LUNAR_DAY_NAMES,
)
from .solar_terms import get_solar_terms_for_month


# ─── 颜色方案 ───────────────────────────────────────────────
COLOR_BG = "#1e1e2e"           # 主背景
COLOR_HEADER_BG = "#313244"    # 标题栏
COLOR_CELL_BG = "#2a2a3a"      # 日期单元格
COLOR_CELL_BG_ALT = "#222233"  # 隔行背景
COLOR_TEXT = "#cdd6f4"         # 主文字
COLOR_TEXT_DIM = "#6c7086"     # 次要文字
COLOR_TODAY_BG = "#89b4fa"     # 今天背景
COLOR_TODAY_TEXT = "#1e1e2e"   # 今天文字
COLOR_SUNDAY = "#f38ba8"       # 周日文字
COLOR_SATURDAY = "#89b4fa"     # 周六文字
COLOR_FESTIVAL = "#f9e2af"     # 节日文字
COLOR_SOLAR_TERM = "#94e2d5"   # 节气文字
COLOR_LUNAR = "#a6adc8"        # 农历文字
COLOR_LUNAR_SPECIAL = "#cba6f7"  # 初一/十五
COLOR_BTN_BG = "#45475a"
COLOR_BTN_ACTIVE = "#585b70"
COLOR_BTN_TEXT = "#cdd6f4"
COLOR_WEEKDAY_HEADER = "#89b4fa"

FONT_TITLE = ("Helvetica", 18, "bold")
FONT_MONTH = ("Helvetica", 14, "bold")
FONT_WEEKDAY = ("Helvetica", 11, "bold")
FONT_SOLAR = ("Helvetica", 13, "bold")
FONT_LUNAR = ("Helvetica", 9)
FONT_BTN = ("Helvetica", 11)
FONT_INFO = ("Helvetica", 10)


class PerpetualCalendarGUI:
    """万年历 GUI 主窗口"""

    def __init__(self, year: int | None = None, month: int | None = None):
        today = datetime.date.today()
        self.year = year or today.year
        self.month = month or today.month
        self.today = today

        # 窗口
        self.root = tk.Tk()
        self.root.title("万年历")
        self.root.geometry("720x620")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(True, True)
        self.root.minsize(600, 520)

        # 响应式缩放
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_weekday_bar()
        self._build_calendar_grid()
        self._build_footer()

        self._render()

        # 键盘绑定
        self.root.bind("<Left>", lambda e: self._prev_month())
        self.root.bind("<Right>", lambda e: self._next_month())
        self.root.bind("<Up>", lambda e: self._prev_year())
        self.root.bind("<Down>", lambda e: self._next_year())
        self.root.bind("<KeyPress-t>", lambda e: self._go_today())
        self.root.bind("<KeyPress-g>", lambda e: self._jump_dialog())

        self.root.mainloop()

    # ─── 构建 UI 部件 ──────────────────────────────────────

    def _build_header(self):
        """标题栏：年月、干支、导航按钮"""
        header = tk.Frame(self.root, bg=COLOR_HEADER_BG, padx=15, pady=12)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # 上月按钮
        self.btn_prev = tk.Button(
            header, text="◀ 上月", font=FONT_BTN,
            bg=COLOR_BTN_BG, fg=COLOR_BTN_TEXT,
            activebackground=COLOR_BTN_ACTIVE, activeforeground=COLOR_BTN_TEXT,
            relief="flat", cursor="hand2", padx=12, pady=4,
            command=self._prev_month,
        )
        self.btn_prev.grid(row=0, column=0, padx=(0, 10))

        # 年月标题
        self.lbl_title = tk.Label(
            header, text="", font=FONT_MONTH,
            bg=COLOR_HEADER_BG, fg=COLOR_TEXT,
        )
        self.lbl_title.grid(row=0, column=1)

        # 干支生肖
        self.lbl_sexagenary = tk.Label(
            header, text="", font=FONT_INFO,
            bg=COLOR_HEADER_BG, fg=COLOR_LUNAR_SPECIAL,
        )
        self.lbl_sexagenary.grid(row=0, column=2, padx=20)

        # 下月按钮
        self.btn_next = tk.Button(
            header, text="下月 ▶", font=FONT_BTN,
            bg=COLOR_BTN_BG, fg=COLOR_BTN_TEXT,
            activebackground=COLOR_BTN_ACTIVE, activeforeground=COLOR_BTN_TEXT,
            relief="flat", cursor="hand2", padx=12, pady=4,
            command=self._next_month,
        )
        self.btn_next.grid(row=0, column=3)

    def _build_weekday_bar(self):
        """星期标题栏"""
        bar = tk.Frame(self.root, bg=COLOR_BG, padx=10, pady=(8, 2))
        bar.grid(row=1, column=0, sticky="ew")
        for i in range(7):
            bar.grid_columnconfigure(i, weight=1, uniform="wd")

        weekdays = ["一", "二", "三", "四", "五", "六", "日"]
        for i, wd in enumerate(weekdays):
            color = COLOR_SUNDAY if i == 6 else (COLOR_SATURDAY if i == 5 else COLOR_WEEKDAY_HEADER)
            lbl = tk.Label(
                bar, text=wd, font=FONT_WEEKDAY,
                bg=COLOR_BG, fg=color, anchor="center",
            )
            lbl.grid(row=0, column=i, sticky="ew")

        # 分隔线
        sep = tk.Frame(self.root, height=2, bg=COLOR_HEADER_BG)
        sep.grid(row=2, column=0, sticky="ew", pady=(0, 4))

    def _build_calendar_grid(self):
        """日历格子容器"""
        self.grid_frame = tk.Frame(self.root, bg=COLOR_BG, padx=10, pady=4)
        self.grid_frame.grid(row=3, column=0, sticky="nsew")
        for i in range(7):
            self.grid_frame.grid_columnconfigure(i, weight=1, uniform="cd")
        for i in range(6):
            self.grid_frame.grid_rowconfigure(i, weight=1)

        # 预创建 42 个格子（6 行 × 7 列）
        self.cells: list[tk.Frame] = []
        self.cell_solar: list[tk.Label] = []
        self.cell_lunar: list[tk.Label] = []
        self.cell_tag: list[tk.Label] = []

        for row in range(6):
            for col in range(7):
                idx = row * 7 + col
                cell = tk.Frame(
                    self.grid_frame, bg=COLOR_CELL_BG,
                    relief="flat", bd=1,
                    highlightthickness=1, highlightbackground=COLOR_HEADER_BG,
                )
                cell.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
                cell.grid_rowconfigure(0, weight=1)
                cell.grid_rowconfigure(2, weight=1)
                cell.grid_columnconfigure(0, weight=1)

                # 公历日期
                solar_lbl = tk.Label(
                    cell, text="", font=FONT_SOLAR,
                    bg=COLOR_CELL_BG, fg=COLOR_TEXT, anchor="s",
                )
                solar_lbl.grid(row=0, column=0)

                # 农历日期
                lunar_lbl = tk.Label(
                    cell, text="", font=FONT_LUNAR,
                    bg=COLOR_CELL_BG, fg=COLOR_LUNAR, anchor="n",
                )
                lunar_lbl.grid(row=1, column=0)

                # 标签（节日/节气）
                tag_lbl = tk.Label(
                    cell, text="", font=("Helvetica", 8),
                    bg=COLOR_CELL_BG, fg=COLOR_FESTIVAL, anchor="n",
                )
                tag_lbl.grid(row=2, column=0)

                self.cells.append(cell)
                self.cell_solar.append(solar_lbl)
                self.cell_lunar.append(lunar_lbl)
                self.cell_tag.append(tag_lbl)

    def _build_footer(self):
        """底部工具栏"""
        footer = tk.Frame(self.root, bg=COLOR_HEADER_BG, padx=15, pady=10)
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        # 今天按钮
        btn_today = tk.Button(
            footer, text="📅 今天", font=FONT_BTN,
            bg=COLOR_BTN_BG, fg=COLOR_BTN_TEXT,
            activebackground=COLOR_BTN_ACTIVE, activeforeground=COLOR_BTN_TEXT,
            relief="flat", cursor="hand2", padx=14, pady=4,
            command=self._go_today,
        )
        btn_today.grid(row=0, column=0, padx=(0, 8))

        # 跳转按钮
        btn_jump = tk.Button(
            footer, text="🔍 跳转", font=FONT_BTN,
            bg=COLOR_BTN_BG, fg=COLOR_BTN_TEXT,
            activebackground=COLOR_BTN_ACTIVE, activeforeground=COLOR_BTN_TEXT,
            relief="flat", cursor="hand2", padx=14, pady=4,
            command=self._jump_dialog,
        )
        btn_jump.grid(row=0, column=1, padx=8)

        # 今年全年
        btn_year = tk.Button(
            footer, text="📆 今年全年", font=FONT_BTN,
            bg=COLOR_BTN_BG, fg=COLOR_BTN_TEXT,
            activebackground=COLOR_BTN_ACTIVE, activeforeground=COLOR_BTN_TEXT,
            relief="flat", cursor="hand2", padx=14, pady=4,
            command=self._show_annual_terminal,
        )
        btn_year.grid(row=0, column=2, padx=8)

        # 今日信息
        wd = "一二三四五六日"
        self.lbl_today = tk.Label(
            footer, text=f"今天: {self.today.year}年{self.today.month}月{self.today.day}日 星期{wd[self.today.weekday()]}",
            font=FONT_INFO, bg=COLOR_HEADER_BG, fg=COLOR_TEXT_DIM,
        )
        self.lbl_today.grid(row=0, column=3, sticky="e")

        # 快捷键提示
        tips = tk.Label(
            self.root, text="← → 翻月  ↑ ↓ 翻年  T 今天  G 跳转",
            font=("Helvetica", 9), bg=COLOR_BG, fg=COLOR_TEXT_DIM,
            pady=4,
        )
        tips.grid(row=5, column=0, sticky="ew")

    # ─── 日历渲染 ──────────────────────────────────────────

    def _render(self):
        """根据当前 year/month 渲染日历"""
        import calendar

        # 更新标题
        sexagenary = year_sexagenary(self.year)
        zodiac = year_zodiac(self.year)
        self.lbl_title.config(text=f"{self.year} 年  {self.month} 月")
        self.lbl_sexagenary.config(text=f"{sexagenary}{zodiac}年")

        # 获取日历矩阵（周一为第一列）
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(self.year, self.month)

        # 节气
        terms = get_solar_terms_for_month(self.year, self.month)
        term_map: dict[int, str] = {t.day: t.name for t in terms}

        # 行列转换为 6 行 × 7 列的 cell 索引
        for row_idx, week in enumerate(month_days):
            for col_idx, day in enumerate(week):
                idx = row_idx * 7 + col_idx
                cell = self.cells[idx]
                solar_lbl = self.cell_solar[idx]
                lunar_lbl = self.cell_lunar[idx]
                tag_lbl = self.cell_tag[idx]

                if day == 0:
                    # 空白格（上月/下月占位）
                    cell.configure(bg=COLOR_BG, highlightbackground=COLOR_BG)
                    solar_lbl.configure(text="", bg=COLOR_BG)
                    lunar_lbl.configure(text="", bg=COLOR_BG)
                    tag_lbl.configure(text="", bg=COLOR_BG)
                    continue

                is_today = (
                    self.year == self.today.year
                    and self.month == self.today.month
                    and day == self.today.day
                )
                is_weekend = col_idx >= 5

                # 单元格背景
                if is_today:
                    cell_bg = COLOR_TODAY_BG
                    highlight = COLOR_TODAY_BG
                elif is_weekend:
                    cell_bg = COLOR_CELL_BG_ALT
                    highlight = COLOR_HEADER_BG
                else:
                    cell_bg = COLOR_CELL_BG
                    highlight = COLOR_HEADER_BG

                cell.configure(bg=cell_bg, highlightbackground=highlight)

                # 公历日期颜色
                if is_today:
                    solar_color = COLOR_TODAY_TEXT
                    solar_font = ("Helvetica", 14, "bold")
                elif col_idx == 6:
                    solar_color = COLOR_SUNDAY
                    solar_font = FONT_SOLAR
                elif col_idx == 5:
                    solar_color = COLOR_SATURDAY
                    solar_font = FONT_SOLAR
                else:
                    solar_color = COLOR_TEXT
                    solar_font = FONT_SOLAR

                solar_lbl.configure(
                    text=str(day), font=solar_font,
                    bg=cell_bg, fg=solar_color,
                )

                # 农历日期
                ld = solar_to_lunar(self.year, self.month, day)
                day_name = LUNAR_DAY_NAMES[ld.day - 1]
                is_special_lunar = day_name in ("初一", "十五")

                if is_today:
                    lunar_color = COLOR_TODAY_TEXT
                elif is_special_lunar:
                    lunar_color = COLOR_LUNAR_SPECIAL
                else:
                    lunar_color = COLOR_LUNAR

                lunar_lbl.configure(
                    text=day_name, bg=cell_bg, fg=lunar_color,
                )

                # 节日 / 节气标签
                festival = lunar_festival(ld) or solar_festival(self.month, day)
                term = term_map.get(day)

                tags = []
                if term:
                    tags.append(("╎" + term, COLOR_SOLAR_TERM))
                if festival:
                    tags.append(("●" + festival, COLOR_FESTIVAL))

                tag_lbl.configure(text="", bg=cell_bg)
                if tags:
                    text = "  ".join(t[0] for t in tags)
                    tag_lbl.configure(text=text, bg=cell_bg, fg=tags[0][1])

    # ─── 导航方法 ──────────────────────────────────────────

    def _prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self._render()

    def _next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self._render()

    def _prev_year(self):
        self.year -= 1
        self._render()

    def _next_year(self):
        self.year += 1
        self._render()

    def _go_today(self):
        self.year = self.today.year
        self.month = self.today.month
        self._render()

    def _jump_dialog(self):
        """弹出跳转对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("跳转到")
        dialog.geometry("280x200")
        dialog.configure(bg=COLOR_HEADER_BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 280) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(
            dialog, text="跳转到指定年月", font=FONT_MONTH,
            bg=COLOR_HEADER_BG, fg=COLOR_TEXT,
        ).pack(pady=(16, 12))

        # 年份
        row_y = tk.Frame(dialog, bg=COLOR_HEADER_BG)
        row_y.pack(pady=4)
        tk.Label(row_y, text="年  ", font=FONT_BTN, bg=COLOR_HEADER_BG, fg=COLOR_TEXT).pack(side="left")
        entry_year = tk.Entry(row_y, font=FONT_BTN, width=8, justify="center",
                              bg=COLOR_CELL_BG, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
                              relief="flat")
        entry_year.insert(0, str(self.year))
        entry_year.pack(side="left")

        # 月份
        row_m = tk.Frame(dialog, bg=COLOR_HEADER_BG)
        row_m.pack(pady=4)
        tk.Label(row_m, text="月  ", font=FONT_BTN, bg=COLOR_HEADER_BG, fg=COLOR_TEXT).pack(side="left")
        entry_month = tk.Entry(row_m, font=FONT_BTN, width=8, justify="center",
                               bg=COLOR_CELL_BG, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
                               relief="flat")
        entry_month.insert(0, str(self.month))
        entry_month.pack(side="left")

        def do_jump():
            try:
                y = int(entry_year.get())
                m = int(entry_month.get())
                if 1900 <= y <= 2100 and 1 <= m <= 12:
                    self.year = y
                    self.month = m
                    self._render()
                    dialog.destroy()
                else:
                    messagebox.showwarning("范围错误", "年份: 1900–2100\n月份: 1–12")
            except ValueError:
                messagebox.showwarning("格式错误", "请输入有效的数字")

        btn_go = tk.Button(
            dialog, text="跳转", font=FONT_BTN,
            bg=COLOR_BTN_BG, fg=COLOR_BTN_TEXT,
            activebackground=COLOR_BTN_ACTIVE, activeforeground=COLOR_BTN_TEXT,
            relief="flat", cursor="hand2", padx=24, pady=4,
            command=do_jump,
        )
        btn_go.pack(pady=14)

        entry_year.focus_set()
        entry_year.bind("<Return>", lambda e: entry_month.focus_set())
        entry_month.bind("<Return>", lambda e: do_jump())

    def _show_annual_terminal(self):
        """在终端打印全年视图"""
        messagebox.showinfo(
            "全年视图",
            f"请在终端中运行: python main.py {self.year}"
        )


def run_gui(year: int | None = None, month: int | None = None):
    """启动 GUI"""
    PerpetualCalendarGUI(year=year, month=month)
