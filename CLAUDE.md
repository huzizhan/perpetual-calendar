# CLAUDE.md — 万年历项目记忆文件

## 项目概述

多历法万年历系统，支持 **中国农历 / 伊斯兰历 / 日本和历 / 佛历** 四种历法。
提供 **Web 浏览器界面**（主推）、终端 Rich 渲染、终端 TUI 交互、GUI 图形界面四种展示方式。

## 运行方式

```bash
cd /Users/frank/tmp/perpetual-calendar
pip install -r requirements.txt   # rich + flask

python main.py                    # 终端当月（农历）
python main.py 2026 6             # 终端指定年月
python main.py --web              # Web 版（推荐，自动打开浏览器）
python main.py --web --port 5000  # 指定端口
python main.py --islamic 2026 6   # 终端伊斯兰历
python main.py --japanese 2026 6  # 终端日本和历
python main.py --buddhist 2026 6  # 终端佛历
python main.py -i                 # 终端交互模式
```

Web 服务启动后访问 `http://127.0.0.1:5000`，顶部四个按钮切换历法，键盘 1-4 也可切换。

## 项目结构

```
perpetual-calendar/
├── main.py              # 统一入口，参数解析，分发到各模式
├── config.yaml          # 全局配置（预留）
├── requirements.txt     # rich + flask
├── CLAUDE.md            # 本文件
├── README.md            # 用户文档
│
├── src/
│   ├── lunar.py         # 🔴 中国农历引擎（最核心，代码最多）
│   │   ├── LUNAR_YEAR_INFO    1900-2100年农历数据表（16位编码）
│   │   ├── solar_to_lunar()   公历→农历转换
│   │   ├── year_sexagenary()  干支纪年（1900=庚子年）
│   │   ├── year_zodiac()      生肖
│   │   ├── LUNAR_FESTIVALS    农历节日表
│   │   ├── SOLAR_FESTIVALS    公历节日表
│   │   ├── LUNAR_FESTIVAL_INTRO  9篇农历节日介绍（~100字/篇）
│   │   └── SOLAR_FESTIVAL_INTRO  7篇公历节日介绍
│   │
│   ├── solar_terms.py   # 🌞 二十四节气
│   │   └── _BASE_DOY_2000     2000年基准节气日期，年度漂移修正±1天
│   │
│   ├── islamic.py       # 🌙 伊斯兰历（希吉来历）
│   │   ├── gregorian_to_islamic()  公历→伊斯兰历
│   │   ├── ISLAMIC_FESTIVALS       伊斯兰节日
│   │   ├── ISLAMIC_FESTIVAL_INTRO  6篇节日介绍
│   │   └── _is_islamic_leap_year() 30年周期闰年判断
│   │
│   ├── japanese.py      # 🇯🇵 日本和历（元号）
│   │   ├── gregorian_to_japanese() 公历→和历（五朝年号）
│   │   ├── JAPANESE_HOLIDAYS       日本祝日
│   │   ├── JAPANESE_HOLIDAY_INTRO  7篇祝日介绍
│   │   ├── rokuyo_name()           六曜计算
│   │   └── month_wareki_name()     和风月名
│   │
│   ├── buddhist.py      # 🛕 佛历（泰国佛教纪元）
│   │   ├── gregorian_to_buddhist() BE=CE+543
│   │   ├── THAI_BUDDHIST_HOLIDAYS 泰国佛节
│   │   ├── BUDDHIST_FESTIVAL_INTRO 8篇节日介绍
│   │   └── THAI_MONTH_NAMES       泰文月份名
│   │
│   ├── webapp.py        # 🌐 Flask Web 应用（~500行，含内嵌HTML/CSS/JS）
│   │   ├── /                 主页
│   │   ├── /api/calendar?year=&month=&type=  API
│   │   └── type参数: chinese|islamic|japanese|buddhist
│   │
│   ├── renderer.py      # 🖥️ Rich 终端渲染（六种render函数）
│   ├── tui.py           # ⌨️ 终端交互模式（方向键导航）
│   └── gui.py           # 🪟 tkinter GUI（深色主题）
│
├── tests/               # 单元测试（4个文件）
├── scripts/             # 工具脚本
├── models/              # 模型权重目录（预留）
└── notebooks/           # Jupyter 实验
```

## Git 分支结构

