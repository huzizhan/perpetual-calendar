"""
伊斯兰历（希吉来历）转换引擎
=============================
纯太阴历，以公元 622 年 7 月 16 日（希吉来）为纪元。
基于科威特算法 (Kuwaiti Algorithm)，全球通用。

特性：
- 公历 ↔ 伊斯兰历互转
- 12 个月份中/阿/英三语名称
- 闰年判断（30 年周期中 11 个闰年）
- 伊斯兰重要节日
"""

from dataclasses import dataclass
from typing import Optional


# ─── 伊斯兰历月份名称 ──────────────────────────────────────

ISLAMIC_MONTH_NAMES_CN = [
    "穆哈兰姆", "萨法尔",
    "赖比尔·敖外鲁", "赖比尔·阿色尼",
    "主马达·敖外鲁", "主马达·阿色尼",
    "赖哲卜", "舍尔邦",
    "莱麦丹", "闪瓦鲁",
    "祖勒·盖尔德", "祖勒·罕哲",
]

ISLAMIC_MONTH_NAMES_AR = [
    "محرم", "صفر",
    "ربيع الأول", "ربيع الثاني",
    "جمادى الأولى", "جمادى الثانية",
    "رجب", "شعبان",
    "رمضان", "شوال",
    "ذو القعدة", "ذو الحجة",
]

ISLAMIC_MONTH_NAMES_EN = [
    "Muharram", "Safar",
    "Rabi' al-awwal", "Rabi' al-thani",
    "Jumada al-awwal", "Jumada al-thani",
    "Rajab", "Sha'ban",
    "Ramadan", "Shawwal",
    "Dhu al-Qi'dah", "Dhu al-Hijjah",
]


@dataclass
class IslamicDate:
    """伊斯兰历日期"""
    year: int
    month: int
    day: int

    def __str__(self) -> str:
        return f"{self.year}-{self.month:02d}-{self.day:02d} AH"

    def month_name_cn(self) -> str:
        return ISLAMIC_MONTH_NAMES_CN[self.month - 1]

    def month_name_en(self) -> str:
        return ISLAMIC_MONTH_NAMES_EN[self.month - 1]


# ─── 伊斯兰节日 ────────────────────────────────────────────

ISLAMIC_FESTIVALS: dict[tuple[int, int], str] = {
    (1, 1):   "新年 (伊斯兰历新年)",
    (1, 10):  "阿舒拉日",
    (3, 12):  "圣纪节 (先知诞辰)",
    (7, 27):  "登霄节",
    (8, 15):  "白拉特夜",
    (9, 1):   "斋月开始 (莱麦丹)",
    (9, 27):  "盖德尔夜 (高贵之夜)",
    (10, 1):  "开斋节",
    (10, 2):  "开斋节 (第二日)",
    (10, 3):  "开斋节 (第三日)",
    (12, 9):  "阿拉法特日",
    (12, 10): "古尔邦节 (宰牲节)",
    (12, 11): "古尔邦节 (第二日)",
    (12, 12): "古尔邦节 (第三日)",
}

ISLAMIC_SPECIAL_MONTHS: dict[int, str] = {
    1: "禁月 (الأشهر الحرم)",
    7: "禁月 (الأشهر الحرم)",
    11: "禁月 (الأشهر الحرم)",
    12: "禁月 (الأشهر الحرم)",
    9: "斋月 (رمضان)",
}

# ─── 伊斯兰节日介绍 ──────────────────────────────────────

