"""
万年历 Web 版 — Flask 后端 + 内嵌 HTML/CSS/JS
在浏览器中查看交互式万年历。
"""

import calendar as cal_module
import datetime
import json
import logging

from flask import Flask, request, jsonify, render_template_string

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

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ─── HTML 页面（内嵌模板） ──────────────────────────────────

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>万年历</title>
<style>
  :root {
    --bg: #1e1e2e;
    --surface: #2a2a3a;
    --header-bg: #313244;
    --text: #cdd6f4;
    --text-dim: #6c7086;
    --accent: #89b4fa;
    --accent2: #cba6f7;
    --red: #f38ba8;
    --yellow: #f9e2af;
    --green: #a6e3a1;
    --teal: #94e2d5;
    --radius: 10px;
    --transition: 0.2s ease;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                 "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
  }

  .container {
    width: 100%;
    max-width: 780px;
    background: var(--surface);
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    overflow: hidden;
  }

  /* ── 顶部标题栏 ── */
  .header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 20px 24px 12px;
    background: var(--header-bg);
  }

  .nav-btn {
    width: 40px; height: 40px;
    border: none; border-radius: 50%;
    background: rgba(255,255,255,0.08);
    color: var(--text);
    font-size: 18px;
    cursor: pointer;
    transition: var(--transition);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .nav-btn:hover { background: rgba(255,255,255,0.18); transform: scale(1.05); }
  .nav-btn:active { transform: scale(0.95); }

  .title-group { text-align: center; }
  .title-group .ym {
    font-size: 24px; font-weight: 700; color: var(--text);
    letter-spacing: 2px;
  }
  .title-group .gz {
    font-size: 14px; color: var(--accent2); margin-top: 3px;
  }

  /* ── 快捷按钮 ── */
  .quick-bar {
    display: flex; justify-content: center; gap: 10px;
    padding: 8px 24px 16px;
    background: var(--header-bg);
  }
  .quick-btn {
    padding: 6px 16px;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    background: transparent;
    color: var(--text-dim);
    font-size: 13px;
    cursor: pointer;
    transition: var(--transition);
  }
  .quick-btn:hover { color: var(--text); border-color: rgba(255,255,255,0.3); }

  /* ── 星期标题 ── */
  .weekdays {
    display: grid; grid-template-columns: repeat(7, 1fr);
    padding: 10px 20px 4px;
    font-size: 13px; font-weight: 600;
    text-align: center; color: var(--text-dim);
  }
  .weekdays span:nth-child(7) { color: var(--red); }
  .weekdays span:nth-child(6) { color: var(--accent); }

  /* ── 日历网格 ── */
  .grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 3px; padding: 4px 14px 18px;
  }

  .cell {
    aspect-ratio: 1;
    border-radius: var(--radius);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    cursor: pointer; transition: var(--transition);
    position: relative; min-height: 72px;
    background: var(--bg);
  }
  .cell:hover { background: rgba(255,255,255,0.06); }
  .cell.empty { background: transparent; cursor: default; }
  .cell.empty:hover { background: transparent; }

  .cell .solar {
    font-size: 18px; font-weight: 600; color: var(--text);
    line-height: 1.3;
  }
  .cell .lunar {
    font-size: 12px; color: var(--text-dim);
    line-height: 1.3;
  }
  .cell .lunar.special { color: var(--accent2); font-weight: 600; }
  .cell .tag {
    font-size: 10px; margin-top: 1px;
    white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis; max-width: 90%;
  }
  .cell .tag.term { color: var(--teal); }
  .cell .tag.festival { color: var(--yellow); }

  /* 周末列 */
  .cell.sunday .solar { color: var(--red); }
  .cell.saturday .solar { color: var(--accent); }

  /* 今天 */
  .cell.today {
    background: var(--accent) !important;
    box-shadow: 0 4px 16px rgba(137, 180, 250, 0.4);
  }
  .cell.today .solar { color: #1e1e2e; font-weight: 800; }
  .cell.today .lunar { color: #1e1e2e; }
  .cell.today .lunar.special { color: #1e1e2e; }
  .cell.today .tag { color: #1e1e2e; }
  .cell.today .tag.term,
  .cell.today .tag.festival { color: #1e1e2e; }

  /* ── 底部 ── */
  .footer {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 24px; background: var(--header-bg);
    font-size: 13px; color: var(--text-dim);
  }
  .footer .today-info { font-weight: 500; color: var(--text); }
  .footer .hint { font-size: 12px; }

  /* ── 响应式 ── */
  @media (max-width: 520px) {
    .grid { gap: 2px; padding: 2px 6px 12px; }
    .cell { min-height: 50px; border-radius: 8px; }
    .cell .solar { font-size: 15px; }
    .cell .lunar { font-size: 10px; }
    .title-group .ym { font-size: 20px; }
  }

  /* ── 加载动画 ── */
  .loading { opacity: 0.5; pointer-events: none; transition: opacity 0.15s; }
</style>
</head>
<body>
<div class="container">
  <!-- 标题栏 -->
  <div class="header">
    <button class="nav-btn" onclick="prevMonth()" title="上月 (←)">◀</button>
    <button class="nav-btn" onclick="prevYear()" title="上年 (↑)">▲</button>
    <div class="title-group">
      <div class="ym" id="title-ym">2026 年  6 月</div>
      <div class="gz" id="title-gz">丙午马年</div>
    </div>
    <button class="nav-btn" onclick="nextYear()" title="下年 (↓)">▼</button>
    <button class="nav-btn" onclick="nextMonth()" title="下月 (→)">▶</button>
  </div>

  <!-- 快捷按钮 -->
  <div class="quick-bar">
    <button class="quick-btn" onclick="goToday()">📅 今天</button>
    <button class="quick-btn" onclick="jumpDialog()">🔍 跳转</button>
  </div>

  <!-- 星期 -->
  <div class="weekdays">
    <span>一</span><span>二</span><span>三</span><span>四</span>
    <span>五</span><span>六</span><span>日</span>
  </div>

  <!-- 日历网格 -->
  <div class="grid" id="calendar-grid"></div>

  <!-- 底部 -->
  <div class="footer">
    <span class="hint">←→ 翻月  ↑↓ 翻年  T 今天  G 跳转</span>
    <span class="today-info" id="today-info"></span>
  </div>

  <!-- 跳转对话框 -->
  <dialog id="jump-dialog" style="
    border:none; border-radius:16px; padding:28px 32px;
    background:var(--header-bg); color:var(--text);
    box-shadow:0 20px 60px rgba(0,0,0,0.5);
    min-width:260px;
  ">
    <div style="font-size:18px;font-weight:700;margin-bottom:16px;text-align:center;">跳转到</div>
    <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px;">
      <label style="width:24px;">年</label>
      <input id="jump-year" type="number" min="1900" max="2100"
             style="flex:1;padding:8px 12px;border-radius:8px;border:1px solid rgba(255,255,255,0.2);
                    background:var(--bg);color:var(--text);font-size:15px;text-align:center;">
    </div>
    <div style="display:flex;gap:10px;align-items:center;margin-bottom:16px;">
      <label style="width:24px;">月</label>
      <input id="jump-month" type="number" min="1" max="12"
             style="flex:1;padding:8px 12px;border-radius:8px;border:1px solid rgba(255,255,255,0.2);
                    background:var(--bg);color:var(--text);font-size:15px;text-align:center;">
    </div>
    <div style="display:flex;gap:10px;justify-content:flex-end;">
      <button onclick="closeJump()" style="padding:8px 20px;border-radius:8px;border:1px solid rgba(255,255,255,0.2);
               background:transparent;color:var(--text);cursor:pointer;">取消</button>
      <button onclick="doJump()" style="padding:8px 20px;border-radius:8px;border:none;
               background:var(--accent);color:#1e1e2e;font-weight:600;cursor:pointer;">跳转</button>
    </div>
  </dialog>
</div>

<script>
  // ── 状态 ──
  let currentYear = {{ year }};
  let currentMonth = {{ month }};
  const todayStr = "{{ today }}";  // "2026-06-13"
  const today = new Date(todayStr);
  const WEEKDAYS = ["一","二","三","四","五","六","日"];

  // ── 日历加载 ──
  async function loadCalendar() {
    const grid = document.getElementById("calendar-grid");
    grid.classList.add("loading");

    const resp = await fetch(`/api/calendar?year=${currentYear}&month=${currentMonth}`);
    const data = await resp.json();

    document.getElementById("title-ym").textContent =
      `${data.year} 年  ${data.month} 月`;
    document.getElementById("title-gz").textContent =
      `${data.sexagenary}${data.zodiac}年`;

    // 更新今天信息
    const twd = WEEKDAYS[today.getDay() === 0 ? 6 : today.getDay() - 1];
    document.getElementById("today-info").textContent =
      `今天: ${today.getFullYear()}年${today.getMonth()+1}月${today.getDate()}日 星期${twd}`;

    // 渲染格子
    grid.innerHTML = "";
    for (const cell of data.cells) {
      const div = document.createElement("div");
      div.className = "cell";

      if (cell.day === 0) {
        div.classList.add("empty");
        grid.appendChild(div);
        continue;
      }

      // 样式类
      if (cell.isToday) div.classList.add("today");
      if (cell.weekday === 6) div.classList.add("sunday");
      if (cell.weekday === 5) div.classList.add("saturday");

      // 点击跳转到该日期所在月份
      div.onclick = () => {
        const d = new Date(currentYear, currentMonth - 1, cell.day);
        currentYear = d.getFullYear();
        currentMonth = d.getMonth() + 1;
        loadCalendar();
      };

      // 公历日期
      const solarEl = document.createElement("div");
      solarEl.className = "solar";
      solarEl.textContent = cell.day;
      div.appendChild(solarEl);

      // 农历日期
      const lunarEl = document.createElement("div");
      lunarEl.className = "lunar";
      if (cell.isSpecialLunar) lunarEl.classList.add("special");
      lunarEl.textContent = cell.lunarDayName;
      div.appendChild(lunarEl);

      // 标签（节日/节气）
      if (cell.tag) {
        const tagEl = document.createElement("div");
        tagEl.className = "tag " + cell.tagType;
        tagEl.textContent = cell.tag;
        div.appendChild(tagEl);
      }

      grid.appendChild(div);
    }

    grid.classList.remove("loading");
  }

  // ── 导航 ──
  function prevMonth() { currentMonth--; if(currentMonth<1){currentMonth=12;currentYear--;} loadCalendar(); }
  function nextMonth() { currentMonth++; if(currentMonth>12){currentMonth=1;currentYear++;} loadCalendar(); }
  function prevYear()  { currentYear--; loadCalendar(); }
  function nextYear()  { currentYear++; loadCalendar(); }
  function goToday()   { currentYear=today.getFullYear(); currentMonth=today.getMonth()+1; loadCalendar(); }

  function jumpDialog() {
    document.getElementById("jump-year").value = currentYear;
    document.getElementById("jump-month").value = currentMonth;
    document.getElementById("jump-dialog").showModal();
  }
  function closeJump() { document.getElementById("jump-dialog").close(); }
  function doJump() {
    const y = parseInt(document.getElementById("jump-year").value);
    const m = parseInt(document.getElementById("jump-month").value);
    if (y >= 1900 && y <= 2100 && m >= 1 && m <= 12) {
      currentYear = y; currentMonth = m; loadCalendar(); closeJump();
    } else {
      alert("年份: 1900–2100, 月份: 1–12");
    }
  }

  // ── 键盘绑定 ──
  document.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT") return;
    switch(e.key) {
      case "ArrowLeft":  prevMonth(); break;
      case "ArrowRight": nextMonth(); break;
      case "ArrowUp":    prevYear();  break;
      case "ArrowDown":  nextYear();  break;
      case "t": case "T": goToday(); break;
      case "g": case "G": jumpDialog(); break;
    }
  });

  // 启动
  loadCalendar();
</script>
</body>
</html>"""


# ─── API ────────────────────────────────────────────────────

@app.route("/")
def index():
    """主页"""
    today = datetime.date.today()
    return render_template_string(
        PAGE_HTML,
        year=today.year,
        month=today.month,
        today=today.isoformat(),
    )


@app.route("/api/calendar")
def api_calendar():
    """返回指定年月的日历数据（JSON）"""
    try:
        year = int(request.args.get("year", datetime.date.today().year))
        month = int(request.args.get("month", datetime.date.today().month))
    except (ValueError, TypeError):
        return jsonify({"error": "参数格式错误"}), 400

    if year < 1900 or year > 2100:
        return jsonify({"error": "年份超出范围 (1900–2100)"}), 400
    if month < 1 or month > 12:
        return jsonify({"error": "月份超出范围 (1–12)"}), 400

    today = datetime.date.today()

    # 日历矩阵
    cal = cal_module.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    # 节气
    terms = get_solar_terms_for_month(year, month)
    term_map: dict[int, str] = {t.day: t.name for t in terms}

    cells = []
    for week_idx, week in enumerate(month_days):
        for col_idx, day in enumerate(week):
            if day == 0:
                cells.append({"day": 0})
                continue

            is_today = (year == today.year and month == today.month and day == today.day)

            # 农历
            ld = solar_to_lunar(year, month, day)
            day_name = LUNAR_DAY_NAMES[ld.day - 1]
            is_special = day_name in ("初一", "十五")

            # 标签
            festival = lunar_festival(ld) or solar_festival(month, day)
            term = term_map.get(day)

            tag = None
            tag_type = ""
            if term:
                tag = "╎ " + term
                tag_type = "term"
            if festival:
                tag = (tag + "  " if tag else "") + "● " + festival
                tag_type = "festival"

            cells.append({
                "day": day,
                "weekday": col_idx,  # 0=Mon, 6=Sun
                "isToday": is_today,
                "lunarDayName": day_name,
                "isSpecialLunar": is_special,
                "tag": tag,
                "tagType": tag_type,
            })

    return jsonify({
        "year": year,
        "month": month,
        "sexagenary": year_sexagenary(year),
        "zodiac": year_zodiac(year),
        "cells": cells,
    })


# ─── 启动 ────────────────────────────────────────────────────

def run_web(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """启动 Web 服务"""
    print(f"\n  📅 万年历 Web 版")
    print(f"  ───────────────────")
    print(f"  打开浏览器访问: http://{host}:{port}")
    print(f"  按 Ctrl+C 退出\n")
    app.run(host=host, port=port, debug=debug)