```
main                  ← 基础版（仅农历）
├── islamic-calendar  ← +伊斯兰历
├── japanese-calendar ← +日本和历
├── buddhist-calendar ← +佛历
└── unified           ← 🎯 四历法统一版（当前开发分支，所有新功能在此）
```

**所有新功能在 `unified` 分支开发。**

## 关键设计决策

### 农历引擎 (lunar.py)
- **数据表编码**: 每年一个16位整数，bit 0-3=闰月月份，bit 4-15=12个月大小，bit 16=闰月大小
- **基准**: 1900-01-31 = 农历庚子年正月初一
- **干支**: 1900=庚子年，base_stem=6, base_branch=0
- **引号规范**: 节日介绍中的中文引号全部使用「」而非 "" 或 ""，否则 Python 字符串语法错误

### 伊斯兰历 (islamic.py)
- **算法**: 科威特算法 (Kuwaiti Algorithm)
- **儒略日计算**: 1582-10-04 及之前用儒略历公式（无世纪修正），之后用格里高利历公式
- **纪元**: 1 Muharram 1 AH = 622-07-16 (Julian)，JD = 1948440
- **30年闰年周期**: {2,5,7,10,13,16,18,21,24,26,29} 为闰年，Dhu al-Hijjah 加1天
- **精度**: ±1天

### 日本和历 (japanese.py)
- **五朝年号**: 明治(1868)/大正(1912)/昭和(1926)/平成(1989)/令和(2019)
- **边界处理**: 1989-01-07=昭和64年，1989-01-08=平成元年
- **元年表示**: is_gannen=True 时显示「元」而非「1」

### 佛历 (buddhist.py)
- **换算**: BE = CE + 543
- **月份**: 泰文全称+缩写，罗马化对照
- **格子显示**: 泰文缩写+日期（如 มิ.ย.13），避免每格重复BE年份

### Web 前端 (webapp.py)
- **CSS Grid**: `grid-template-rows: repeat(6, 1fr)` 强制六行等高，避免内容溢出导致行高不一
- **历法配色**: 农历=紫(#cba6f7) / 伊斯兰=橙(#fab387) / 和历=粉(#f38ba8) / 佛历=金(#f9e2af)
- **节日面板**: 日历下方自动展示，多月节日有切换按钮，点击格子自动跳转对应节日
- **API字段**: 每格可带 `festivalName` 实现点击跳转
- **键盘快捷键**: 1-4切历法，←→翻月，↑↓翻年，T今天，G跳转

## 已知注意事项

1. `python -c` 测试需要 `cd` 到项目根目录，否则 `from src.xxx` 找不到模块
2. Web 服务用 `nohup python main.py --web --port 5000 > /tmp/calendar-server.log 2>&1 &` 启动可持久化
3. 端口占用时用 `lsof -ti:5000 | xargs kill -9` 清理
4. 节气精度±1天（日常使用足够）
5. 伊斯兰历精度±1天（计算历法 vs 实际观月差异）
6. 日本祝日中的「成人の日」「海の日」「敬老の日」「スポーツの日」实际是浮动周一，当前简化处理为固定日期
7. 农历数据表覆盖 1900-2100 年，超出范围需扩展数据
8. 不要使用中文引号 "" 在 Python 字符串内，用「」替代

## 最新进度 (2026-06-19)

- 农历数据修复: bit 映射 `(16-month)` 替换 `(3+month)`，5处数据错误修正，100/100 vs lunardate
- 黄历引擎: 日干支/建除十二神/宜忌/冲煞/吉神凶煞/纳音五行
- PWA: manifest + Service Worker (v1.0.0) + 图标生成 + 离线页面
- 伊斯兰历: epoch=1948440，±1天（科威特算法 vs 实际观月差异，合理）
- 日本和历/佛历: 全部验证通过
- 服务端口: 8090（8080=code-server, 5000=AirPlay占用）

## 后续方向

- [ ] 希伯来历（默冬周期19年7闰）
- [ ] 波斯太阳历（春分岁首）
- [ ] 导出日历图片/PDF
- [ ] iCal/ICS 订阅生成
- [ ] 农历生日提醒
- [ ] 节气精确到时辰
- [ ] 日本祝日浮动日期精确化
- [ ] 多语言界面（英/日/泰/阿）
- [ ] HTTPS 部署 + 域名
- [ ] AdMob 广告接入
- [ ] 用户系统 + 云同步