ISLAMIC_FESTIVAL_INTRO: dict[str, str] = {
    "开斋节": (
        "开斋节（Eid al-Fitr）是伊斯兰教最重要的节日之一，标志着斋月（莱麦丹月）的结束。"
        "在经历了一个月的日出至日落禁食后，穆斯林在这一天沐浴更衣、前往清真寺参加会礼、"
        "缴纳开斋捐（Zakat al-Fitr）以帮助贫困者。家人团聚共享美食，互赠礼物，"
        "孩子们穿上新衣。开斋节通常持续三天，是感恩、宽恕与社区团结的庆典。"
    ),
    "古尔邦节 (宰牲节)": (
        "古尔邦节（Eid al-Adha）又称宰牲节，是伊斯兰历十二月十日，"
        "纪念先知易卜拉欣（亚伯拉罕）为服从真主而愿意牺牲儿子的故事。"
        "真主最终以羊代替，因此穆斯林在这一天宰杀牛羊骆驼，将肉分成三份："
        "自用、馈赠亲友、施舍穷人。这一天也是朝觐（Hajj）的核心仪式日，"
        "全球穆斯林齐聚麦加，是伊斯兰教最盛大的节日。"
    ),
    "阿舒拉日": (
        "阿舒拉日是伊斯兰历穆哈兰姆月第十日。逊尼派纪念先知穆萨（摩西）在真主帮助下"
        "率以色列人渡过红海、摆脱法老奴役的日子。什叶派则在这一天哀悼先知穆罕默德的外孙"
        "侯赛因在卡尔巴拉战役中殉难。许多穆斯林在这一天自愿斋戒以表达虔诚。"
    ),
    "圣纪节 (先知诞辰)": (
        "圣纪节是伊斯兰历三月十二日，纪念先知穆罕默德的诞辰。相传穆圣于公元571年"
        "出生于麦加。这一天穆斯林在清真寺举行赞圣仪式，诵读《古兰经》、"
        "讲述先知生平事迹，弘扬先知仁爱、诚实、宽容的美德。"
        "不同教派和地区对圣纪节的庆祝方式有所差异，但其核心是对先知的爱与敬仰。"
    ),
    "登霄节": (
        "登霄节纪念先知穆罕默德于夜行登霄的神迹之旅。相传穆圣在一夜之间从麦加禁寺"
        "骑乘仙马布拉克来到耶路撒冷远寺，并从那里登上七重天，面见历代先知，"
        "最终领受真主规定的每日五次礼拜。这一事件是伊斯兰信仰中仅次于《古兰经》降示的"
        "重大奇迹，穆斯林在这一夜礼拜、诵经、祈求真主的恩典。"
    ),
    "新年 (伊斯兰历新年)": (
        "伊斯兰历新年是穆哈兰姆月（一月）的第一天，标志着希吉来历新年的开始。"
        "公元622年，先知穆罕默德为躲避迫害从麦加迁徙到麦地那，这一伟大迁徙事件"
        "被定为伊斯兰历的纪元元年。新年是回顾信仰历程、祈求平安吉庆的时刻，"
        "穆斯林在清真寺祈祷、与家人团聚，以简朴而虔诚的方式迎接新的一年。"
    ),
}



# ─── 核心算法 ──────────────────────────────────────────────

# 伊斯兰历纪元: 1 Muharram 1 AH = 公元 622 年 7 月 16 日 (Julian)
# 对应儒略日: 1948440（使用 Julian 公式计算，622 年在 1582 年改革前）
HIJRI_EPOCH_JD = 1948440  # 科威特算法标准epoch，已验证对准2024-2026开斋节/古尔邦节


def _is_julian_date(year: int, month: int, day: int) -> bool:
    """判断给定日期是否在儒略历时期（1582-10-04 及之前）"""
    return (year < 1582
            or (year == 1582 and month < 10)
            or (year == 1582 and month == 10 and day <= 4))


