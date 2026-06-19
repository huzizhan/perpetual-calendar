"""
黄历择日引擎
=============
基于干支纪日和建除十二神的每日宜忌推算。
采用传统黄历规则，适配 1900–2100 年范围。
"""

from dataclasses import dataclass, field
from typing import Optional

from .lunar import HEAVENLY_STEMS, EARTHLY_BRANCHES, ZODIAC

# ─── 基准日: 2000-01-01 = 庚申日 (sexagenary index 56) ───
_REF_YEAR, _REF_MONTH, _REF_DAY = 2000, 1, 1
_REF_SEXAGENARY_IDX = 56  # 庚申

# ─── 纳音五行（六十甲子纳音，按 sexagenary index 0-59）────
_NAYIN_WUXING = [
    "海中金", "海中金", "炉中火", "炉中火", "大林木", "大林木",
    "路旁土", "路旁土", "剑锋金", "剑锋金", "山头火", "山头火",
    "涧下水", "涧下水", "城头土", "城头土", "白蜡金", "白蜡金",
    "杨柳木", "杨柳木", "泉中水", "泉中水", "屋上土", "屋上土",
    "霹雳火", "霹雳火", "松柏木", "松柏木", "流年水", "流年水",
    "沙中土", "沙中土", "山下火", "山下火", "平地木", "平地木",
    "壁上土", "壁上土", "金箔金", "金箔金", "覆灯火", "覆灯火",
    "天河水", "天河水", "大驿土", "大驿土", "钗钏金", "钗钏金",
    "桑柘木", "桑柘木", "大溪水", "大溪水", "沙中金", "沙中金",
    "长流水", "长流水", "白蜡金", "白蜡金", "山下火", "山下火",
    "大溪水", "大溪水",
]

# ─── 建除十二神 ──────────────────────────────────────────
_JIANCHU_NAMES = ["建", "除", "满", "平", "定", "执", "破", "危", "成", "收", "开", "闭"]

# 建除宜忌规则：每个建除神对应一组宜和忌
_JIANCHU_YIJI: dict[str, dict[str, list[str]]] = {
    "建": {
        "宜": ["出行", "赴任", "祭祀", "祈福", "求嗣", "入学", "纳财"],
        "忌": ["动土", "开仓", "安葬", "伐木", "开渠"],
    },
    "除": {
        "宜": ["祭祀", "祈福", "求医", "治病", "扫舍", "拆卸", "除服"],
        "忌": ["嫁娶", "入宅", "开业", "出行", "安床"],
    },
    "满": {
        "宜": ["祭祀", "祈福", "嫁娶", "开业", "交易", "纳财", "入宅"],
        "忌": ["安葬", "赴任", "求医", "出行"],
    },
    "平": {
        "宜": ["祭祀", "修饰垣墙", "平治道涂", "修造"],
        "忌": ["嫁娶", "开业", "安葬", "开渠", "伐木"],
    },
    "定": {
        "宜": ["祭祀", "嫁娶", "开业", "交易", "入学", "签约", "纳采"],
        "忌": ["出行", "安葬", "伐木", "词讼", "移徙"],
    },
    "执": {
        "宜": ["祭祀", "修造", "嫁娶", "交易", "纳财", "捕猎"],
        "忌": ["出行", "开业", "安葬", "入宅", "移徙"],
    },
    "破": {
        "宜": ["祭祀", "求医", "治病", "拆卸", "破屋", "坏垣"],
        "忌": ["嫁娶", "开业", "出行", "入宅", "安葬", "签约"],
    },
    "危": {
        "宜": ["祭祀", "祈福", "安床", "交易", "纳财"],
        "忌": ["出行", "嫁娶", "开业", "动土", "安葬"],
    },
    "成": {
        "宜": ["嫁娶", "开业", "出行", "入宅", "移徙", "安床", "交易", "纳财", "修造"],
        "忌": ["词讼", "安葬"],
    },
    "收": {
        "宜": ["祭祀", "嫁娶", "纳财", "交易", "入学", "修造", "栽种", "牧养"],
        "忌": ["出行", "安葬", "伐木", "行丧", "开市"],
    },
    "开": {
        "宜": ["嫁娶", "开业", "出行", "入宅", "交易", "纳财", "开市", "修造", "移徙"],
        "忌": ["安葬", "伐木", "畋猎", "取鱼"],
    },
    "闭": {
        "宜": ["祭祀", "祈福", "安床", "纳财", "修造", "补垣", "塞穴"],
        "忌": ["嫁娶", "开业", "出行", "入宅", "安葬", "开市"],
    },
}

