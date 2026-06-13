"""
农历转换引擎
-----------------
内嵌 1900–2100 年农历数据，支持：
- 公历 ↔ 农历互转
- 天干地支 / 生肖 / 节气
- 传统节日
"""

from dataclasses import dataclass
from typing import Optional

# ============================================================
# 农历年数据表 (1900–2100)，共 201 年
# 每一年用一个 16 位整数编码：
#   bit 0-3   : 闰月月份（0 = 无闰月）
#   bit 4-15  : 月份 1-12 的大小月（1=30天, 0=29天）
#               bit 4 → 正月, bit 5 → 二月, ...
#   bit 16    : 闰月大小（1=30天, 0=29天）
# ============================================================
LUNAR_YEAR_INFO = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950,  # 1900–1905
    0x16554, 0x056a0, 0x09ad0, 0x055d2, 0x04ae0, 0x0a5b6,  # 1906–1911
    0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2,  # 1912–1917
    0x095b0, 0x14977, 0x04970, 0x0a4b0, 0x0b4b5, 0x06a50,  # 1918–1923
    0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,  # 1924–1929
    0x06566, 0x0d4a0, 0x0ea50, 0x16a95, 0x05ad0, 0x02b60,  # 1930–1935
    0x186e3, 0x092e0, 0x1c8d7, 0x0c950, 0x0d4a0, 0x1d8a6,  # 1936–1941
    0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2,  # 1942–1947
    0x0a950, 0x0b557, 0x06ca0, 0x0b550, 0x15355, 0x04da0,  # 1948–1953
    0x0a5b0, 0x14573, 0x052b0, 0x0a9a8, 0x0e950, 0x06aa0,  # 1954–1959
    0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260,  # 1960–1965
    0x0f263, 0x0d950, 0x05b57, 0x056a0, 0x096d0, 0x04dd5,  # 1966–1971
    0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540,  # 1972–1977
    0x0b6a0, 0x195a6, 0x095b0, 0x049b0, 0x0a974, 0x0a4b0,  # 1978–1983
    0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,  # 1984–1989
    0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58,  # 1990–1995
    0x05ac0, 0x0ab60, 0x096d5, 0x092e0, 0x0c960, 0x0d954,  # 1996–2001
    0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0,  # 2002–2007
    0x092d0, 0x0cab5, 0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50,  # 2008–2013
    0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,  # 2014–2019
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6,  # 2020–2025
    0x0a4e0, 0x0d260, 0x0ea65, 0x0d530, 0x05aa0, 0x076a3,  # 2026–2031
    0x096d0, 0x04afb, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250,  # 2032–2037
    0x0d520, 0x0dd45, 0x0b5a0, 0x056d0, 0x055b2, 0x049b0,  # 2038–2043
    0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,  # 2044–2049
    0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6,  # 2050–2055
    0x0ea50, 0x06b20, 0x1a6c4, 0x0aae0, 0x092e0, 0x0d2e3,  # 2056–2061
    0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0,  # 2062–2067
    0x0a6d0, 0x055d4, 0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0,  # 2068–2073
    0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,  # 2074–2079
    0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55,  # 2080–2085
    0x04b60, 0x0a570, 0x054e4, 0x0d160, 0x0e968, 0x0d520,  # 2086–2091
    0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a4d0,  # 2092–2097
    0x0d150, 0x0f252, 0x0d520,                          # 2098–2100
]

# 公历月份天数（非闰年）
SOLAR_MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# 天干地支
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ZODIAC = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

# 农历月份名称
LUNAR_MONTH_NAMES = [
    "正", "二", "三", "四", "五", "六",
    "七", "八", "九", "十", "冬", "腊",
]
LUNAR_DAY_NAMES = [
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十",
]

# 节气名称
SOLAR_TERM_NAMES = [
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分",
    "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
    "小暑", "大暑", "立秋", "处暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
]

# 中国传统节日（农历）
LUNAR_FESTIVALS = {
    (1, 1): "春节",
    (1, 15): "元宵节",
    (2, 2): "龙抬头",
    (5, 5): "端午节",
    (7, 7): "七夕",
    (7, 15): "中元节",
    (8, 15): "中秋节",
    (9, 9): "重阳节",
    (10, 15): "下元节",
    (12, 8): "腊八节",
    (12, 23): "小年(北)",
    (12, 24): "小年(南)",
    (12, 30): "除夕",
}

# 公历节日
SOLAR_FESTIVALS = {
    (1, 1): "元旦",
    (2, 14): "情人节",
    (3, 8): "妇女节",
    (3, 12): "植树节",
    (4, 1): "愚人节",
    (5, 1): "劳动节",
    (5, 4): "青年节",
    (6, 1): "儿童节",
    (7, 1): "建党节",
    (8, 1): "建军节",
    (9, 10): "教师节",
    (10, 1): "国庆节",
    (12, 25): "圣诞节",
}


