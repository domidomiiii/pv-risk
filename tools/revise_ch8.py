# -*- coding: utf-8 -*-
"""基于已建成网站修订论文第 8 章（图文兼备）。

策略：deepcopy 原文档的段落/表格元素作格式模板，替换文字与行内容，
整体替换第 8 章（元素 230—277），同步摘要一句与附录图表清单。
原件保留，输出修订版 docx。
运行：python tools/revise_ch8.py
"""
import copy
import os

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(ROOT),
                   "光伏上市公司财务困境预警研究与应用_含系统实现(1).docx")
DST = os.path.join(os.path.dirname(ROOT),
                   "光伏上市公司财务困境预警研究与应用_含系统实现_修订版.docx")
FIG = os.path.join(ROOT, "docs")

d = docx.Document(SRC)
body = d.element.body
children = list(body.iterchildren())

TPL_CHAPTER = children[230]   # 8 系统实现（14pt 加粗）
TPL_SECTION = children[232]   # 8.1 …（12pt 加粗）
TPL_BODY = children[231]      # 正文（10.5pt，首行缩进）
TPL_CAPTION = children[241]   # 图题
TPL_TBL4 = children[245]      # 表 8-1（4 列）
TPL_TBL3 = children[263]      # 表 8-2（3 列）
TPL_TBL4B = children[273]     # 表 8-3（4 列）
ANCHOR = children[278]        # 9 结论


def para(tpl, text):
    el = copy.deepcopy(tpl)
    p = Paragraph(el, d)
    runs = p.runs
    if runs:
        runs[0].text = text
        for r in runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(text)
    return el


def set_cell(cell, text):
    paras = cell.paragraphs
    for extra in paras[1:]:
        extra._element.getparent().remove(extra._element)
    runs = paras[0].runs
    if runs:
        runs[0].text = text
        for r in runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        paras[0].add_run(text)


def make_table(tpl, rows):
    el = copy.deepcopy(tpl)
    tb = Table(el, d)
    while len(tb.rows) < len(rows):
        tb._tbl.append(copy.deepcopy(tb.rows[1]._tr))
    while len(tb.rows) > len(rows):
        tr = tb.rows[-1]._tr
        tr.getparent().remove(tr)
    for row, vals in zip(tb.rows, rows):
        for cell, v in zip(row.cells, vals):
            set_cell(cell, v)
    return el


def make_img(filename, width_cm):
    p = d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(FIG, filename), width=Cm(width_cm))
    return p._element


E = []  # 新第 8 章元素序列

E.append(para(TPL_CHAPTER, "8 系统实现"))
E.append(para(TPL_BODY,
    "第 7 章的评分卡与第 5、6 章的实证结果在 Web 应用系统 PV-Risk（光伏上市公司财务风险预警与实证分析系统）中落地。"
    "系统以 Firth Logit 评分卡为核心功能，为论文各章表格与图提供统一的展示位置，以本地与云端双模式部署；"
    "界面采用深色动力学排印风格，提供指针响应与实时复算的交互组件。"))

E.append(para(TPL_SECTION, "8.1 设计目标与约束"))
E.append(para(TPL_BODY,
    "系统承担三项功能。其一，评分卡可独立复算：输入企业当期的 11 项报表字段，输出八项指标、缩尾值、"
    "标准化值、各项贡献、logit、0—100 分值、A—D 等级与三项主要风险来源；评估页提供手动输入、上传 Excel、"
    "内置验证案例与交互沙盘四种录入方式，沙盘支持拖动滑杆实时复算。其二，实证结果可对应查阅：第 3—7 章的"
    "表 3-2 至表 7-3 在系统中均有对应展示位置，第 5 章的模型对比、滚动外推、SHAP 重要性与校准结果以交互图表呈现。"
    "其三，评估过程可留存：单次评估结果入库存档，并可导出为 Excel。"))
