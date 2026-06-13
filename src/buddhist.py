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
    (1, 1): "新年 (วันขึ้นปีใหม่)",
    (2, 14): "万佛节 (มาฆบูชา)*",
    (4, 6): "扎克里日 (จักรี)",
    (4, 13): "宋干节/泼水节",
    (4, 14): "宋干节 第二日",
    (4, 15): "宋干节 第三日",
    (5, 4): "加冕日 (ฉัตรมงคล)",
    (6, 3): "王后诞辰",
    (7, 28): "国王诞辰",
    (8, 12): "母亲节/王太后诞辰",
    (10, 13): "拉玛九世纪念日",
    (10, 23): "朱拉隆功纪念日",
    (12, 5): "父亲节/拉玛九世诞辰",
    (12, 10): "宪法日 (รัฐธรรมนูญ)",
    (12, 31): "除夕 (สิ้นปี)",
}

# ─── 泰国佛教节日介绍 ──────────────────────────────────

BUDDHIST_FESTIVAL_INTRO: dict[str, str] = {
    "新年 (วันขึ้นปีใหม่)": (
        "泰国新年为公历1月1日，是全国性的法定假日。虽然泰国还有传统的宋干节（泼水节）"
        "作为泰历新年，但公历新年同样被广泛庆祝。曼谷的中央世界广场会举办盛大倒计时活动，"
        "寺庙敲钟祈福，人们相互赠送礼物、布施僧侣，以积德的方式迎接新的一年。"
    ),
    "宋干节/泼水节": (
        "宋干节（Songkran）是泰国最盛大的传统节日，每年4月13日至15日庆祝，"
        "标志着泰历新年的到来。节日源于古老的沐浴净身祈福仪式，如今演变为全民泼水狂欢。"
        "人们走上街头互相泼水祝福，象征洗去过去一年的不顺。除泼水外，"
        "泰国人还会前往寺庙布施、堆沙塔、向长辈行洒水礼以示尊敬，体现了泰国文化的独特魅力。"
    ),
    "宋干节 第二日": (
        "宋干节第二天被称为「家庭日」，这一天人们拜访长辈，行洒水礼祈求祝福。"
        "也会去寺庙聆听佛法、为佛像洒水沐浴（浴佛仪式）。"
        "各大寺庙香火鼎盛，人们用浸有花瓣的清水为佛像和僧侣洒水，"
        "并将沙粒运到寺庙堆成沙塔，寓意将过去一年无意中带走的佛寺沙土归还。"
    ),
    "宋干节 第三日": (
        "宋干节第三天也是泰国新年日，这一天举行更为盛大的庆祝和布施活动。"
        "年轻人为长辈行水滴礼，长辈则回赠祝福。人们相信这一天布施和行善能获得加倍的功德。"
        "各地举办选美比赛、花车巡游，在清迈还会举行「宋干小姐」游行，"
        "整个国家沉浸在欢乐祥和的气氛中，是了解泰国传统文化的绝佳窗口。"
    ),
    "国王诞辰": (
        "泰国国王诞辰（拉玛十世哇集拉隆功国王为7月28日）是泰国最庄严的国家庆典之一。"
        "这一天全国悬挂国王画像和国旗，民众身着黄色T恤（代表王室颜色）参加庆祝活动。"
        "夜晚在皇家田广场举行盛大烛光祈福仪式，数以万计的民众点燃蜡烛、齐唱国王颂歌，"
        "场面庄严而感人。这一天的庆祝体现了泰国人民对王室的深厚敬意。"
    ),
    "王后诞辰": (
        "6月3日是素提达王后诞辰，全国放假庆祝。泰国人民在这一天表达对王后的敬爱，"
        "各地政府机构和学校举行庆祝仪式，悬挂王后肖像。"
        "民众穿紫色衣服（象征王后的颜色）前往皇家公园或寺庙祈福，"
        "晚上举行烛光晚会。王后诞辰也是泰国彰显传统价值观和民族团结的重要时刻。"
    ),
    "万佛节 (มาฆบูชา)*": (
        "万佛节（Makha Bucha）是泰国最重要的佛教节日之一，"
        "纪念佛陀在世时1250位阿罗汉不约而同齐聚竹林精舍的奇迹时刻。"
        "佛陀借此机会宣说了佛教的核心教义「波罗提木叉教诫」。"
        "这一天泰国全国放假禁酒，信众清晨布施、下午在寺庙诵经、"
        "夜晚手持蜡烛绕寺巡行（巡烛礼），寂静庄严的烛光长龙令人动容。"
    ),
    "朱拉隆功纪念日": (
        "10月23日是拉玛五世朱拉隆功大帝（1868-1910）的逝世纪念日。"
        "朱拉隆功是泰国最受爱戴的君主之一，他废除奴隶制、推行近代化改革、"
        "创办现代教育体系、兴建铁路，被誉为「现代泰国之父」。"
        "这一天民众自发前往朱拉隆功骑马雕像献花致敬，全国降半旗志哀，"
        "学生和民众纷纷感念大帝为泰国带来的进步与变革。"
    ),
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
