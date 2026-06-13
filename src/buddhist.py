"""
佛历（佛教纪元）转换引擎
========================
主要用于泰国 / 老挝 / 柬埔寨 / 缅甸。
泰阳历: BE = CE + 543，月日与公历一致。
"""

import datetime
from dataclasses import dataclass
from typing import Optional


# ─── 佛教纪元 ──────────────────────────────────────────────

BUDDHIST_YEAR_OFFSET = 543  # 佛历 = 公历 + 543


@dataclass
class BuddhistDate:
    """佛历日期"""
    year: int           # 佛历年 (BE)
    month: int          # 月 (1-12)
    day: int            # 日
    gregorian_year: int  # 对应公历年

    def __str__(self) -> str:
        return f"BE {self.year}-{self.month:02d}-{self.day:02d}"

    def thai_str(self) -> str:
        """泰式表示：พ.ศ. 2569"""
        return f"พ.ศ. {self.year}"


# ─── 泰文月份名 ────────────────────────────────────────────

THAI_MONTH_NAMES = [
    "มกราคม",    # 1月  Makarakhom
    "กุมภาพันธ์", # 2月  Kumphaphan
    "มีนาคม",     # 3月  Minakhom
    "เมษายน",     # 4月  Mesayon
    "พฤษภาคม",   # 5月  Pruetsaphakhom
    "มิถุนายน",   # 6月  Mithunayon
    "กรกฎาคม",    # 7月  Karakadakhom
    "สิงหาคม",    # 8月  Singhakhom
    "กันยายน",    # 9月  Kanyayon
    "ตุลาคม",     # 10月 Tulakhom
    "พฤศจิกายน",  # 11月 Phruetsachikayon
    "ธันวาคม",    # 12月 Thanwakhom
]

THAI_MONTH_SHORT = [
    "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.",
    "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.",
    "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.",
]

THAI_MONTH_ROMANIZED = [
    "Makarakhom", "Kumphaphan", "Minakhom", "Mesayon",
    "Pruetsaphakhom", "Mithunayon", "Karakadakhom", "Singhakhom",
    "Kanyayon", "Tulakhom", "Phruetsachikayon", "Thanwakhom",
]


# ─── 泰国佛教节日（公历固定日期部分） ───────────────────────

THAI_BUDDHIST_HOLIDAYS: dict[tuple[int, int], str] = {
    (1, 1): "วันขึ้นปีใหม่ (新年)",
    (2, 14): "วันมาฆบูชา (万佛节)*",   # 农历正月十五，简化公历近似
    (4, 6): "วันจักรี (扎克里王朝纪念日)",
    (4, 13): "วันสงกรานต์ (宋干节/泼水节)",
    (4, 14): "วันสงกรานต์ (宋干节 第二日)",
    (4, 15): "วันสงกรานต์ (宋干节 第三日)",
    (5, 4): "วันฉัตรมงคล (加冕纪念日)",
    (6, 3): "วันเฉลิมพระชนมพรรษาสมเด็จพระนางเจ้าฯ (王后诞辰)",
    (7, 28): "วันเฉลิมพระชนมพรรษาพระบาทสมเด็จพระเจ้าอยู่หัว (国王诞辰)",
    (8, 12): "วันเฉลิมพระชนมพรรษาสมเด็จพระนางเจ้าฯ (王太后诞辰/母亲节)",
    (10, 13): "วันคล้ายวันสวรรคต (拉玛九世纪念日)",
    (10, 23): "วันปิยมหาราช (朱拉隆功纪念日)",
    (12, 5): "วันคล้ายวันพระราชสมภพ (父亲节/拉玛九世诞辰)",
    (12, 10): "วันรัฐธรรมนูญ (宪法日)",
    (12, 31): "วันสิ้นปี (除夕)",
}

# 泰国星期名
THAI_WEEKDAYS = [
    "วันจันทร์", "วันอังคาร", "วันพุธ",
    "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์",
]

THAI_WEEKDAYS_SHORT = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]


def gregorian_to_buddhist(year: int, month: int, day: int) -> BuddhistDate:
    """公历 → 佛历"""
    return BuddhistDate(
        year=year + BUDDHIST_YEAR_OFFSET,
        month=month,
        day=day,
        gregorian_year=year,
    )


def buddhist_to_gregorian(bd: BuddhistDate) -> tuple[int, int, int]:
    """佛历 → 公历"""
    return (bd.year - BUDDHIST_YEAR_OFFSET, bd.month, bd.day)


def thai_month_name(month: int) -> str:
    """获取月份的泰文名"""
    return THAI_MONTH_NAMES[month - 1]


def thai_month_short(month: int) -> str:
    """获取月份的泰文缩写"""
    return THAI_MONTH_SHORT[month - 1]


def thai_holiday(month: int, day: int) -> Optional[str]:
    """查询泰国佛教节日"""
    return THAI_BUDDHIST_HOLIDAYS.get((month, day))


def thai_weekday_name(weekday: int) -> str:
    """获取星期名（0=周一）"""
    return THAI_WEEKDAYS[weekday]