E.append(para(TPL_BODY, "实现过程受三项约束。"))
E.append(para(TPL_BODY,
    "其一，计算真实性。评分链路的每一步由代码按论文公式执行，参数（P1/P99 分位点、缩尾后均值与标准差、"
    "Firth 系数、截距、等级阈值）从配置文件读取。海源复材案例只提供表 7-3 的输入指标值，输出全部由公式计算。"))
E.append(para(TPL_BODY,
    "其二，数据性质分级标注。系统中的数据分为三类：实时计算的评分结果；论文已公布、以静态或交互形式展示的"
    "实证结果（表 3-2 至表 6-5 以及图 5-1 至图 5-4 所依据的汇总数值）；以及因缺少 765 条原始观测与 LightGBM "
    "模型文件而无法重算的内容。前两类在界面上分别标注；第三类只呈现论文结论，不设“重新训练”或“在线预测”入口（6.5 节）。"))
E.append(para(TPL_BODY,
    "其三，依赖可控。技术栈限定为 Python、Streamlit、Pandas、NumPy、Plotly、SQLite 与 openpyxl；本地环境以 "
    "Python 3.13 验证，云端运行时为 Python 3.12。系统不含前端构建流程与外部接口，参数与实证数据以 JSON 集中管理，"
    "修改参数不需要改动代码。"))

E.append(para(TPL_SECTION, "8.2 总体架构"))
E.append(para(TPL_BODY,
    "系统分为五层（图 8-1）。配置层存放五份 JSON，分别是指标口径、评分卡与模型参数、风险等级阈值、论文实证结果"
    "与首页概览。核心算法层由六个模块构成，分别负责指标计算、输入校验、缩尾与标准化、Firth 评分、贡献分解与配置加载。"
    "服务层负责流程编排与数据出入，包括评估编排、Excel 导入与结果导出。展示层由 Streamlit 页面与共享组件构成："
    "四个一级菜单，以及主题与动效、侧栏、图表、指标卡、表格与交互组件六个共享组件；交互组件为自包含 iframe，"
    "在浏览器内完成指针响应排印与实时评分。存储层为 SQLite 与本地目录，保存评估记录与上传数据。"))
E.append(make_img("fig8_1_architecture.png", 15.875))
E.append(para(TPL_CAPTION, "图 8-1 系统总体架构"))
E.append(para(TPL_BODY,
    "注：箭头表示调用与数据流向。配置层的参数由核心算法层读取，服务层负责编排与读写存储层；展示层不直接访问数据库。"))
E.append(para(TPL_BODY,
    "表 8-1 给出各模块的文件与职责对应关系。应用代码约 3 340 行（含注释与空行），其中核心算法六个模块合计 528 行。"))
E.append(para(TPL_CAPTION, "表 8-1 系统模块组成与职责"))
E.append(make_table(TPL_TBL4, [
    ["层级", "模块文件", "主要职责", "对应论文内容"],
    ["核心算法", "core/indicator_calculator.py", "由 11 项报表字段计算八项指标", "表 3-1"],
    ["核心算法", "core/validation.py", "缺失、零分母与异常值检查", "3.2 节"],
    ["核心算法", "core/preprocessing.py", "1%/99% 缩尾与 Z-score 标准化", "7.2 节第一、二步"],
    ["核心算法", "core/firth_scoring.py", "logit、分值计算与 A—D 定级", "7.2 节第三、四步"],
    ["核心算法", "core/risk_attribution.py", "贡献分解与三项主要风险来源", "7.2 节第四步"],
    ["核心算法", "core/config_loader.py", "读取五份配置文件", "—"],
    ["服务层", "services/assessment_service.py", "串联校验、计算、评分与归因", "第 7 章"],
    ["服务层", "services/import_service.py", "解析 Excel 财务数据模板", "—"],
    ["服务层", "services/export_service.py", "评估结果导出为 Excel", "—"],
    ["展示层", "views/（四个页面）", "首页、风险评估、实证研究、数据管理", "第 3—7 章"],
    ["展示层", "components/（六个组件）", "主题与动效、侧栏、图表、指标卡、表格、交互组件", "—"],
    ["存储层", "database/（db、repository、schema.sql）", "评估记录存取（SQLite）", "—"],
]))