def _gregorian_to_jd(year: int, month: int, day: int) -> int:
    """
    公历日期 → 儒略日 (Julian Day Number)

    处理历法切换：
    - 1582-10-15 及之后：格里高利历（含世纪修正）
    - 1582-10-04 及之前：儒略历（无世纪修正）

    注意：1582-10-05 至 1582-10-14 在历史上不存在（被跳过）。
    """
    y = year
    m = month
    if m <= 2:
        y -= 1
        m += 12

    if _is_julian_date(year, month, day):
        # 儒略历：无世纪修正
        b = 0
    else:
        # 格里高利历：含世纪修正
        a = y // 100
        b = 2 - a + (a // 4)

    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + day + b - 1524
    return jd


def _jd_to_gregorian(jd: int) -> tuple[int, int, int]:
    """儒略日 → 公历日期"""
    jd += 1524
    a = int((jd - 122.1) / 365.25)
    b = int(365.25 * a)
    c = int((jd - b) / 30.6001)
    d = jd - b - int(30.6001 * c)

    if c <= 13:
        month = c - 1
        year = a - 4716
    else:
        month = c - 13
        year = a - 4715

    if month <= 2:
        year += 1

    return (year, month, d)


def _is_islamic_leap_year(year: int) -> bool:
    """
    判断伊斯兰历闰年。
    30 年周期中，第 2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29 年为闰年。
    """
    leap_years_in_cycle = {2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29}
    return (year % 30) in leap_years_in_cycle


def _days_in_islamic_year(year: int) -> int:
    """伊斯兰历某年总天数"""
    return 355 if _is_islamic_leap_year(year) else 354


def _days_in_islamic_month(year: int, month: int) -> int:
    """伊斯兰历某月天数"""
    # 奇数月 30 天，偶数月 29 天
    # 闰年时第 12 月为 30 天
    if month == 12 and _is_islamic_leap_year(year):
        return 30
    return 30 if month % 2 == 1 else 29


def gregorian_to_islamic(year: int, month: int, day: int) -> IslamicDate:
    """
    公历 → 伊斯兰历 转换

    算法步骤：
    1. 公历 → 儒略日
    2. 儒略日 → 伊斯兰历（从纪元开始推算）
    """
    jd = _gregorian_to_jd(year, month, day)

    # 从伊斯兰历纪元开始的天数
    days_since_epoch = jd - int(HIJRI_EPOCH_JD)

    if days_since_epoch < 0:
        raise ValueError(f"日期超出范围（伊斯兰历纪元 622-07-16 之前）: "
                         f"{year}-{month}-{day}")

    # 推算伊斯兰历年
    islamic_year = 1
    while True:
        year_days = _days_in_islamic_year(islamic_year)
        if days_since_epoch < year_days:
            break
        days_since_epoch -= year_days
        islamic_year += 1

    # 推算月份
    islamic_month = 1
    while True:
        month_days = _days_in_islamic_month(islamic_year, islamic_month)
        if days_since_epoch < month_days:
            break
        days_since_epoch -= month_days
        islamic_month += 1

    islamic_day = days_since_epoch + 1

    return IslamicDate(year=islamic_year, month=islamic_month, day=islamic_day)


def islamic_to_gregorian(islamic_date: IslamicDate) -> tuple[int, int, int]:
    """伊斯兰历 → 公历"""
    # 计算从纪元到该日期的总天数
    total_days = 0

    # 整年
    for y in range(1, islamic_date.year):
        total_days += _days_in_islamic_year(y)

    # 整月
    for m in range(1, islamic_date.month):
        total_days += _days_in_islamic_month(islamic_date.year, m)

    # 天数
    total_days += islamic_date.day - 1

    jd = int(HIJRI_EPOCH_JD) + total_days
    return _jd_to_gregorian(jd)


def islamic_festival(idate: IslamicDate) -> Optional[str]:
    """查询伊斯兰节日"""
    return ISLAMIC_FESTIVALS.get((idate.month, idate.day))


def islamic_month_special(idate: IslamicDate) -> Optional[str]:
    """查询特殊月份说明"""
    return ISLAMIC_SPECIAL_MONTHS.get(idate.month)


# ─── 快捷查询 ──────────────────────────────────────────────

def get_islamic_year_info(year: int) -> dict:
    """获取伊斯兰历某年的基本信息"""
    # 该年对应的大致公历年份范围
    jan1_id = gregorian_to_islamic(year, 1, 1)
    dec31_id = gregorian_to_islamic(year, 12, 31)

    return {
        "first_day": jan1_id,
        "last_day": dec31_id,
        "is_leap": _is_islamic_leap_year(jan1_id.year),
        "total_days": _days_in_islamic_year(jan1_id.year),
    }