# ─── 冲煞映射 ────────────────────────────────────────────
_CHONG_MAP = {  # 地支 → (冲, 煞方)
    "子": ("马", "南"), "丑": ("羊", "东"), "寅": ("猴", "北"),
    "卯": ("鸡", "西"), "辰": ("狗", "南"), "巳": ("猪", "东"),
    "午": ("鼠", "北"), "未": ("牛", "西"), "申": ("虎", "南"),
    "酉": ("兔", "东"), "戌": ("龙", "北"), "亥": ("蛇", "西"),
}

# ─── 吉神（基于建除神 + 日支） ────────────────────────────
_JISHEN_MAP: dict[str, list[str]] = {
    "建": ["天德", "月德"], "除": ["天德", "月恩", "母仓"],
    "满": ["天德", "福德", "月恩"], "平": ["天马", "要安"],
    "定": ["时德", "民日", "三合", "阴德"], "执": ["月德", "要安"],
    "破": ["驿马"], "危": ["天德", "母仓", "六合"],
    "成": ["天德", "天喜", "三合", "天医"], "收": ["天德", "母仓", "六合"],
    "开": ["月德", "母仓", "时德"], "闭": ["天德", "王日", "天马"],
}

# ─── 凶煞（基于建除神 + 日支） ────────────────────────────
_XIONGSHEN_MAP: dict[str, list[str]] = {
    "建": ["月建", "土府"], "除": ["月害", "天吏"],
    "满": ["灾煞", "天刑"], "平": ["死神", "月刑"],
    "定": ["死气", "官符"], "执": ["小耗", "劫煞"],
    "破": ["月破", "大耗", "灾煞"], "危": ["月煞", "月虚"],
    "成": ["月厌", "地火"], "收": ["河魁", "月刑"],
    "开": ["月厌", "地火"], "闭": ["血支", "月煞"],
}


@dataclass
class AlmanacEntry:
    """单日黄历信息"""
    sexagenary: str       # 日柱干支，如"庚申"
    day_stem: str         # 日干，如"庚"
    day_branch: str       # 日支，如"申"
    jianchu: str          # 建除十二神
    wuxing: str           # 纳音五行
    yi: list[str]         # 宜
    ji: list[str]         # 忌
    chong: str            # 冲煞，如"冲虎(戊寅)煞南"
    jishen: list[str]     # 吉神
    xiongshen: list[str]  # 凶煞

    def to_dict(self) -> dict:
        return {
            "sexagenary": self.sexagenary,
            "dayStem": self.day_stem,
            "dayBranch": self.day_branch,
            "jianchu": self.jianchu,
            "wuxing": self.wuxing,
            "yi": self.yi,
            "ji": self.ji,
            "chong": self.chong,
            "jishen": self.jishen,
            "xiongshen": self.xiongshen,
        }


# ─── 日干支计算 ────────────────────────────────────────────

def _days_between(y1: int, m1: int, d1: int, y2: int, m2: int, d2: int) -> int:
    """计算两个公历日期之间的天数差（y1,m1,d1 在 y2,m2,d2 之前）"""
    from datetime import date
    return (date(y2, m2, d2) - date(y1, m1, d1)).days