E.append(para(TPL_SECTION, "8.3 评分链路的实现"))
E.append(para(TPL_BODY,
    "评分链路即表 7-2 与重定阈值所定义的四个步骤，外加输入校验与结果归因。图 8-2 给出完整的数据流。"))
E.append(make_img("fig8_2_flow.png", 15.875))
E.append(para(TPL_CAPTION, "图 8-2 企业风险评估的计算流程"))
E.append(para(TPL_BODY,
    "注：①—⑩为计算顺序。error 级问题阻断评分，warning 级问题仅在结果页提示。"))
E.append(para(TPL_SECTION, "8.3.1 输入校验与指标计算"))
E.append(para(TPL_BODY,
    "评估入口接受企业名称、股票代码、财务数据年度与 11 项报表字段（资产总计、负债合计、流动资产合计、流动负债合计、"
    "在建工程净额、固定资产净额、未分配利润、归母净利润、营业收入、上期营业收入与经营活动现金流量净额）。八项指标按"
    "表 3-1 的口径计算，以“分子字段—分母字段”的字段对声明，八项指标由同一函数生成。"
    "分母绝对值小于 1e-12 或字段缺失时返回空值，不以 0 代替缺失参与评分。"))
E.append(para(TPL_BODY,
    "校验分两级。error 级阻断评分：任一必填字段缺失或非法、任一指标分母为零，系统只返回问题清单，不输出分值。"
    "warning 级仅提示：上期营业收入缺失（仅影响 growth，其余七项照常评分）、资产负债率超过 100%（资不抵债，"
    "属表 3-3 注所述真实极端值）、流动比率为负。"))
E.append(para(TPL_SECTION, "8.3.2 缩尾与标准化"))
E.append(para(TPL_BODY,
    "缩尾按表 7-2 的 P1/P99 分位点截断，标准化使用缩尾后的均值与标准差，顺序固定为先缩尾后标准化。两者为依次调用的两个函数，"
    "返回项记录原始值、缩尾值与 z 值，并标记是否触及上、下界。以海源复材为例，reta 原始值 −1.351 低于下界 −1.1103，"
    "缩尾后取 −1.1103，z 为 −4.573。"))
E.append(para(TPL_SECTION, "8.3.3 logit、分值与定级"))
E.append(para(TPL_BODY,
    "logit 由截距 −1.941 加八项系数与 z 值的内积得到，其中 lev 贡献经符号约束截断（8.3.4 节），分值经 Sigmoid 变换后乘以 100。"
    "定级按训练集（2014—2022，n=551）分值 50/75/90 分位重定的四个区间执行：14.23 与 23.17 归 B 级、37.27 归 C 级，"
    "37.28 起为 D 级，后 50%/前 10% 的语义不变。原切点 11.52/20.02/33.24 下，lev 的负贡献会把高杠杆亏损企业从 D 压到 C，"
    "故本轮重定；原切点保留于配置元数据供回滚。分值不作四舍五入后再比较。"))
E.append(para(TPL_SECTION, "8.3.4 贡献分解与风险来源"))
E.append(para(TPL_BODY,
    "单项贡献取系数与 z 值之积。β_lev = −0.495 是控制其余七项不变的条件效应，不是提高负债率的因果效应。"
    "lev 贡献取 max(0, β_lev × z_lev)，其余七项不变，logit 与风险来源排序均用截断后贡献；"
    "原始贡献保留于 raw_contributions 字段供明细展示。按降序排列后取截断后正向贡献最大的三项作为主要风险来源。"
    "lev 被截断时结果页追加符号约束提示。结果页固定显示：分值为 0—100 的相对风险评分，未经概率校准，"
    "不代表下一年度亏损的绝对概率。"))

