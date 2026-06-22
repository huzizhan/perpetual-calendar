"""
万年历 Web 版 — Flask 后端 + 内嵌 HTML/CSS/JS
四历法统一：农历 / 伊斯兰历 / 日本和历 / 佛历
"""

import calendar as cal_module
import datetime
import json
import logging

import os
from flask import Flask, request, jsonify, render_template_string, send_from_directory

from .huangli import compute_almanac
from .lunar import (
    solar_to_lunar, year_sexagenary, year_zodiac,
    lunar_festival, solar_festival, LUNAR_DAY_NAMES,
    LUNAR_FESTIVAL_INTRO, SOLAR_FESTIVAL_INTRO,
)
from .solar_terms import get_solar_terms_for_month
from .islamic import (
    gregorian_to_islamic, islamic_festival, islamic_month_special,
    ISLAMIC_MONTH_NAMES_CN, ISLAMIC_FESTIVAL_INTRO,
)
from .japanese import (
    gregorian_to_japanese, japanese_holiday, rokuyo_name, month_wareki_name,
    JAPANESE_HOLIDAY_INTRO,
)
from .buddhist import (
    gregorian_to_buddhist, thai_holiday, thai_month_name, thai_month_short,
    BUDDHIST_FESTIVAL_INTRO,
)

logging.basicConfig(level=logging.INFO)
app = Flask(__name__, static_folder=None)  # 禁用默认静态，用自定义路由

PAGE_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>万年历</title>
<style>
:root{--bg:#1e1e2e;--surface:#2a2a3a;--header-bg:#313244;--text:#cdd6f4;--text-dim:#6c7086;--accent:#89b4fa;--accent2:#cba6f7;--islamic:#fab387;--jp:#f38ba8;--buddha:#f9e2af;--red:#f38ba8;--yellow:#f9e2af;--green:#a6e3a1;--teal:#94e2d5;--radius:10px;--transition:0.2s ease}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}
.container{width:100%;max-width:820px;background:var(--surface);border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.4);overflow:hidden}
.header{display:flex;align-items:center;justify-content:center;gap:12px;padding:20px 24px 8px;background:var(--header-bg)}
.nav-btn{width:40px;height:40px;border:none;border-radius:50%;background:rgba(255,255,255,0.08);color:var(--text);font-size:18px;cursor:pointer;transition:var(--transition);display:flex;align-items:center;justify-content:center;flex-shrink:0}
.nav-btn:hover{background:rgba(255,255,255,0.18);transform:scale(1.05)}
.title-group{text-align:center}
.title-group .ym{font-size:24px;font-weight:700;color:var(--text);letter-spacing:2px}
.title-group .gz{font-size:13px;margin-top:2px}
.title-group .gz.c0{color:var(--accent2)}
.title-group .gz.c1{color:var(--islamic)}
.title-group .gz.c2{color:var(--jp)}
.title-group .gz.c3{color:var(--buddha)}

