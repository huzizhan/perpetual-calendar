"""
日本和历（元号）转换引擎
========================
基于年号纪元：令和 / 平成 / 昭和 / 大正 / 明治
月份日期与公历一致，仅年份表达不同。
"""

import datetime
from dataclasses import dataclass
from typing import Optional


# ─── 年号定义（按时间倒序） ────────────────────────────────

@dataclass
class Era:
    """年号信息"""
    name: str           # 年号名（汉字）
    name_cn: str        # 中文称呼
    start_date: datetime.date  # 年号起始日期


ERAS: list[Era] = [
    Era("令和", "令和", datetime.date(2019, 5, 1)),
    Era("平成", "平成", datetime.date(1989, 1, 8)),
    Era("昭和", "昭和", datetime.date(1926, 12, 25)),
    Era("大正", "大正", datetime.date(1912, 7, 30)),
    Era("明治", "明治", datetime.date(1868, 10, 23)),
]


@dataclass
class JapaneseDate:
    """日本和历日期"""
    era_name: str       # 年号
    year: int           # 和历年 (元年=1)
    month: int          # 月 (1-12, 同公历)
    day: int            # 日 (同公历)
    gregorian_year: int  # 对应公历年
    is_gannen: bool = False  # 是否元年

    def __str__(self) -> str:
        y = "元" if self.is_gannen else str(self.year)
        return f"{self.era_name}{y}年{self.month}月{self.day}日"

    def short_str(self) -> str:
        """简短格式：令和8.6.13"""
        y = "元" if self.is_gannen else str(self.year)
        return f"{self.era_name}{y}.{self.month}.{self.day}"


# ─── 日本节日（公历固定日期） ───────────────────────────────

JAPANESE_HOLIDAYS: dict[tuple[int, int], str] = {
    (1, 1): "元日 (元旦)",
    (1, 13): "成人の日 (成人节)",  # 实际是1月第二个周一，简化处理
    (2, 11): "建国記念の日 (建国纪念日)",
    (2, 23): "天皇誕生日 (天皇诞辰)",
    (3, 20): "春分の日 (春分)",
    (4, 29): "昭和の日 (昭和之日)",
    (5, 3): "憲法記念日 (宪法纪念日)",
    (5, 4): "みどりの日 (绿之日)",
    (5, 5): "こどもの日 (儿童节)",
    (7, 22): "海の日 (海之日)",  # 实际是7月第三个周一
    (8, 11): "山の日 (山之日)",
    (9, 15): "敬老の日 (敬老日)",  # 实际是9月第三个周一
    (9, 23): "秋分の日 (秋分)",
    (10, 14): "スポーツの日 (体育之日)",  # 实际是10月第二个周一
    (11, 3): "文化の日 (文化之日)",
    (11, 23): "勤労感謝の日 (勤劳感谢日)",
}

# 月份和风名（旧称，装饰性展示）
JAPANESE_MONTH_NAMES = [
    "睦月", "如月", "弥生", "卯月", "皐月", "水無月",
    "文月", "葉月", "長月", "神無月", "霜月", "師走",
]

# 日本六曜（六辉——简单版，按日期循环）
ROKUYO = ["先勝", "友引", "先負", "仏滅", "大安", "赤口"]


def gregorian_to_japanese(year: int, month: int, day: int) -> JapaneseDate:
    """
    公历 → 日本和历 转换
    """
    target = datetime.date(year, month, day)

    for era in ERAS:
        if target >= era.start_date:
            era_year = year - era.start_date.year + 1
            is_gannen = (era_year == 1)

            # 检查是否在同一年号内（跨年号年份需要特殊处理）
            # 例如 1989年1月7日是昭和64年，1月8日是平成元年
            if era_year == 1 and target < era.start_date:
                continue  # 该年号尚未开始

            return JapaneseDate(
                era_name=era.name,
                year=era_year,
                month=month,
                day=day,
                gregorian_year=year,
                is_gannen=is_gannen,
            )

    # 明治之前的日期（罕见）
    return JapaneseDate(
        era_name="西暦", year=year, month=month, day=day,
        gregorian_year=year, is_gannen=False,
    )


def japanese_holiday(month: int, day: int) -> Optional[str]:
    """查询日本公历节日"""
    return JAPANESE_HOLIDAYS.get((month, day))


def rokuyo_name(gregorian_date: datetime.date) -> str:
    """六曜（六辉）：按月日简单循环"""
    m, d = gregorian_date.month, gregorian_date.day
    idx = (m + d) % 6
    return ROKUYO[idx]


def month_wareki_name(month: int) -> str:
    """月份的和风名称"""
    return JAPANESE_MONTH_NAMES[month - 1]
