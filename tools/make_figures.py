# -*- coding: utf-8 -*-
"""生成论文第 8 章插图（学术印刷风格：白底黑字）。

图 8-1 系统总体架构（五层）
图 8-2 企业风险评估的计算流程（①—⑩）
运行：python tools/make_figures.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs")

INK = "#1a1a1a"
BAND = "#eef1f5"
EDGE = "#33475b"
FILL = "#ffffff"
GREY = "#666666"


def box(ax, x, y, w, h, text, fs=7.5, bold=False, fill=FILL, edge=EDGE, lw=0.8):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle="round,pad=0.004,rounding_size=0.008",
                       linewidth=lw, edgecolor=edge, facecolor=fill,
                       transform=ax.transAxes, clip_on=False)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=INK, fontweight="bold" if bold else "normal",
            transform=ax.transAxes, linespacing=1.25)


def arrow(ax, p1, p2, style="-|>", color=EDGE, lw=0.9, ls="-"):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=9,
                        linewidth=lw, color=color, linestyle=ls,
                        transform=ax.transAxes, clip_on=False,
                        shrinkA=1.5, shrinkB=1.5)
    ax.add_patch(a)


def layer_label(ax, y, h, text):
    ax.add_patch(FancyBboxPatch((0.0, y), 0.085, h,
                                boxstyle="round,pad=0.002,rounding_size=0.006",
                                linewidth=0, facecolor=BAND,
                                transform=ax.transAxes, clip_on=False))
    ax.text(0.0425, y + h / 2, text, ha="center", va="center", fontsize=8,
            color=EDGE, fontweight="bold", transform=ax.transAxes,
            linespacing=1.3)


# ---------------------------------------------------------------------------
# 图 8-1 系统总体架构
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.25, 4.35))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

X0, W = 0.10, 0.88

# 展示层
layer_label(ax, 0.760, 0.215, "展示层")
pw = (W - 3 * 0.015) / 4
for i, t in enumerate(["首页 · 研究概览", "企业风险评估", "实证研究", "数据管理"]):
    box(ax, X0 + i * (pw + 0.015), 0.885, pw, 0.075, t, fs=7.5)
box(ax, X0, 0.775, W, 0.085,
    "共享组件：主题与动效 · 侧栏导航 · 图表 · 指标卡 · 表格 · 交互组件（自包含 iframe）",
    fs=7, fill=BAND)

# 服务层
layer_label(ax, 0.555, 0.130, "服务层")
sw = (W - 2 * 0.02) / 3
for i, t in enumerate(["评估编排\nassessment_service", "Excel 导入\nimport_service",
                       "结果导出\nexport_service"]):
    box(ax, X0 + i * (sw + 0.02), 0.575, sw, 0.090, t, fs=7)

# 核心算法层
layer_label(ax, 0.330, 0.150, "核心\n算法层")
cw = (W - 5 * 0.012) / 6
core = ["指标计算", "输入校验", "缩尾与\n标准化", "Firth 评分", "贡献分解", "配置加载"]
for i, t in enumerate(core):
    box(ax, X0 + i * (cw + 0.012), 0.360, cw, 0.095, t, fs=7)

# 配置层 / 存储层
layer_label(ax, 0.060, 0.180, "配置层")
box(ax, X0, 0.075, 0.52, 0.150,
    "五份 JSON\n指标口径 · 评分卡与模型参数 · 风险等级阈值\n论文实证结果 · 首页概览",
    fs=7, fill=BAND)
ax.add_patch(FancyBboxPatch((0.665, 0.060), 0.085, 0.180,
                            boxstyle="round,pad=0.002,rounding_size=0.006",
                            linewidth=0, facecolor=BAND,
                            transform=ax.transAxes, clip_on=False))
ax.text(0.7075, 0.150, "存储层", ha="center", va="center", fontsize=8,
        color=EDGE, fontweight="bold", transform=ax.transAxes)
box(ax, 0.765, 0.075, 0.215, 0.150, "SQLite\nassessments 表\ndata/ 目录", fs=7, fill=BAND)

# 箭头
arrow(ax, (0.54, 0.775), (0.54, 0.665))
ax.text(0.555, 0.720, "调用", fontsize=6.5, color=GREY, transform=ax.transAxes)
arrow(ax, (0.54, 0.575), (0.54, 0.455))
ax.text(0.555, 0.515, "编排", fontsize=6.5, color=GREY, transform=ax.transAxes)
arrow(ax, (0.30, 0.225), (0.30, 0.360))
ax.text(0.315, 0.290, "读取参数", fontsize=6.5, color=GREY, transform=ax.transAxes)
# 读写箭头走右侧外沿，避免穿过核心算法层框体
arrow(ax, (0.98, 0.620), (0.995, 0.620), style="-")
arrow(ax, (0.995, 0.620), (0.995, 0.150), style="-")
arrow(ax, (0.995, 0.150), (0.98, 0.150))
ax.text(0.988, 0.400, "读写", fontsize=6.5, color=GREY, rotation=90,
        va="center", transform=ax.transAxes)

fig.savefig(os.path.join(OUT, "fig8_1_architecture.png"), dpi=220,
            bbox_inches="tight", pad_inches=0.04, facecolor="white")
plt.close(fig)

# ---------------------------------------------------------------------------
# 图 8-2 企业风险评估的计算流程
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.25, 5.4))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

steps = [
    "① 输入 11 项报表字段（手动 / Excel / 内置案例 / 交互沙盘）",
    "② 两级校验：error 级阻断评分，warning 级仅提示",
    "③ 按表 3-1 口径计算八项指标（分母为零返回空值）",
    "④ 按表 7-2 的 P1/P99 分位点缩尾（标记触界）",
    "⑤ Z-score 标准化（缩尾后均值与标准差）",
    "⑥ logit = −1.941 + Σ β·z",
    "⑦ 分值 = 100 / (1 + e^−logit)",
    "⑧ 按重定阈值定级（边界取闭区间）",
    "⑨ 贡献分解：β·z，降序排列",
    "⑩ 取正向贡献前三为风险来源 · 结果入库",
]
n = len(steps)
top, bot = 0.965, 0.035
gap = (top - bot) / n
bh = gap * 0.62
bw = 0.60
x0 = 0.10
for i, t in enumerate(steps):
    y = top - (i + 1) * gap + (gap - bh) / 2
    box(ax, x0, y, bw, bh, t, fs=7.5)
    if i < n - 1:
        arrow(ax, (x0 + bw / 2, y), (x0 + bw / 2, y - (gap - bh)))

# error 分支
y2 = top - 2 * gap + (gap - bh) / 2
box(ax, 0.755, y2, 0.215, bh, "返回问题清单\n不输出分值", fs=7, fill=BAND)
arrow(ax, (x0 + bw, y2 + bh / 2), (0.755, y2 + bh / 2), ls="--")
ax.text(0.7125, y2 + bh + 0.008, "error", fontsize=6.5, color=GREY,
        ha="center", transform=ax.transAxes)

fig.savefig(os.path.join(OUT, "fig8_2_flow.png"), dpi=220,
            bbox_inches="tight", pad_inches=0.04, facecolor="white")
plt.close(fig)

print("figures saved:", os.path.join(OUT, "fig8_1_architecture.png"),
      os.path.join(OUT, "fig8_2_flow.png"))