E.append(para(TPL_SECTION, "8.4 数据与配置管理"))
E.append(para(TPL_BODY,
    "五份配置文件的用途与来源见表 8-2。Firth 系数与指标口径为不得修改项，元数据注明来源与使用限制；"
    "等级阈值为应用层重定项。"))
E.append(para(TPL_CAPTION, "表 8-2 配置文件与内容来源"))
E.append(make_table(TPL_TBL3, [
    ["配置文件", "内容", "来源"],
    ["indicator_definitions.json", "八项指标口径、11 项报表字段", "表 3-1、3.2 节"],
    ["model_parameters.json", "Firth 系数与截距、P1/P99 分位点、缩尾后均值与标准差、LightGBM 超参数",
     "表 5-1、表 7-2、表 4-1"],
    ["risk_levels.json", "A—D 等级阈值（训练集分位重定）、分位含义与内置验证案例", "训练集 n=551、表 7-3"],
    ["research_results.json", "表 3-2 至表 6-5 的汇总数值、图 5-1 至图 5-4 所依据的数值", "第 3—6 章"],
    ["research_overview.json", "样本概况、三类模型、四项结论、适用边界", "摘要、结论"],
]))
E.append(para(TPL_BODY,
    "评估记录存入 SQLite 单表 assessments，共 16 个字段：企业名称、股票代码、年度、创建时间、11 项原始字段的 JSON、"
    "八项指标、缩尾值、z 值、贡献、logit、分值、等级、等级含义、三项风险来源与校验提示。明细以 JSON 列保存，"
    "系统只保存单次评估快照，不做跨企业汇总查询。"))
E.append(para(TPL_BODY,
    "Excel 导入模板含 14 列（企业名称、股票代码、年度与 11 项报表字段）。导入时逐行校验，对不合格行给出原因并跳过，"
    "合格行进入评估队列。导出为含“评估概览”“指标明细”“校验提示”三个工作表的文件；历史记录可另导出为单表。"))
E.append(para(TPL_BODY,
    "数据库目录按三级优先级解析：环境变量 PV_RISK_DB_DIR 指定的路径优先；其次为项目 data/ 目录，以写入探测确认可写；"
    "探测失败时回退至系统临时目录（8.7 节）。"))

E.append(para(TPL_SECTION, "8.5 实证结果的呈现与交互设计"))
E.append(para(TPL_BODY,
    "系统按四个一级菜单组织：首页（研究概览）、企业风险评估、实证研究与数据管理。实证研究页以五个二级标签整合论文"
    "第 3—7 章，依次为研究设计与样本、模型与研究方法、实证结果与模型比较、稳健性检验、评分卡构建与案例。表 3-2 至表 7-3 "
    "以表格原样呈现；表 5-4 至表 5-7 另以柱状图与折线图呈现，所有此类图表标注“论文实证结果”。"))
E.append(para(TPL_BODY,
    "图 5-1（ROC/PR 曲线）、图 5-2（SHAP 值分布）与图 5-3（杠杆依赖图）依赖逐观测的预测值与 SHAP 矩阵，"
    "论文只公布汇总指标与重要性排序。系统保留表格与文字说明，注明论文仅公布汇总值，不以示意曲线替代；"
    "图 5-4 以表 5-7 的汇总值绘制平均预测概率与 Brier 得分的对比柱状图。"))
E.append(para(TPL_BODY,
    "界面采用深色动力学排印风格：墨黑舞台（#0b0b0c）、骨白文字（#f4f1eb）、信号橙（#ff4d00）为唯一强调色，字体为可变字体 "
    "Inter Variable。动效限于 transform、opacity 与 font-variation-settings 三类属性：首页标题逐字入场、核心数字跑马灯滚动、"
    "侧栏字标字重呼吸；侧栏提供动效开关，系统级 prefers-reduced-motion 设置直接呈现终态。等级语义色（A 绿、B 青、C 琥珀、"
    "D 红）独立于强调色保留，用于等级徽章与仪表弧段。"))