@dataclass
class LunarDate:
    """农历日期"""
    year: int
    month: int
    day: int
    is_leap: bool = False  # 是否闰月


def _is_leap_year(year: int) -> bool:
    """判断公历闰年"""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _solar_days_in_year(year: int) -> int:
    """公历某年总天数"""
    return 366 if _is_leap_year(year) else 365


def _solar_days_in_month(year: int, month: int) -> int:
    """公历某月天数"""
    if month == 2 and _is_leap_year(year):
        return 29
    return SOLAR_MONTH_DAYS[month - 1]


def _lunar_year_days(lunar_year: int) -> int:
    """农历某年总天数"""
    info = LUNAR_YEAR_INFO[lunar_year - 1900]
    days = 0
    # 每月天数
    for i in range(4, 16):
        days += 30 if (info >> i) & 1 else 29
    # 闰月天数
    leap_month = info & 0xf
    if leap_month:
        days += 30 if (info >> 16) & 1 else 29
    return days


def _lunar_leap_month(lunar_year: int) -> int:
    """农历某年闰月月份（0 = 无闰月）"""
    return LUNAR_YEAR_INFO[lunar_year - 1900] & 0xf


def _lunar_month_days(lunar_year: int, lunar_month: int, is_leap: bool = False) -> int:
    """农历某月天数"""
    info = LUNAR_YEAR_INFO[lunar_year - 1900]
    leap_month = info & 0xf
    if is_leap and lunar_month == leap_month:
        return 30 if (info >> 16) & 1 else 29
    return 30 if (info >> (3 + lunar_month)) & 1 else 29


def solar_to_lunar(year: int, month: int, day: int) -> LunarDate:
    """
    公历 → 农历 转换
    算法：从 1900-01-31（农历庚子年正月初一）作为基准点，计算天数差。
    """
    # 1900-01-31 = 农历 1900 年正月初一
    base_solar = _days_from_1900_01_31(1900, 1, 31)
    target_solar = _days_from_1900_01_31(year, month, day)
    offset = target_solar - base_solar

    if offset < 0:
        raise ValueError(f"日期超出范围: {year}-{month}-{day}（最早 1900-01-31）")

    # 在农历年中推进
    lunar_year = 1900
    while lunar_year <= 2100:
        year_days = _lunar_year_days(lunar_year)
        if offset < year_days:
            break
        offset -= year_days
        lunar_year += 1

    if lunar_year > 2100:
        raise ValueError(f"日期超出范围: {year}-{month}-{day}")

    # 在月份中推进
    leap_month = _lunar_leap_month(lunar_year)
    lunar_month = 1
    is_leap = False

    for m in range(1, 13):
        # 当月天数
        month_days = _lunar_month_days(lunar_year, m, False)
        if offset < month_days:
            lunar_month = m
            is_leap = False
            break
        offset -= month_days

        # 闰月
        if leap_month == m:
            leap_days = _lunar_month_days(lunar_year, m, True)
            if offset < leap_days:
                lunar_month = m
                is_leap = True
                break
            offset -= leap_days

    lunar_day = offset + 1
    return LunarDate(year=lunar_year, month=lunar_month, day=lunar_day, is_leap=is_leap)


def _days_from_1900_01_31(year: int, month: int, day: int) -> int:
    """计算公历日期距离 1900-01-31 的天数"""
    days = 0
    for y in range(1900, year):
        days += _solar_days_in_year(y)
    for m in range(1, month):
        days += _solar_days_in_month(year, m)
    days += day
    return days


def lunar_date_str(ld: LunarDate) -> str:
    """格式化农历日期为中文"""
    leap_prefix = "闰" if ld.is_leap else ""
    month_name = LUNAR_MONTH_NAMES[ld.month - 1]
    day_name = LUNAR_DAY_NAMES[ld.day - 1]
    return f"{leap_prefix}{month_name}月{day_name}"


def year_sexagenary(year: int) -> str:
    """年份的干支纪年（1900 = 庚子年）"""
    base_year = 1900
    base_stem = 6   # 庚
    base_branch = 0  # 子
    offset = year - base_year
    stem = HEAVENLY_STEMS[(base_stem + offset) % 10]
    branch = EARTHLY_BRANCHES[(base_branch + offset) % 12]
    return f"{stem}{branch}"


def year_zodiac(year: int) -> str:
    """年份的生肖（1900 = 鼠年 = 子）"""
    base_year = 1900
    base_branch = 0  # 子 = 鼠
    offset = year - base_year
    return ZODIAC[(base_branch + offset) % 12]


def lunar_festival(ld: LunarDate) -> Optional[str]:
    """查询农历节日"""
    if not ld.is_leap:
        return LUNAR_FESTIVALS.get((ld.month, ld.day))
    return None


def solar_festival(month: int, day: int) -> Optional[str]:
    """查询公历节日"""
    return SOLAR_FESTIVALS.get((month, day))
