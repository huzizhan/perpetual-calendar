"""
二十四节气计算
基于 2000 年基准日期 + 年度漂移修正，精度 ±1 天。
"""

from dataclasses import dataclass
from typing import Optional
import calendar as cal_module

# 节气顺序
SOLAR_TERMS_ORDER = [
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分",
    "清明", "谷雨", "立夏", "小满", "芒种", "夏至",
    "小暑", "大暑", "立秋", "处暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
]


@dataclass
class SolarTerm:
    """节气信息"""
    name: str
    month: int
    day: int


# 2000 年（闰年）各节气的 day-of-year（1月1日=1），基于天文年历
_BASE_DOY_2000 = [
    6,    # 小寒 1月6日
    21,   # 大寒 1月21日
    35,   # 立春 2月4日
    50,   # 雨水 2月19日
    65,   # 惊蛰 3月5日
    80,   # 春分 3月20日
    95,   # 清明 4月4日
    111,  # 谷雨 4月20日
    126,  # 立夏 5月5日
    142,  # 小满 5月21日
    157,  # 芒种 6月5日
    173,  # 夏至 6月21日
    189,  # 小暑 7月7日
    204,  # 大暑 7月22日
    220,  # 立秋 8月7日
    236,  # 处暑 8月23日
    251,  # 白露 9月7日
    267,  # 秋分 9月23日
    282,  # 寒露 10月8日
    297,  # 霜降 10月23日
    312,  # 立冬 11月7日
    327,  # 小雪 11月22日
    342,  # 大雪 12月7日
    356,  # 冬至 12月21日
]


def _is_leap(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _count_leap_years(from_year: int, to_year: int) -> int:
    """统计半开区间 [from_year, to_year) 中的闰年数"""
    if from_year > to_year:
        from_year, to_year = to_year, from_year
        sign = -1
    else:
        sign = 1
    count = 0
    for y in range(from_year, to_year):
        if _is_leap(y):
            count += 1
    return count * sign


def _compute_term_doy(year: int, term_index: int) -> float:
    """
    计算节气在给定年份的 day-of-year（浮点）。

    方法：以 2000 年的实际节气日期为基准，
    加上 (year - 2000) * 0.2422 的年度漂移，
    减去闰年多出的天数修正。
    """
    base_doy = _BASE_DOY_2000[term_index]

    # 年度漂移：回归年比公历年长 ~0.2422 天
    year_diff = year - 2000
    drift = year_diff * 0.2422

    # 闰年修正：2000-02-29 到 year-02-29 之间的闰日
    leap_adjust = _count_leap_years(2000, year)

    # 对于 1 月节气（term 0-1），year 年的节气取决于 year-1 的冬至
    # 修正：year_diff 和 leap_adjust 需要按比例分配
    # 简化：直接加漂移
    doy = base_doy + drift - leap_adjust

    # 处理跨年：doy 可能落在上一年或下一年
    max_doy = 366 if _is_leap(year) else 365
    while doy > max_doy:
        doy -= max_doy
    while doy < 1:
        doy += (366 if _is_leap(year - 1) else 365)

    return doy


def _doy_to_month_day(year: int, doy: float) -> tuple[int, int]:
    """将 day-of-year 转换为 (month, day)"""
    days_in_month = [
        31, 29 if cal_module.isleap(year) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
    ]
    doy_int = int(round(doy))
    max_doy = 366 if _is_leap(year) else 365
    doy_int = max(1, min(max_doy, doy_int))

    cumulative = 0
    for m, dim in enumerate(days_in_month, 1):
        if doy_int <= cumulative + dim:
            day = doy_int - cumulative
            return (m, day)
        cumulative += dim

    return (12, 31)


def get_solar_terms_for_month(year: int, month: int) -> list[SolarTerm]:
    """计算某年某月内的所有节气"""
    terms: list[SolarTerm] = []
    for term_idx, term_name in enumerate(SOLAR_TERMS_ORDER):
        doy = _compute_term_doy(year, term_idx)
        m, d = _doy_to_month_day(year, doy)
        if m == month:
            terms.append(SolarTerm(name=term_name, month=m, day=d))
    return terms


def get_solar_term_for_date(year: int, month: int, day: int) -> Optional[SolarTerm]:
    """查询某日期是否为节气日"""
    terms = get_solar_terms_for_month(year, month)
    for st in terms:
        if st.day == day:
            return st
    return None