E.append(para(TPL_BODY,
    "系统提供三个自包含交互组件，均运行于 iframe 内并与主应用同源通信。其一，指针响应首屏：标题的可变字重与横向缩放随指针"
    "位置阻尼插值，CTA 按钮具磁吸效果，点击后跳转对应页面（图 8-3）。其二，交互评分沙盘：八个滑杆对应八项指标，拖动即在客户端"
    "复算缩尾→标准化→logit→分值→等级→贡献，仪表指针阻尼跟随。沙盘默认联动模式：拖动 lev 时按训练集相关系数同步调整"
    "Δz_roa = −0.40×Δz_lev、Δz_cr = −0.50×Δz_lev、Δz_reta = −0.49×Δz_lev；"
    "条件效应模式保留但默认关闭，滑杆旁常驻警告文案。客户端与后端共用同一参数载荷（含符号约束与联动系数）。"
    "另提供重置为训练均值、随机扰动、海源复材 2024 案例与导出当前参数 "
    "JSON 四个动作（图 8-4）。其三，结果仪表：真实评估完成后指针自零扫至分值，贡献条依次伸缩（图 8-5）。"))
E.append(make_img("fig_ui_home.png", 12.0))
E.append(para(TPL_CAPTION, "图 8-3 系统首页（动力学排印首屏与核心数字跑马灯）"))
E.append(make_img("fig_ui_sandbox.png", 12.0))
E.append(para(TPL_CAPTION, "图 8-4 交互评分沙盘（八滑杆实时复算与阻尼仪表）"))
E.append(make_img("fig_ui_result.png", 12.0))
E.append(para(TPL_CAPTION, "图 8-5 评估结果仪表与贡献分解"))

E.append(para(TPL_SECTION, "8.6 系统验证"))
E.append(para(TPL_BODY,
    "验证分三部分：单元测试、案例复算与端到端导入验证。单元测试覆盖八项指标口径、缺失与零分母处理、缩尾与标准化的顺序、"
    "定级边界、Sigmoid 分值、符号约束、沙盘联动一致性、贡献排序与案例复算，共 10 项，全部通过（表 8-3）。"))
E.append(para(TPL_BODY,
    "海源复材复算：logit = 2.1407，分值 89.48，D 级；lev 原始贡献 −0.524 置零后计入 logit。"
    "三项主要风险来源为 roa（+1.971）、reta（+1.010）、ocf（+0.526）。"))
E.append(para(TPL_BODY,
    "端到端验证由 tools/verify_import.py 执行：生成符合导入模板的验证 Excel，跑通“Excel 导入 → 字段校验 → 指标计算 → "
    "缩尾与标准化 → Firth 评分 → 定级 → 归因”全链路。海源复材（002529）得分 89.4798、D 级；"
    "两家测试企业分别得 4.5190（A 级）与 18.4880（B 级），导入解析错误 0 条。"
    "联动模式下 lev 从 0.46 拖至 0.93，分值自 12.55 升至 40.56。"))
