"""自包含交互组件（iframe 内完整 JS，经 Streamlit 组件协议双向通信）。

三个组件，全部沿用动力学排印令牌（墨黑/骨白/信号橙/Panel）：
    - kinetic_hero：指针响应可变字重首屏 + 磁吸 CTA（回传导航跳转）
    - score_sandbox：八滑杆实时评分沙盘（缩尾→z→logit→分值→等级→贡献），
      仪表指针阻尼动画、贡献条伸缩、重置/随机/案例/导出
    - result_gauge：真实评估结果的仪表与贡献瀑布动画
动效纪律：只动 transform / opacity / font-variation-settings；
单 rAF 循环驱动阻尼；prefers-reduced-motion 直接终态。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

import streamlit as st
import streamlit.components.v1 as components

from core.config_loader import load_indicators, load_model_parameters, load_risk_levels

_TOKENS = """
:root{--ink:#0b0b0c;--bone:#f4f1eb;--orange:#ff4d00;--panel:#141416;
--muted:#8a857b;--bd:rgba(244,241,235,0.12);
--a:#4ade80;--b:#2dd4bf;--c:#fbbf24;--d:#f87171;}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:var(--ink);color:var(--bone);
font-family:'Inter','Helvetica Neue','Microsoft YaHei',system-ui,sans-serif;}
body{overflow:hidden;}
::-webkit-scrollbar{width:8px;height:8px;}
::-webkit-scrollbar-track{background:var(--ink);}
::-webkit-scrollbar-thumb{background:#2a2a2e;border-radius:4px;}
::-webkit-scrollbar-thumb:hover{background:var(--orange);}
::selection{background:var(--orange);color:var(--ink);}
@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important;}}
"""

_FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Inter:opsz,wght@14..32,300..900&display=swap');"
)


def _params_payload() -> Dict[str, Any]:
    """评分链路参数（表 7-2 / 表 5-1 / 表 7-1），供组件内客户端实时复算。"""
    mp = load_model_parameters()
    rl = load_risk_levels()
    params = mp["scorecard_params"]["params"]
    names = {d["variable"]: d.get("name_cn", d["variable"])
             for d in load_indicators()["indicators"]}
    return {
        "variables": list(params.keys()),
        "names": names,
        "p1": {k: v["winsor_p1"] for k, v in params.items()},
        "p99": {k: v["winsor_p99"] for k, v in params.items()},
        "mean": {k: v["mean"] for k, v in params.items()},
        "std": {k: v["std"] for k, v in params.items()},
        "coef": {k: v["coef"] for k, v in params.items()},
        "intercept": mp["scorecard_params"]["intercept"],
        "levels": rl["levels"],
    }


# ---------------------------------------------------------------------------
# 1) 指针响应首屏
# ---------------------------------------------------------------------------
_HERO_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><style>__TOKENS__ __FONT__
.stage{position:relative;height:100vh;overflow:hidden;display:flex;
flex-direction:column;justify-content:center;padding:0 40px;}
.grain{position:absolute;inset:0;opacity:.05;pointer-events:none;
background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)'/%3E%3C/svg%3E");}
.glow{position:absolute;width:520px;height:520px;left:0;top:0;border-radius:50%;
background:radial-gradient(circle,rgba(255,77,0,0.16),rgba(255,77,0,0.05) 45%,transparent 70%);
pointer-events:none;will-change:transform;}
.label{font-size:13px;font-weight:500;letter-spacing:0.12em;text-transform:uppercase;
color:var(--muted);margin-bottom:18px;}
.title{overflow:hidden;font-size:clamp(40px,6.4vw,84px);font-weight:900;
line-height:0.98;letter-spacing:-0.03em;}
.title .ch{display:inline-block;transform:translateY(110%);opacity:0;
animation:rise .8s cubic-bezier(0.22,1,0.36,1) forwards;animation-delay:var(--d);
will-change:transform,font-variation-settings;}
@keyframes rise{to{transform:translateY(0);opacity:1;}}
.sub{color:var(--muted);font-size:14px;line-height:1.5;margin-top:16px;max-width:760px;}
.cta-row{margin-top:28px;display:flex;gap:16px;align-items:center;}
.cta{background:var(--orange);color:var(--ink);border:none;border-radius:2px;
font-weight:700;font-size:16px;padding:14px 32px;cursor:pointer;
transition:filter .4s cubic-bezier(0.22,1,0.36,1),transform .4s cubic-bezier(0.22,1,0.36,1);
will-change:transform;}
.cta:hover{filter:brightness(1.08);font-weight:900;}
.cta:active{transform:scale(0.98);}
.ghost{background:transparent;color:var(--bone);border:1px solid rgba(244,241,235,0.25);
border-radius:2px;font-size:14px;padding:13px 24px;cursor:pointer;
transition:border-color .4s,color .4s;}
.ghost:hover{border-color:var(--orange);color:var(--orange);}
.hint{color:var(--muted);font-size:12px;letter-spacing:0.08em;}
</style></head><body>
<div class="stage">
  <div class="grain"></div><div class="glow" id="glow"></div>
  <div class="label">Solar PV Listed Companies · Financial Risk Warning</div>
  <div class="title" id="title"></div>
  <div class="sub">__SUB__</div>
  <div class="cta-row">
    <button class="cta" id="cta">开始企业风险评估</button>
    <button class="ghost" id="ghost">查看实证研究</button>
    <span class="hint">移动指针 · 字重随距离呼吸</span>
  </div>
</div>
<script>
(function(){
  var TITLE=__TITLE__;
  var box=document.getElementById('title');
  var chars=[];
  TITLE.split('').forEach(function(c,i){
    var s=document.createElement('span');s.className='ch';
    s.style.setProperty('--d',(i*35)+'ms');
    s.textContent=c===' '?'\\u00a0':c;box.appendChild(s);chars.push(s);
  });
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var glow=document.getElementById('glow');
  var mx=innerWidth/2,my=innerHeight/2,gx=mx,gy=my;
  var targets=chars.map(function(){return {w:700,s:1};});
  var current=chars.map(function(){return {w:700,s:1};});
  addEventListener('mousemove',function(e){
    mx=e.clientX;my=e.clientY;
    if(reduce)return;
    chars.forEach(function(s,i){
      var r=s.getBoundingClientRect();
      var dx=(r.left+r.width/2)-mx,dy=(r.top+r.height/2)-my;
      var d=Math.sqrt(dx*dx+dy*dy);
      var t=Math.max(0,1-d/340);
      targets[i].w=300+600*t;
      targets[i].s=1+0.10*t;
    });
  });
  function frame(){
    gx+=(mx-gx)*0.08;gy+=(my-gy)*0.08;
    glow.style.transform='translate('+(gx-260)+'px,'+(gy-260)+'px)';
    if(!reduce){
      chars.forEach(function(s,i){
        var c=current[i],t=targets[i];
        c.w+=(t.w-c.w)*0.12;c.s+=(t.s-c.s)*0.12;
        s.style.fontVariationSettings="'wght' "+Math.round(c.w);
        s.style.transform='translateY(0) scaleX('+c.s.toFixed(3)+')';
      });
    }
    requestAnimationFrame(frame);
  }
  if(reduce){chars.forEach(function(s){s.style.transform='none';s.style.opacity=1;});}
  else{requestAnimationFrame(frame);}
  function send(v){
    // iframe 持 allow-same-origin：直接点击父页侧栏对应导航项，
    // 走 Streamlit widget 机制完成跳转（sandbox 禁止 top-navigation）
    try{
      var map={dashboard:'首页',assessment:'企业风险评估',empirical:'实证研究',data:'数据管理'};
      var labels=window.parent.document.querySelectorAll('section[data-testid="stSidebar"] label');
      for(var i=0;i<labels.length;i++){
        if(labels[i].textContent.indexOf(map[v])!==-1){labels[i].click();return;}
      }
    }catch(e){}
  }
  var cta=document.getElementById('cta');
  cta.addEventListener('mousemove',function(e){
    if(reduce)return;
    var r=cta.getBoundingClientRect();
    var dx=e.clientX-(r.left+r.width/2),dy=e.clientY-(r.top+r.height/2);
    cta.style.transform='translate('+dx*0.12+'px,'+dy*0.18+'px)';
  });
  cta.addEventListener('mouseleave',function(){cta.style.transform='';});
  cta.addEventListener('click',function(){send('assessment');});
  document.getElementById('ghost').addEventListener('click',function(){send('empirical');});
})();
</script></body></html>
"""