.cal-toggle{display:flex;justify-content:center;gap:4px;padding:10px 24px 14px;background:var(--header-bg);flex-wrap:wrap}
.cal-toggle button{padding:6px 13px;border:1px solid rgba(255,255,255,0.12);border-radius:20px;background:transparent;color:var(--text-dim);font-size:12px;cursor:pointer;transition:var(--transition)}
.cal-toggle button:hover{color:var(--text);border-color:rgba(255,255,255,0.3)}
.cal-toggle button.active{font-weight:700;color:#1e1e2e}
.cal-toggle button.active.c0{background:var(--accent2);border-color:var(--accent2)}
.cal-toggle button.active.c1{background:var(--islamic);border-color:var(--islamic)}
.cal-toggle button.active.c2{background:var(--jp);border-color:var(--jp)}
.cal-toggle button.active.c3{background:var(--buddha);border-color:var(--buddha)}

.quick-bar{display:flex;justify-content:center;gap:10px;padding:0 24px 14px;background:var(--header-bg)}
.quick-btn{padding:5px 14px;border:1px solid rgba(255,255,255,0.10);border-radius:16px;background:transparent;color:var(--text-dim);font-size:12px;cursor:pointer;transition:var(--transition)}
.quick-btn:hover{color:var(--text);border-color:rgba(255,255,255,0.25)}

.weekdays{display:grid;grid-template-columns:repeat(7,1fr);padding:8px 20px 2px;font-size:12px;font-weight:600;text-align:center;color:var(--text-dim)}
.weekdays span:nth-child(7){color:var(--red)}
.weekdays span:nth-child(6){color:var(--accent)}

.grid{display:grid;grid-template-columns:repeat(7,1fr);grid-template-rows:repeat(6,1fr);gap:3px;padding:4px 14px 16px;min-height:420px}
.cell{border-radius:var(--radius);display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;transition:var(--transition);background:var(--bg);overflow:hidden}
.cell:hover{background:rgba(255,255,255,0.06)}
.cell.empty{background:transparent;cursor:default}.cell.empty:hover{background:transparent}
.cell .solar{font-size:17px;font-weight:600;color:var(--text);line-height:1.2}
.cell .lunar{font-size:11px;color:var(--text-dim);line-height:1.2}
.cell .lunar.s0{color:var(--accent2);font-weight:600}
.cell .lunar.s1{color:var(--islamic);font-weight:600}
.cell .lunar.s2{color:var(--jp);font-weight:600}
.cell .lunar.s3{color:var(--buddha);font-weight:600}
.cell .tag{font-size:9px;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:92%}
.cell .tag.term{color:var(--teal)}
.cell .tag.f0{color:var(--yellow)}
.cell .tag.f1{color:var(--islamic)}
.cell .tag.f2{color:var(--jp)}
.cell .tag.f3{color:var(--buddha)}
.cell.sunday .solar{color:var(--red)}
.cell.saturday .solar{color:var(--accent)}
.cell.today{background:var(--accent)!important;box-shadow:0 4px 16px rgba(137,180,250,0.4)}
.cell.today .solar,.cell.today .lunar,.cell.today .tag{color:#1e1e2e!important}
.footer{display:flex;align-items:center;justify-content:space-between;padding:10px 24px;background:var(--header-bg);font-size:12px;color:var(--text-dim)}
.footer .today-info{font-weight:500;color:var(--text)}
@media(max-width:520px){.grid{gap:2px;padding:2px 6px 12px}.cell{min-height:48px;border-radius:8px}.cell .solar{font-size:14px}.cell .lunar{font-size:9px}.title-group .ym{font-size:18px}}
.loading{opacity:0.5;pointer-events:none;transition:opacity 0.15s}
.festival-panel{display:none;margin:0 14px 12px;padding:14px 18px;background:var(--header-bg);border-radius:12px;border-left:4px solid var(--accent2)}
.festival-panel.show{display:block}
.festival-panel .fp-title{font-size:15px;font-weight:700;color:var(--accent2);margin-bottom:6px}
.festival-panel .fp-date{font-size:11px;color:var(--text-dim);margin-bottom:8px}
.festival-panel .fp-intro{font-size:12px;color:var(--text);line-height:1.7;text-align:justify}
.festival-panel .fp-nav{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.festival-panel .fp-nav button{padding:4px 12px;border-radius:12px;border:1px solid rgba(255,255,255,0.15);background:transparent;color:var(--text-dim);font-size:11px;cursor:pointer}
.festival-panel .fp-nav button:hover,.festival-panel .fp-nav button.active{color:var(--accent2);border-color:var(--accent2)}
/* 黄历面板 */
.almanac-panel{display:none;margin:0 14px 12px;padding:14px 18px;background:var(--header-bg);border-radius:12px;border-left:4px solid var(--yellow)}
.almanac-panel.show{display:block}
.almanac-panel .ap-header{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.almanac-panel .ap-header .ap-sexagenary{font-size:18px;font-weight:700;color:var(--yellow)}
.almanac-panel .ap-header .ap-jianchu{font-size:13px;padding:3px 10px;border-radius:10px;background:rgba(249,226,175,0.15);color:var(--yellow);font-weight:600}
.almanac-panel .ap-header .ap-wuxing{font-size:12px;color:var(--text-dim)}
.almanac-panel .ap-row{display:flex;gap:12px;margin-bottom:6px;flex-wrap:wrap}
.almanac-panel .ap-label{font-size:10px;font-weight:700;color:var(--text-dim);min-width:20px}
.almanac-panel .ap-tags{display:flex;flex-wrap:wrap;gap:4px}
.almanac-panel .ap-tags span{padding:3px 9px;border-radius:8px;font-size:11px}
.ap-tag-yi{background:rgba(166,227,161,0.15);color:var(--green)}
.ap-tag-ji{background:rgba(243,139,168,0.15);color:var(--red)}
.ap-tag-shen{background:rgba(250,179,135,0.15);color:var(--orange)}
.ap-tag-xiong{background:rgba(166,173,200,0.12);color:var(--text-dim)}
.ap-chong{font-size:12px;color:var(--red);font-weight:600}
/* 移动端 */
.bottom-nav{display:none;position:fixed;bottom:0;left:0;right:0;background:var(--header-bg);border-top:1px solid rgba(255,255,255,0.08);z-index:100;padding:6px 0 env(safe-area-inset-bottom)}
.bottom-nav .bn-tabs{display:flex;justify-content:space-around}
.bottom-nav .bn-tab{flex:1;text-align:center;padding:6px 0;color:var(--text-dim);font-size:10px;cursor:pointer;transition:var(--transition);border:none;background:transparent}
.bottom-nav .bn-tab .bn-icon{font-size:20px;display:block;margin-bottom:2px}
.bottom-nav .bn-tab.active{color:var(--accent)}
/* 弹窗居中 */
dialog{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);margin:0;max-width:90vw;max-height:80vh}
dialog::backdrop{background:rgba(0,0,0,0.6)}
@media(max-width:768px){
body{padding:0;align-items:flex-start}
.container{border-radius:0;min-height:100vh;max-width:100%}
.header{padding:14px 12px 6px;gap:6px}
.nav-btn{width:34px;height:34px;font-size:15px}
.title-group .ym{font-size:18px}
.cal-toggle{padding:6px 12px 10px;gap:3px}
.cal-toggle button{padding:5px 10px;font-size:11px}
.quick-bar{padding:0 12px 8px}
.grid{padding:3px 6px;gap:2px}
.cell{min-height:58px;border-radius:8px}
.cell .solar{font-size:15px}
.cell .lunar{font-size:10px}
.cell .tag{font-size:8px}
.festival-panel,.almanac-panel{margin:0 8px 10px;padding:12px 14px}
.bottom-nav{display:block}
.footer{padding-bottom:70px}
}
@media(max-width:400px){
.header{padding:10px 8px 4px}
.grid{padding:2px 4px;gap:1px}
.cell{min-height:48px}
.cell .solar{font-size:13px}
.cell .lunar{font-size:9px}
.title-group .ym{font-size:16px}
.cal-toggle button{padding:4px 8px;font-size:10px}
}
</style>
<!-- PWA -->
<link rel="manifest" href="/static/manifest.json">
<meta name="theme-color" content="#313244">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="万年历">
<link rel="apple-touch-icon" href="/static/icons/icon-192.png">
<link rel="apple-touch-icon" sizes="512x512" href="/static/icons/icon-512.png">
</head><body>
<div class="container">
<div class="header">
<button class="nav-btn" onclick="prevMonth()">◀</button>
<button class="nav-btn" onclick="prevYear()">▲</button>
<div class="title-group"><div class="ym" id="title-ym"></div><div class="gz" id="title-gz"></div></div>
<button class="nav-btn" onclick="nextYear()">▼</button>
<button class="nav-btn" onclick="nextMonth()">▶</button>
</div>
<div class="cal-toggle">
<button id="b0" class="active c0" onclick="switchCal(0)">🇨🇳 农历·节气</button>
<button id="b1" class="c1" onclick="switchCal(1)">🌙 伊斯兰历</button>
<button id="b2" class="c2" onclick="switchCal(2)">🇯🇵 日本和历</button>
<button id="b3" class="c3" onclick="switchCal(3)">🛕 佛历</button>
</div>
<div class="quick-bar">
<button class="quick-btn" onclick="goToday()">📅 今天</button>
<button class="quick-btn" onclick="jumpDialog()">🔍 跳转</button>
</div>
<div class="weekdays"><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span></div>
<div class="grid" id="g"></div>
<div class="festival-panel" id="fp">
  <div class="fp-title" id="fp-title"></div>
  <div class="fp-date" id="fp-date"></div>
  <div class="fp-intro" id="fp-intro"></div>
  <div class="fp-nav" id="fp-nav"></div>
</div>
<div class="almanac-panel" id="ap">
  <div class="ap-header">
    <span class="ap-sexagenary" id="ap-sexagenary"></span>
    <span class="ap-jianchu" id="ap-jianchu"></span>
    <span class="ap-wuxing" id="ap-wuxing"></span>
  </div>
  <div class="ap-row"><span class="ap-label">宜</span><div class="ap-tags" id="ap-yi"></div></div>
  <div class="ap-row"><span class="ap-label">忌</span><div class="ap-tags" id="ap-ji"></div></div>
  <div class="ap-row"><span class="ap-label">冲</span><span class="ap-chong" id="ap-chong"></span></div>
  <div class="ap-row"><span class="ap-label">吉</span><div class="ap-tags" id="ap-jishen"></div></div>
  <div class="ap-row"><span class="ap-label">凶</span><div class="ap-tags" id="ap-xiongshen"></div></div>
</div>
<div class="bottom-nav"><div class="bn-tabs"><button class="bn-tab active" onclick="switchTab(0)"><span class="bn-icon">📅</span>日历</button><button class="bn-tab" onclick="switchTab(1)"><span class="bn-icon">🎉</span>节日</button><button class="bn-tab" onclick="switchTab(2)"><span class="bn-icon">🧿</span>黄历</button></div></div>
<div class="footer"><span class="hint">←→翻月 ↑↓翻年 1-4切历法 T今天 G跳转</span><span class="today-info" id="ti"></span></div>
<dialog id="jd" style="border:none;border-radius:14px;padding:24px 28px;background:var(--header-bg);color:var(--text);box-shadow:0 20px 60px rgba(0,0,0,0.5);min-width:250px">
<div style="font-size:16px;font-weight:700;margin-bottom:14px;text-align:center">跳转到</div>
<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px"><label style="width:22px">年</label><input id="jy" type="number" min="622" max="2100" style="flex:1;padding:7px 10px;border-radius:7px;border:1px solid rgba(255,255,255,0.2);background:var(--bg);color:var(--text);font-size:16px;text-align:center"></div>
<div style="display:flex;gap:8px;align-items:center;margin-bottom:14px"><label style="width:22px">月</label><input id="jm" type="number" min="1" max="12" style="flex:1;padding:7px 10px;border-radius:7px;border:1px solid rgba(255,255,255,0.2);background:var(--bg);color:var(--text);font-size:16px;text-align:center"></div>
<div style="display:flex;gap:8px;justify-content:flex-end"><button onclick="closeJump()" style="padding:7px 16px;border-radius:7px;border:1px solid rgba(255,255,255,0.2);background:transparent;color:var(--text);cursor:pointer;font-size:13px">取消</button><button onclick="doJump()" style="padding:7px 16px;border-radius:7px;border:none;background:var(--accent);color:#1e1e2e;font-weight:600;cursor:pointer;font-size:13px">跳转</button></div>
</dialog>
</div>
<script>
const TYPES=["chinese","islamic","japanese","buddhist"];
let cY={{year}},cM={{month}},cal=0;
const today=new Date("{{today}}"),WD=["一","二","三","四","五","六","日"];

function switchCal(n){cal=n;for(let i=0;i<4;i++){let b=document.getElementById("b"+i);b.className=cal===i?"active c"+i:"c"+i}load()}

async function load(){
  const grid=document.getElementById("g");grid.classList.add("loading");
  const r=await fetch(`/api/calendar?year=${cY}&month=${cM}&type=${TYPES[cal]}`),d=await r.json();
  document.getElementById("title-ym").textContent=`${d.year} 年  ${d.month} 月`;
  const gz=document.getElementById("title-gz");
  gz.textContent=d.subtitle||(d.sexagenary||"")+(d.zodiac||"")+"年"||"";
  gz.className="gz c"+cal;
  document.getElementById("ti").textContent=`今天: ${today.getFullYear()}年${today.getMonth()+1}月${today.getDate()}日 星期${WD[today.getDay()===0?6:today.getDay()-1]}`;
  grid.innerHTML="";
  for(const c of d.cells){
    const div=document.createElement("div");div.className="cell";
    if(c.day===0){div.classList.add("empty");grid.appendChild(div);continue}
    if(c.isToday)div.classList.add("today");
    if(c.weekday===6)div.classList.add("sunday");if(c.weekday===5)div.classList.add("saturday");
    if(c.festivalName)div.setAttribute('data-festival',c.festivalName);
    div.onclick=async()=>{const dd=new Date(cY,cM-1,c.day);cY=dd.getFullYear();cM=dd.getMonth()+1;await load();if(c.almanac)renderAlmanac(c.almanac);if(c.festivalName)switchToFestival(c.festivalName)};
    const se=document.createElement("div");se.className="solar";se.textContent=c.day;div.appendChild(se);
    const le=document.createElement("div");le.className="lunar";
    if(c.isSpecialLunar)le.classList.add("s"+cal);le.textContent=c.lunarDayName||"";div.appendChild(le);
    if(c.tag){const te=document.createElement("div");te.className="tag "+(c.tagType||"");te.textContent=c.tag;div.appendChild(te)}
    grid.appendChild(div)
  }grid.classList.remove("loading")
  // 节日介绍面板
  if(d.festivals&&d.festivals.length>0){
    _festivals=d.festivals;_festIdx=0;_renderFestival(0);
  }else{_festivals=[];document.getElementById("fp").classList.remove("show")}
  // 黄历面板：默认显示今天（仅chinese模式下有almanac数据）
  const todayCell=d.cells.find(c=>c.isToday);
  if(todayCell&&todayCell.almanac){renderAlmanac(todayCell.almanac)}
  else if(cal!==0){document.getElementById("ap").classList.remove("show")}
}

// 黄历面板渲染
function renderAlmanac(a){
  if(!a)return;
  document.getElementById("ap").classList.add("show");
  document.getElementById("ap-sexagenary").textContent=a.sexagenary+"日";
  document.getElementById("ap-jianchu").textContent=a.jianchu;
  document.getElementById("ap-wuxing").textContent=a.wuxing;
  document.getElementById("ap-yi").innerHTML=a.yi.map(t=>'<span class="ap-tag-yi">'+t+'</span>').join('');
  document.getElementById("ap-ji").innerHTML=a.ji.map(t=>'<span class="ap-tag-ji">'+t+'</span>').join('');
  document.getElementById("ap-chong").textContent=a.chong;
  document.getElementById("ap-jishen").innerHTML=a.jishen.map(t=>'<span class="ap-tag-shen">'+t+'</span>').join('');
  document.getElementById("ap-xiongshen").innerHTML=a.xiongshen.map(t=>'<span class="ap-tag-xiong">'+t+'</span>').join('');
}
let _todayAlmanac=null;

// 全局：通过节日名切换面板（日历格点击触发）
let _festivals=[],_festIdx=0;
function switchToFestival(name){
  const idx=_festivals.findIndex(f=>f.name===name);
  if(idx>=0){_festIdx=idx;_renderFestival(idx)}
}
function _renderFestival(idx){
  if(!_festivals.length)return;
  const f=_festivals[idx],fp=document.getElementById("fp");
  fp.classList.add("show");fp.querySelector("#fp-title").textContent=f.name+" 🎉";
  fp.querySelector("#fp-date").textContent=f.date+"（"+f.gregorianDate+"）";
  fp.querySelector("#fp-intro").textContent=f.intro;
  const fn=fp.querySelector("#fp-nav");fn.innerHTML="";
  if(_festivals.length>1)for(let i=0;i<_festivals.length;i++){
    const btn=document.createElement("button");btn.textContent=_festivals[i].name;
    if(i===idx)btn.classList.add("active");
    btn.onclick=()=>{_festIdx=i;_renderFestival(i)};fn.appendChild(btn)
  }
}

function prevMonth(){cM--;if(cM<1){cM=12;cY--}load()}
function nextMonth(){cM++;if(cM>12){cM=1;cY++}load()}
function prevYear(){cY--;load()}
function nextYear(){cY++;load()}
function goToday(){cY=today.getFullYear();cM=today.getMonth()+1;load()}
function jumpDialog(){document.getElementById("jy").value=cY;document.getElementById("jm").value=cM;document.getElementById("jd").showModal()}
function closeJump(){document.getElementById("jd").close()}
function doJump(){const y=parseInt(document.getElementById("jy").value),m=parseInt(document.getElementById("jm").value);if(y>=622&&y<=2100&&m>=1&&m<=12){cY=y;cM=m;load();closeJump()}else{alert("年份: 622–2100, 月份: 1–12")}}
// 移动端 Tab & 滑动
let _activeTab=0;
function switchTab(n){
  _activeTab=n;
  document.querySelectorAll('.bn-tab').forEach((b,i)=>b.classList.toggle('active',i===n));
  const fp=document.getElementById('fp'),ap=document.getElementById('ap'),grid=document.getElementById('g');
  if(n===0){fp.classList.remove('show');ap.classList.remove('show');grid.style.display=''}
  else if(n===1){ap.classList.remove('show');if(_festivals.length)fp.classList.add('show');grid.style.display='none'}
  else if(n===2){fp.classList.remove('show');if(_todayAlmanac)ap.classList.add('show');grid.style.display='none'}
}
let _tSX=0,_tSY=0;
document.addEventListener('touchstart',e=>{_tSX=e.touches[0].clientX;_tSY=e.touches[0].clientY},{passive:true});
document.addEventListener('touchend',e=>{
  const dx=e.changedTouches[0].clientX-_tSX,dy=e.changedTouches[0].clientY-_tSY;
  if(Math.abs(dx)>Math.abs(dy)&&Math.abs(dx)>40){if(dx>0)prevMonth();else nextMonth()}
},{passive:true});
document.addEventListener("keydown",e=>{if(e.target.tagName==="INPUT")return;switch(e.key){case"ArrowLeft":prevMonth();break;case"ArrowRight":nextMonth();break;case"ArrowUp":prevYear();break;case"ArrowDown":nextYear();break;case"t":case"T":goToday();break;case"g":case"G":jumpDialog();break;case"1":switchCal(0);break;case"2":switchCal(1);break;case"3":switchCal(2);break;case"4":switchCal(3);break}});
// PWA: register service worker
if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').then(r=>console.log('[PWA] SW registered')).catch(e=>console.log('[PWA] SW failed',e))}
load();
</script>
</body></html>"""


# ─── API ──────────────────────────────────────────────────

def _build_islamic_cell(year, month, day, col_idx, is_today, term_map):
    idate = gregorian_to_islamic(year, month, day)
    day_name = f"{ISLAMIC_MONTH_NAMES_CN[idate.month-1][:4]} {idate.day}"
    is_special = idate.day in (1, 10, 15)

    ifest = islamic_festival(idate)
    mspecial = islamic_month_special(idate)
    term = term_map.get(day)
    tags = []
    if term: tags.append(("╎"+term, "term"))
    if ifest: tags.append(("●"+ifest, "f1"))
    if mspecial and not ifest: tags.append((mspecial, "f1"))
    tag = "  ".join(t[0] for t in tags) if tags else None
    tag_type = tags[0][1] if tags else ""

    hijri_year = idate.year
    result = {"day": day, "weekday": col_idx, "isToday": is_today,
              "lunarDayName": day_name, "isSpecialLunar": is_special,
              "tag": tag, "tagType": tag_type}
    if ifest: result["festivalName"] = ifest
    return result, f"伊斯兰历 {hijri_year} AH"


def _build_japanese_cell(year, month, day, col_idx, is_today, term_map):
    import datetime as dt
    jd = gregorian_to_japanese(year, month, day)
    day_name = jd.short_str()
    is_special = jd.is_gannen or jd.day == 1

    holiday = japanese_holiday(month, day)
    term = term_map.get(day)
    ry = rokuyo_name(dt.date(year, month, day))
    wm = month_wareki_name(month)

    tags = []
    if term: tags.append(("╎"+term, "term"))
    if holiday: tags.append(("●"+holiday, "f2"))
    elif ry in ("大安","仏滅"): tags.append((ry, "f2"))
    else: tags.append((ry, ""))
    tag = "  ".join(t[0] for t in tags) if tags else None
    tag_type = tags[0][1] if tags and tags[0][1] else ""

    result = {"day": day, "weekday": col_idx, "isToday": is_today,
              "lunarDayName": day_name, "isSpecialLunar": is_special,
              "tag": tag, "tagType": tag_type}
    if holiday: result["festivalName"] = holiday
    return result, f"{jd.era_name}和历  |  {wm}"


def _build_buddhist_cell(year, month, day, col_idx, is_today, term_map):
    bd = gregorian_to_buddhist(year, month, day)
    tms = thai_month_short(month)
    day_name = f"{tms}{day}"
    is_special = (day == 1)

    holiday = thai_holiday(month, day)
    term = term_map.get(day)
    tm = thai_month_short(month)
    tn = thai_month_name(month)

    tags = []
    if term: tags.append(("╎"+term, "term"))
    if holiday: tags.append(("●"+holiday, "f3"))
    tag = "  ".join(t[0] for t in tags) if tags else None
    tag_type = tags[0][1] if tags else ""

    result = {"day": day, "weekday": col_idx, "isToday": is_today,
              "lunarDayName": day_name, "isSpecialLunar": is_special,
              "tag": tag, "tagType": tag_type}
    if holiday: result["festivalName"] = holiday
    return result, f"BE {bd.year}  |  {tn} ({tm})"


def _build_chinese_cell(year, month, day, col_idx, is_today, term_map):
    ld = solar_to_lunar(year, month, day)
    day_name = LUNAR_DAY_NAMES[ld.day - 1]
    is_special = day_name in ("初一", "十五")
    festival = lunar_festival(ld) or solar_festival(month, day)
    term = term_map.get(day)
    tag = None; tag_type = ""
    if term: tag = "╎ "+term; tag_type = "term"
    if festival: tag = (tag+"  " if tag else "") + "● "+festival; tag_type = "f0"
    result = {"day": day, "weekday": col_idx, "isToday": is_today,
              "lunarDayName": day_name, "isSpecialLunar": is_special,
              "tag": tag, "tagType": tag_type}
    if festival: result["festivalName"] = festival
    # 黄历数据
    try:
        al = compute_almanac(year, month, day)
        result["almanac"] = al.to_dict()
    except Exception:
        pass
    return result, None


BUILDERS = {
    "chinese": _build_chinese_cell,
    "islamic": _build_islamic_cell,
    "japanese": _build_japanese_cell,
    "buddhist": _build_buddhist_cell,
}


# ─── 静态文件 & PWA ──────────────────────────────────────

_STATIC_DIR = os.environ.get(
    "STATIC_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
)


@app.route("/sw.js")
def service_worker():
    """Service Worker — 必须在根路径 """
    return send_from_directory(_STATIC_DIR, "sw.js", mimetype="application/javascript")


@app.route("/static/<path:filename>")
def static_files(filename):
    """静态资源：图标、manifest 等"""
    return send_from_directory(_STATIC_DIR, filename)


# ─── 页面 & API ──────────────────────────────────────────

@app.route("/")
def index():
    today = datetime.date.today()
    return render_template_string(PAGE_HTML, year=today.year, month=today.month, today=today.isoformat())


@app.route("/api/calendar")
def api_calendar():
    try:
        year = int(request.args.get("year", datetime.date.today().year))
        month = int(request.args.get("month", datetime.date.today().month))
        cal_type = request.args.get("type", "chinese")
    except (ValueError, TypeError):
        return jsonify({"error": "参数格式错误"}), 400

    if year < 622 or year > 2100:
        return jsonify({"error": "年份超出范围"}), 400
    if month < 1 or month > 12:
        return jsonify({"error": "月份超出范围"}), 400

    today = datetime.date.today()
    cal = cal_module.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    terms = get_solar_terms_for_month(year, month)
    term_map: dict[int, str] = {t.day: t.name for t in terms}

    builder = BUILDERS.get(cal_type, _build_chinese_cell)
    cells = []
    subtitle = None

    for week in month_days:
        for col_idx, day in enumerate(week):
            if day == 0:
                cells.append({"day": 0})
                continue
            is_today = (year == today.year and month == today.month and day == today.day)
            cell, sub = builder(year, month, day, col_idx, is_today, term_map)
            if subtitle is None:
                subtitle = sub
            cells.append(cell)

    result = {"year": year, "month": month, "cells": cells}

    # ── 收集当月节日介绍（所有历法类型） ──
    festivals_in_month: dict[str, dict] = {}
    if cal_type == "chinese":
        result["sexagenary"] = year_sexagenary(year)
        result["zodiac"] = year_zodiac(year)
        for c in cells:
            if c["day"] == 0: continue
            # 农历节日
            ld = solar_to_lunar(year, month, c["day"])
            f = lunar_festival(ld)
            if f and f in LUNAR_FESTIVAL_INTRO and f not in festivals_in_month:
                festivals_in_month[f] = {
                    "name": f, "date": f"农历{ld.month}月{ld.day}日",
                    "gregorianDate": f"{year}年{month}月{c['day']}日",
                    "intro": LUNAR_FESTIVAL_INTRO[f],
                }
            # 公历节日
            sf = solar_festival(month, c["day"])
            if sf and sf in SOLAR_FESTIVAL_INTRO and sf not in festivals_in_month:
                festivals_in_month[sf] = {
                    "name": sf, "date": f"{year}年{month}月{c['day']}日",
                    "gregorianDate": f"{year}年{month}月{c['day']}日",
                    "intro": SOLAR_FESTIVAL_INTRO[sf],
                }
    elif cal_type == "islamic":
        result["subtitle"] = subtitle or ""
        for c in cells:
            if c["day"] == 0: continue
            idate = gregorian_to_islamic(year, month, c["day"])
            f = islamic_festival(idate)
            if f and f in ISLAMIC_FESTIVAL_INTRO and f not in festivals_in_month:
                festivals_in_month[f] = {
                    "name": f, "date": f"伊斯兰历{idate.month}月{idate.day}日",
                    "gregorianDate": f"{year}年{month}月{c['day']}日",
                    "intro": ISLAMIC_FESTIVAL_INTRO[f],
                }
    elif cal_type == "japanese":
        result["subtitle"] = subtitle or ""
        for c in cells:
            if c["day"] == 0: continue
            f = japanese_holiday(month, c["day"])
            if f and f in JAPANESE_HOLIDAY_INTRO and f not in festivals_in_month:
                festivals_in_month[f] = {
                    "name": f, "date": f"{year}年{month}月{c['day']}日",
                    "gregorianDate": f"{year}年{month}月{c['day']}日",
                    "intro": JAPANESE_HOLIDAY_INTRO[f],
                }
    elif cal_type == "buddhist":
        result["subtitle"] = subtitle or ""
        for c in cells:
            if c["day"] == 0: continue
            f = thai_holiday(month, c["day"])
            if f and f in BUDDHIST_FESTIVAL_INTRO and f not in festivals_in_month:
                festivals_in_month[f] = {
                    "name": f, "date": f"BE {year+543}年{month}月{c['day']}日",
                    "gregorianDate": f"{year}年{month}月{c['day']}日",
                    "intro": BUDDHIST_FESTIVAL_INTRO[f],
                }

    if festivals_in_month:
        result["festivals"] = list(festivals_in_month.values())

    return jsonify(result)


def run_web(host="0.0.0.0", port=5000, debug=True):
    import socket, subprocess, os
    local_ip = socket.gethostbyname(socket.gethostname())
    # 尝试获取 Tailscale IP
    ts_ip = ""
    try:
        ts_sock = os.path.expanduser("~/.local/share/tailscale/tailscaled.sock")
        ts_ip = subprocess.run(
            ["tailscale", "--socket=" + ts_sock, "ip", "-4"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except Exception:
        pass

    print(f"\n  📅 万年历 Web 统一版 (热重载已开启)")
    print(f"  ──────────────────────────────────────")
    print(f"  🇨🇳 农历  🌙 伊斯兰历  🇯🇵 日本和历  🛕 佛历")
    print(f"  本机访问:       http://127.0.0.1:{port}")
    print(f"  局域网 (WiFi):  http://{local_ip}:{port}")
    if ts_ip:
        print(f"  Tailscale (iPad): http://{ts_ip}:{port}")
    print(f"  修改源码后自动重载，iPad 浏览器实时看到效果")
    print(f"  按 Ctrl+C 退出\n")
    app.run(host=host, port=port, debug=debug)