E.append(para(TPL_CAPTION, "表 8-3 系统验证用例与结果"))
E.append(make_table(TPL_TBL4B, [
    ["编号", "验证内容", "判定标准", "结果"],
    ["1", "八项指标口径", "与按表 3-1 手工计算的数值一致", "通过"],
    ["2", "缩尾与标准化顺序", "reta 缩尾至 −1.1103，z 为 −4.573", "通过"],
    ["3", "等级边界", "14.23、23.17 归 B；37.27 归 C；37.28 归 D", "通过"],
    ["4", "缺失值阻断", "必填字段缺失时不输出分值", "通过"],
    ["5", "零分母阻断", "资产总计为 0 时四项比值指标报错", "通过"],
    ["6", "Sigmoid 分值", "分值随 logit 单调递增且落于 0—100", "通过"],
    ["7", "风险来源排序", "仅取正向贡献最大三项，负贡献不列入", "通过"],
    ["8", "案例复算", "logit 2.1407、分值 89.48、D 级、来源排序一致", "通过"],
    ["9", "端到端导入链路", "三家企业导入 0 错误；海源复材 89.4798、D 级与预期一致", "通过"],
    ["10", "沙盘客户端复算", "同一输入下与后端分值差小于 0.001", "通过"],
    ["11", "符号约束", "单独推高 lev 分值不降；lev 负贡献置零、原始贡献保留", "通过"],
    ["12", "沙盘联动模式", "lev 0.46→0.93 分值 12.55→40.56，不低于 12.55", "通过"],
]))
E.append(para(TPL_BODY,
    "注：第 9—12 项分别以 tools/verify_import.py、组件对照与联动场景复算运行。"))

E.append(para(TPL_SECTION, "8.7 部署方式与使用边界"))
E.append(para(TPL_BODY,
    "系统以本地与云端双模式部署。本地模式：安装 requirements.txt 所列依赖后，以 streamlit run app.py 启动，浏览器访问本地端口；"
    "数据文件与 SQLite 数据库均位于项目目录内，不外传。云端模式：代码仓库托管于 GitHub，Streamlit Community Cloud 在推送后自动"
    "重新构建部署，运行时为 Python 3.12，公开访问地址为 https://pv-risk-xbyyg3yzaso5cgxxwdbuem.streamlit.app/。目录按配置、核心、"
    "服务、页面、组件、数据库、数据与测试分离，与表 8-1 的层级对应。"))
E.append(para(TPL_BODY,
    "云端容器的文件系统为临时存储：评估历史随容器重启清空，系统以 Excel 导出作为持久留存手段；数据库目录按 8.4 节的三级优先级解析，"
    "只读环境下自动回退临时目录，评估功能保持可用。云端实例为单容器部署，不含用户注册、权限与多人协作，评估历史在同一实例内共享。"))
E.append(para(TPL_BODY,
    "其使用边界与 7.3 节一致，并因工程实现而另有三条。其一，系统只对单家企业当期数据打分；表 5-8 的预警名单为论文结果的静态呈现，"
    "系统不提供全库批量打分。其二，系统不含 LightGBM 模型文件，无法对任意企业运行树模型预测或重算 SHAP 值，相关结果的展示以论文汇总"
    "数值为限。其三，等级阈值由 2014—2022 年训练集固定，行业整体恶化时同一分值的相对含义会漂移（7.5 节），实际使用应按年度重估切点。"))

# ---- 摘要一句同步 ----
p5 = Paragraph(children[5], d)
new_text = p5.text.replace("可本地运行的原型系统", "可本地运行并部署于云端的应用系统")
runs = p5.runs
runs[0].text = new_text
for r in runs[1:]:
    r._element.getparent().remove(r._element)

# ---- 替换第 8 章 ----
for el in children[230:278]:
    body.remove(el)
for el in E:
    ANCHOR.addprevious(el)

# ---- 附录图表清单追加三图 ----
appendix = None
for tb in d.tables:
    if any("图 8-1" in c.text for row in tb.rows for c in row.cells):
        appendix = tb
        break
assert appendix is not None, "未找到附录图表清单"
for vals in [
    ["图 8-3", "系统首页（动力学排印首屏）", "正文插图"],
    ["图 8-4", "交互评分沙盘", "正文插图"],
    ["图 8-5", "评估结果仪表与贡献分解", "正文插图"],
]:
    row = appendix.add_row()
    for cell, v in zip(row.cells, vals):
        set_cell(cell, v)

d.save(DST)
print("saved:", DST)
print("new chapter elements:", len(E))