def kinetic_hero(title: str, subtitle: str, height: int = 460) -> Any:
    """指针响应首屏。CTA 经父页 URL query（?nav=）通知主应用跳转。"""
    html_doc = (
        _HERO_HTML.replace("__TOKENS__", _TOKENS)
        .replace("__FONT__", _FONT_IMPORT)
        .replace("__TITLE__", json.dumps(title, ensure_ascii=False))
        .replace("__SUB__", subtitle)
    )
    return components.html(html_doc, height=height, scrolling=False)


# ---------------------------------------------------------------------------
# 2) 评分沙盘 / 3) 结果仪表（共用渲染器）
# ---------------------------------------------------------------------------
_GAUGE_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><style>__TOKENS__ __FONT__
body{overflow:auto;}
.wrap{padding:20px 24px;display:grid;grid-template-columns:340px 1fr;gap:28px;}
@media (max-width:820px){.wrap{grid-template-columns:1fr;}}
.gauge-box{background:var(--panel);border:1px solid var(--bd);border-radius:2px;
padding:20px;text-align:center;}
.gauge-title{font-size:12px;letter-spacing:0.12em;color:var(--muted);text-transform:uppercase;}
svg{width:100%;max-width:300px;display:block;margin:8px auto;}
.needle{transform-origin:150px 150px;will-change:transform;}
.score{font-size:44px;font-weight:900;letter-spacing:-0.03em;line-height:1;}
.level-chip{display:inline-block;margin-top:10px;padding:5px 16px;border-radius:2px;
border:1px solid currentColor;font-weight:700;font-size:15px;}
.readout{color:var(--muted);font-size:12px;margin-top:10px;letter-spacing:0.06em;}
.controls{display:flex;flex-direction:column;gap:10px;}
.row{display:grid;grid-template-columns:150px 1fr 92px;gap:12px;align-items:center;}
.row label{font-size:13px;color:var(--bone);font-weight:500;}
.row .val{font-size:13px;color:var(--muted);text-align:right;font-variant-numeric:tabular-nums;}
.row .clip{color:var(--c);font-size:11px;}
input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:3px;
background:#2a2a2e;border-radius:2px;outline:none;cursor:pointer;}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;
width:14px;height:14px;border-radius:2px;background:var(--orange);cursor:grab;
transition:transform .3s cubic-bezier(0.22,1,0.36,1);}
input[type=range]::-webkit-slider-thumb:hover{transform:scale(1.25);}
input[type=range]::-moz-range-thumb{width:14px;height:14px;border-radius:2px;
background:var(--orange);border:none;cursor:grab;}
.btns{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px;}
.btns button{background:transparent;color:var(--bone);border:1px solid rgba(244,241,235,0.25);
border-radius:2px;font-size:13px;padding:9px 18px;cursor:pointer;
transition:border-color .4s,color .4s,transform .4s;}
.btns button:hover{border-color:var(--orange);color:var(--orange);}
.btns button:active{transform:scale(0.97);}
.btns button.primary{background:var(--orange);color:var(--ink);border:none;font-weight:700;}
.bars{margin-top:18px;display:flex;flex-direction:column;gap:8px;}
.bar-row{display:grid;grid-template-columns:150px 1fr 74px;gap:12px;align-items:center;}
.bar-row .nm{font-size:12px;color:var(--muted);}
.bar-track{height:10px;background:#1d1d21;border-radius:2px;overflow:hidden;position:relative;}
.bar-fill{position:absolute;inset:0;transform-origin:left center;transform:scaleX(0);
transition:transform .5s cubic-bezier(0.22,1,0.36,1);border-radius:2px;}
.bar-row .cv{font-size:12px;text-align:right;font-variant-numeric:tabular-nums;color:var(--bone);}
.bar-row.top .nm{color:var(--bone);font-weight:700;}
.note{color:var(--muted);font-size:11px;line-height:1.6;margin-top:14px;}
</style></head><body>
<div class="wrap">
  <div class="gauge-box">
    <div class="gauge-title">Risk Score · 0—100</div>
    <svg viewBox="0 0 300 170">
      <path d="M 30 150 A 120 120 0 0 1 37.77 107.52" stroke="#4ade80" stroke-width="10" fill="none" opacity="0.55"/>
      <path d="M 37.77 107.52 A 120 120 0 0 1 52.96 79.41" stroke="#2dd4bf" stroke-width="10" fill="none" opacity="0.55"/>
      <path d="M 52.96 79.41 A 120 120 0 0 1 89.70 46.25" stroke="#fbbf24" stroke-width="10" fill="none" opacity="0.55"/>
      <path d="M 89.70 46.25 A 120 120 0 0 1 270 150" stroke="#f87171" stroke-width="10" fill="none" opacity="0.55"/>
      <g id="ticks"></g>
      <g class="needle" id="needle">
        <line x1="150" y1="150" x2="150" y2="46" stroke="#f4f1eb" stroke-width="3"/>
        <circle cx="150" cy="150" r="7" fill="#ff4d00"/>
      </g>
    </svg>
    <div class="score" id="score">0.0</div>
    <div class="level-chip" id="chip">A</div>
    <div class="readout" id="readout">logit —</div>
  </div>
  <div>
    <div class="controls" id="controls"></div>
    <div class="btns" id="btns"></div>
    <div class="bars" id="bars"></div>
    <div class="note">贡献 = Firth 系数 × 标准化值；取正向最大三项为主要风险来源。
    分值为相对排序值，未经概率校准。滑杆拖动即时重算（客户端复算，参数同表 7-2）。</div>
  </div>
</div>
<script>
(function(){
  var P=__PAYLOAD__;
  var MODE=__MODE__;           // 'sandbox' | 'result'
  var FIXED=__FIXED__;         // result 模式的指标原始值
  var CASE=__CASE__;           // 海源复材案例原始指标
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var V=P.variables, coef=P.coef, names=P.names||{};
  var vals={};
  V.forEach(function(k){ vals[k]= (MODE==='result'? FIXED[k] : (CASE? CASE[k] : P.mean[k])); });

  // 刻度：等级切点
  var ticks=document.getElementById('ticks');
  function ang(score){ return Math.PI*(1-score/100); }
  [11.52,20.02,33.24].forEach(function(t){
    var a=ang(t),x1=150+112*Math.cos(a),y1=150-112*Math.sin(a);
    var x2=150+128*Math.cos(a),y2=150-128*Math.sin(a);
    var l=document.createElementNS('http://www.w3.org/2000/svg','line');
    l.setAttribute('x1',x1);l.setAttribute('y1',y1);
    l.setAttribute('x2',x2);l.setAttribute('y2',y2);
    l.setAttribute('stroke','#8a857b');l.setAttribute('stroke-width','1.5');
    ticks.appendChild(l);
  });

  // 控件区：sandbox 为滑杆，result 为只读 chips
  var controls=document.getElementById('controls');
  var valEls={},clipEls={};
  V.forEach(function(k){
    var row=document.createElement('div');row.className='row';
    var lab=document.createElement('label');lab.textContent=(names[k]||k);
    row.appendChild(lab);
    if(MODE==='sandbox'){
      var lo=P.p1[k]-(P.p99[k]-P.p1[k])*0.35, hi=P.p99[k]+(P.p99[k]-P.p1[k])*0.35;
      var inp=document.createElement('input');inp.type='range';
      inp.min=lo;inp.max=hi;inp.step=(hi-lo)/400;inp.value=vals[k];
      inp.addEventListener('input',function(){vals[k]=parseFloat(inp.value);recompute();});
      row.appendChild(inp);
    }else{
      var chip=document.createElement('div');
      chip.style.cssText='font-size:13px;color:var(--bone);font-variant-numeric:tabular-nums;';
      chip.textContent=Number(vals[k]).toFixed(4);
      row.appendChild(chip);
    }
    var v=document.createElement('div');v.className='val';row.appendChild(v);
    valEls[k]=v;controls.appendChild(row);
  });

  // 按钮区
  var btns=document.getElementById('btns');
  function mkBtn(text,cls,fn){var b=document.createElement('button');b.textContent=text;
    if(cls)b.className=cls;b.addEventListener('click',fn);btns.appendChild(b);return b;}
  if(MODE==='sandbox'){
    mkBtn('重置为训练均值','',function(){V.forEach(function(k){vals[k]=P.mean[k];});syncSliders();recompute();});
    mkBtn('随机扰动','',function(){V.forEach(function(k){
      var span=P.p99[k]-P.p1[k];vals[k]=P.p1[k]+Math.random()*span;});syncSliders();recompute();});
    mkBtn('海源复材 2024 案例','primary',function(){V.forEach(function(k){vals[k]=CASE[k];});syncSliders();recompute();});
    mkBtn('导出当前参数 JSON','',function(){
      var r=compute();var blob=new Blob([JSON.stringify({indicators:vals,z:r.z,
        contributions:r.contrib,logit:r.logit,score:r.score,level:r.level},null,2)],
        {type:'application/json'});
      var a=document.createElement('a');a.href=URL.createObjectURL(blob);
      a.download='pv-risk_sandbox.json';a.click();URL.revokeObjectURL(a.href);});
  }
  function syncSliders(){
    var inputs=controls.querySelectorAll('input[type=range]');
    V.forEach(function(k,i){inputs[i].value=vals[k];});
  }

  // 贡献条
  var bars=document.getElementById('bars');var barEls={};
  V.forEach(function(k){
    var row=document.createElement('div');row.className='bar-row';
    var nm=document.createElement('div');nm.className='nm';nm.textContent=(names[k]||k);
    var track=document.createElement('div');track.className='bar-track';
    var fill=document.createElement('div');fill.className='bar-fill';
    track.appendChild(fill);
    var cv=document.createElement('div');cv.className='cv';
    row.appendChild(nm);row.appendChild(track);row.appendChild(cv);
    bars.appendChild(row);barEls[k]={row:row,fill:fill,cv:cv};
  });

  function compute(){
    var z={},contrib={},logit=P.intercept,clipped={};
    V.forEach(function(k){
      var x=vals[k];var c=Math.min(P.p99[k],Math.max(P.p1[k],x));
      clipped[k]=(x<P.p1[k]||x>P.p99[k]);
      z[k]=(c-P.mean[k])/P.std[k];
      contrib[k]=coef[k]*z[k];logit+=contrib[k];
    });
    var score=100/(1+Math.exp(-logit));
    var level='D';
    if(score<11.52)level='A';else if(score<=20.02)level='B';else if(score<=33.24)level='C';
    var top=V.slice().sort(function(a,b){return contrib[b]-contrib[a];})
      .filter(function(k){return contrib[k]>0;}).slice(0,3);
    return {z:z,contrib:contrib,logit:logit,score:score,level:level,top:top,clipped:clipped};
  }

  var needle=document.getElementById('needle');
  var scoreEl=document.getElementById('score'),chip=document.getElementById('chip');
  var readout=document.getElementById('readout');
  var shown=0,target=0,raf=null;
  var LEVEL_COLOR={A:'#4ade80',B:'#2dd4bf',C:'#fbbf24',D:'#f87171'};
  var LEVEL_MEAN={A:'低风险',B:'中低风险',C:'中高风险',D:'高风险'};
  function loop(){
    shown+=(target-shown)*0.10;
    if(Math.abs(target-shown)<0.02){shown=target;}
    var a=-90+180*shown/100;
    needle.style.transform='rotate('+a.toFixed(2)+'deg)';
    scoreEl.textContent=shown.toFixed(1);
    if(shown!==target){raf=requestAnimationFrame(loop);}else{raf=null;}
  }
  function recompute(){
    var r=compute();target=r.score;
    chip.textContent=r.level+' · '+LEVEL_MEAN[r.level];
    chip.style.color=LEVEL_COLOR[r.level];
    readout.textContent='logit '+r.logit.toFixed(3)+' · 缩尾触界 '+
      V.filter(function(k){return r.clipped[k];}).length+' 项';
    V.forEach(function(k){
      valEls[k].innerHTML=(MODE==='sandbox'? vals[k].toFixed(3):vals[k].toFixed(4))+
        (r.clipped[k]?' <span class="clip">触界</span>':'')+
        ' <span style="color:#8a857b">z '+r.z[k].toFixed(2)+'</span>';
      var b=barEls[k];var c=r.contrib[k];
      var mag=Math.min(1,Math.abs(c)/2.2);
      b.fill.style.transform='scaleX('+mag.toFixed(3)+')';
      b.fill.style.background=c>0?(r.top.indexOf(k)>=0?'#ff4d00':'rgba(255,77,0,0.45)'):'#3a3a40';
      b.cv.textContent=(c>=0?'+':'')+c.toFixed(3);
      b.row.className='bar-row'+(r.top.indexOf(k)>=0?' top':'');
    });
    if(reduce){shown=target;needle.style.transform='rotate('+(-90+180*target/100)+'deg)';
      scoreEl.textContent=target.toFixed(1);}
    else if(!raf){raf=requestAnimationFrame(loop);}
  }
  recompute();
  if(window.Streamlit){Streamlit.setFrameHeight(document.body.scrollHeight+8);}
  addEventListener('resize',function(){
    if(window.Streamlit){Streamlit.setFrameHeight(document.body.scrollHeight+8);}
  });
})();
</script></body></html>
"""


def score_sandbox(height: int = 720) -> Any:
    """八滑杆实时评分沙盘：拖动即重算，仪表指针阻尼跟随。"""
    rl = load_risk_levels()
    case = rl["validation_case"]["raw_indicators"]
    html_doc = (
        _GAUGE_HTML.replace("__TOKENS__", _TOKENS)
        .replace("__FONT__", _FONT_IMPORT)
        .replace("__PAYLOAD__", json.dumps(_params_payload(), ensure_ascii=False))
        .replace("__MODE__", "'sandbox'")
        .replace("__FIXED__", "null")
        .replace("__CASE__", json.dumps(case, ensure_ascii=False))
    )
    return components.html(html_doc, height=height, scrolling=True)


def result_gauge(indicators: Dict[str, float], height: int = 560) -> None:
    """真实评估结果的仪表与贡献瀑布（入场指针扫过 + 贡献条伸缩）。"""
    html_doc = (
        _GAUGE_HTML.replace("__TOKENS__", _TOKENS)
        .replace("__FONT__", _FONT_IMPORT)
        .replace("__PAYLOAD__", json.dumps(_params_payload(), ensure_ascii=False))
        .replace("__MODE__", "'result'")
        .replace("__FIXED__", json.dumps(indicators, ensure_ascii=False))
        .replace("__CASE__", "null")
    )
    components.html(html_doc, height=height, scrolling=True)