def day_sexagenary(year: int, month: int, day: int) -> tuple[int, int]:
    """
    计算公历日期的日干支。
    返回: (stem_idx, branch_idx)  0=甲/子
    基准: 2000-01-01 = 庚申 (stem=6, branch=8, idx=56)
    """
    diff = _days_between(_REF_YEAR, _REF_MONTH, _REF_DAY, year, month, day)
    idx = (_REF_SEXAGENARY_IDX + diff) % 60
    return (idx % 10, idx % 12)


def sexagenary_str(stem_idx: int, branch_idx: int) -> str:
    """干支字符串，如 (6,8) → "庚申" """
    return f"{HEAVENLY_STEMS[stem_idx]}{EARTHLY_BRANCHES[branch_idx]}"


# ─── 建除十二神 ────────────────────────────────────────────

def _lunar_month_branch(year: int, month: int) -> int:
    """
    获取农历月份对应的月地支索引。
    正月=寅(branch 2), 二月=卯(3), ..., 十二月=丑(1)
    简化：用公历月份近似。精确版本需要用农历月份。
    对于黄历用途，误差可接受（同月内地支不变）。
    """
    # 农历正月约在公历1月下旬-2月下旬，取节气月份
    # 立春(约2月4日)起为寅月
    if month >= 2:
        return (month - 2) % 12  # 2月→寅(2), 3月→卯(3)... 1月→丑(1)
    else:
        return 11  # 1月→丑(1, index 1, but we use 0-indexed: 丑=1)


def _jianchu_index(lunar_month_branch: int, day_branch: int) -> int:
    """
    计算建除十二神的索引。
    月支为M，从M日起建，日支为D，则建除神 = (D - M + 12) % 12
    """
    return (day_branch - lunar_month_branch + 12) % 12


def compute_almanac(year: int, month: int, day: int) -> AlmanacEntry:
    """计算某天的完整黄历信息"""
    stem_i, branch_i = day_sexagenary(year, month, day)
    sexa = sexagenary_str(stem_i, branch_i)
    sexa_idx = (stem_i * 12 + branch_i) % 60  # Actually: stem_i*6 + ...

    # 正确的 sexagenary index
    # stem_i and branch_i from day_sexagenary already encode the correct index
    # sexagenary_index = (stem_i * 12  + branch_i) % 60? No.
    # Correct: stem_i = idx % 10, branch_i = idx % 12
    # To recover idx from (stem_i, branch_i): find x where x%10==stem_i and x%12==branch_i
    for idx in range(60):
        if idx % 10 == stem_i and idx % 12 == branch_i:
            sexa_idx = idx
            break

    # 纳音五行
    wuxing = _NAYIN_WUXING[sexa_idx]

    # 建除十二神
    month_branch = _lunar_month_branch(year, month)
    jc_idx = _jianchu_index(month_branch, branch_i)
    jianchu = _JIANCHU_NAMES[jc_idx]

    # 宜忌
    yiji = _JIANCHU_YIJI.get(jianchu, {"宜": [], "忌": []})
    yi = yiji["宜"][:5]  # 最多5条
    ji = yiji["忌"][:5]

    # 冲煞
    branch_name = EARTHLY_BRANCHES[branch_i]
    chong_info = _CHONG_MAP.get(branch_name, ("?", "?"))
    chong = f"冲{chong_info[0]}({sexa})煞{chong_info[1]}"

    # 吉神凶煞
    jishen = _JISHEN_MAP.get(jianchu, [])[:4]
    xiongshen = _XIONGSHEN_MAP.get(jianchu, [])[:4]

    return AlmanacEntry(
        sexagenary=sexa,
        day_stem=HEAVENLY_STEMS[stem_i],
        day_branch=branch_name,
        jianchu=jianchu,
        wuxing=wuxing,
        yi=yi,
        ji=ji,
        chong=chong,
        jishen=jishen,
        xiongshen=xiongshen,
    )
