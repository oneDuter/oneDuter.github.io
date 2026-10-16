"""Generate original explanatory figures for the Kimi K3 note.

Requires matplotlib and numpy. SVG keeps text editable. PNG is exported at
160 dpi. Choose an installed Chinese font with --font if needed.
All toy values and formula slices are marked in the figures and the article.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

P = argparse.ArgumentParser()
P.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "img/learning-notes/kimi-k3")
P.add_argument("--font", default="")
args = P.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
font = args.font or next((x for x in ["/System/Library/Fonts/STHeiti Medium.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"] if Path(x).exists()), "")
if font:
    fm.fontManager.addfont(font)
    family = fm.FontProperties(fname=font).get_name()
else:
    family = "sans-serif"
plt.rcParams.update({"font.family": [family, "DejaVu Sans"], "font.size": 16, "axes.unicode_minus": False,
                     "svg.fonttype": "none", "savefig.facecolor": "#f6f8fc", "figure.facecolor": "#f6f8fc"})
NAVY, TEAL, BLUE, AMBER, RED = "#142e47", "#087f83", "#3368b3", "#bf7b13", "#bb4b51"
PALE, LIGHT, GRAY = "#e6f3f1", "#e8effa", "#68788b"

def canvas(title, subtitle, height=7.5):
    fig, ax = plt.subplots(figsize=(14, height))
    fig.subplots_adjust(left=.025, right=.975, bottom=.055, top=.83)
    ax.set(xlim=(0, 14), ylim=(0, 7)); ax.axis("off")
    fig.text(.035, .94, title, fontsize=25, color=NAVY, weight="bold", va="top")
    fig.text(.035, .88, subtitle, fontsize=14, color=GRAY, va="top")
    return fig, ax

def box(ax, x, y, w, h, text, color=TEAL, fill=PALE, size=17):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.035,rounding_size=0.12", linewidth=1.5, edgecolor=color, facecolor=fill))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=size, color=NAVY, linespacing=1.55)

def arrow(ax, start, end, color=GRAY, rad=0):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=18, color=color, linewidth=1.7, connectionstyle=f"arc3,rad={rad}"))

def note(ax, x, y, text, size=15, color=GRAY, ha="center"):
    ax.text(x, y, text, fontsize=size, color=color, ha=ha, va="center", linespacing=1.5)

def save(fig, name):
    fig.savefig(args.output / (name+".svg"))
    fig.savefig(args.output / (name+".png"), dpi=160)
    plt.close(fig)

fig, ax = canvas("01  Kimi K3：三种信息流", "2.78T 总参数 · 104.2B 激活参数 · 93 层 · 最长 1M token；据报告 pp.3、11 重绘")
box(ax,.25,5.35,2.35,1.1,"文字 / 图像 / 视频",BLUE,LIGHT)
arrow(ax,(2.65,5.9),(3.2,5.9))
box(ax,3.25,5.35,3.25,1.1,"共享表示空间\n视觉：MoonViT-V2 + MLP",BLUE,LIGHT)
arrow(ax,(6.55,5.9),(7.1,5.9))
box(ax,7.15,5.35,6.25,1.1,"23 × [3 KDA + 1 Gated MLA] + 末尾 MLA",size=17)
for x,title,body,col,fill in [(.25,"序列方向","KDA：更新压缩记忆\nMLA：全局内容交互",BLUE,LIGHT),(4.9,"深度方向","AttnRes：选择早期表示\n块内累加，块间加权",TEAL,PALE),(9.55,"通道方向","Stable LatentMoE\n896 选 16 + 2 共享专家",AMBER,"#fff2dc")]:
    box(ax,x,2.1,4.2,2.3,title+"\n\n"+body,col,fill)
    arrow(ax,(x+2.1,5.1),(x+2.1,4.5),col)
box(ax,.5,.4,12.65,1,"容量与长任务能力还依赖：训练数据 + 多预算 RL + 可恢复环境 + 缓存与调度",size=18)
save(fig,"01-overview")

fig, ax = canvas("02  KDA：按误差修正记忆", "教学例子：单头、两键通道、单值通道；忽略卷积与输出门。对应 Eq.1，p.4")
for x,lab,body in [(.25,"旧记忆","S = [2, 4]"),(3.65,"逐通道衰减","A = [1.6, 2]"),(7.05,"读取旧预测","k = [1, 0]\n预测值 = 1.6"),(10.45,"修正后记忆","S 新 = [2.3, 2]")]:
    box(ax,x,3.85,3.05,1.8,lab+"\n"+body,size=18)
for x in [3.35,6.75,10.15]: arrow(ax,(x,4.75),(x+.25,4.75))
note(ax,3.47,3.25,"α = [0.8, 0.5]",size=16)
note(ax,9,3.05,"目标 v = 3；误差 e = 3 − 1.6 = 1.4\nβ = 0.5；只沿当前键方向写入 0.7",size=18,color=TEAL)
box(ax,.7,.6,12.5,1.25,"A = Diag(α) S 旧       e = v − Aᵀ k       S 新 = A + β k eᵀ\n最后用当前查询 q 从更新后的 S 读取输出",BLUE,LIGHT,size=19)
save(fig,"02-kda-update")

fig, ax = canvas("03  AttnRes：从累加到选择性读取", "教学结构；右侧权重为示意，不是模型观测值。实际使用 Block AttnRes，原文 p.6")
note(ax,3.4,6.5,"普通残差",size=21,color=BLUE)
note(ax,10.4,6.5,"Block AttnRes",size=21,color=TEAL)
for y,label in [(5.05,"前层输出"),(3.15,"继续相加"),(1.25,"后层读取混合状态")]:
    box(ax,1,y,4.8,1,label,BLUE,LIGHT)
arrow(ax,(3.4,5),(3.4,4.22));arrow(ax,(3.4,3.1),(3.4,2.3))
for y,lab in [(5.3,"Embedding"),(3.9,"早期块表示"),(2.5,"近期块 / 当前部分和")]:box(ax,7.05,y,3.2,.85,lab,size=16)
box(ax,11,3.4,2.45,1.4,"打分 + softmax\n加权求和",size=16)
for y,v in [(5.72,"0.2"),(4.32,"0.5"),(2.92,"0.3")]:
    arrow(ax,(10.3,y),(10.95,4.1),TEAL)
    note(ax,10.6,y,v,size=13,color=TEAL)
note(ax,10.3,1.55,"块内仍求和；保留少量块级来源\n降低表示存储和跨阶段通信",size=17)
save(fig,"03-attnres")

fig, ax = canvas("04  MoE：容量、专家负载与设备负载", "上部为 K3 路由路径；下部为教学例子。QB 与 MoonEP 处理不同层面的平衡，pp.7–9、19–20")
box(ax,.25,5.2,2,1.1,"x：7168 维",BLUE,LIGHT)
box(ax,3,5.2,2.3,1.1,"降维到 3584",BLUE,LIGHT)
box(ax,6.05,5.2,3.2,1.1,"896 专家中选 16",TEAL,PALE)
box(ax,10,5.2,3.7,1.1,"加权汇合 → Norm\n升维回 7168",TEAL,PALE)
for x in [2.3,5.35,9.3]:arrow(ax,(x,5.75),(x+.65,5.75))
note(ax,6.9,4.45,"另有 2 个共享专家直接处理全宽输入，与路由输出相加",size=17)
box(ax,.3,.65,6.3,3.05,"QB：专家是否得到合理训练？\n\n8 token / 4 专家 / Top-1\n负载 [4,3,1,0] → 目标 [2,2,2,2]\n通过统计分位数更新下一步路由偏置",size=18)
box(ax,7.15,.65,6.3,3.05,"MoonEP：设备工作量是否相同？\n\n将热门专家复制到空闲设备执行\n相同权重的副本，梯度回收到原属设备\n物理调度不增加逻辑专家数量",AMBER,"#fff2dc",size=18)
save(fig,"04-moe-balance")

fig, axes = plt.subplots(1,2,figsize=(14,7.5))
fig.subplots_adjust(left=.075,right=.96,bottom=.16,top=.79,wspace=.27)
fig.text(.035,.94,"05  稳定化：控制衰减范围与激活增长",fontsize=25,color=NAVY,weight="bold")
fig.text(.035,.88,"公式曲线；A=0；右图两个分支取同一标量输入 x，非训练实测。对应 pp.5、7–8、43",fontsize=14,color=GRAY)
z=np.linspace(-8,8,400)
axes[0].plot(z,-np.logaddexp(0,z),label="旧：−softplus(z)",color=BLUE,lw=3)
axes[0].plot(z,-5/(1+np.exp(-z)),label="K3：−5 sigmoid(z)",color=TEAL,lw=3)
axes[0].axhline(-5,ls="--",color=AMBER,lw=1.7)
axes[0].text(-7.5,-5.7,"下界 −5；16 步累计大于 −80",fontsize=13,color=AMBER)
axes[0].set(xlabel="衰减 logit z",ylabel="每步 log-decay g",ylim=(-9,.4));axes[0].legend(fontsize=13,loc="lower left")
x=np.linspace(-10,50,600);sig=1/(1+np.exp(-x))
axes[1].plot(x,x*x*sig,label="SwiGLU 切片",color=BLUE,lw=3)
axes[1].plot(x,4*np.tanh(x/4)*sig*25*np.tanh(x/25),label="SiTU 切片",color=TEAL,lw=3)
axes[1].axhline(100,ls="--",color=AMBER,lw=1.7)
axes[1].set(xlabel="两分支标量输入 x",ylabel="激活输出（对称对数刻度）",yscale="symlog",ylim=(-1,3500));axes[1].legend(fontsize=13,loc="upper left")
for a in axes:a.grid(alpha=.18);a.spines[["top","right"]].set_visible(False)
fig.text(.075,.045,"有界的是单步衰减与逐元素激活；不代表整个网络的状态、输出或累计遗忘都受同样界限约束。",fontsize=14,color=GRAY)
save(fig,"05-stability")

fig, ax = canvas("06  后训练：九位教师与可恢复的长任务", "三个任务域 × low / high / max → 统一模型；下方为跨迭代 rollout 示意，pp.12–14、21–22")
box(ax,.2,4.2,1.8,1.2,"SFT\n冷启动策略",BLUE,LIGHT)
for y,d in [(5.55,"一般任务"),(4.35,"一般代理"),(3.15,"编程代理")]:
    box(ax,3,y,5.1,.85,d+"     low  /  high  /  max",size=17)
arrow(ax,(2.05,4.8),(2.85,4.8))
box(ax,9,4.2,4.6,1.2,"多教师 on-policy 蒸馏\n一个模型，按 effort 使用",size=18)
for y in [5.98,4.78,3.58]:arrow(ax,(8.15,y),(8.85,4.8),TEAL)
box(ax,.35,.4,4,1.45,"迭代 t：部分轨迹完成\n长轨迹暂停 → 策略更新",BLUE,LIGHT,size=17)
box(ax,4.95,.4,4,1.45,"保存：模型前缀状态\n+ 沙箱进程 / 文件状态",AMBER,"#fff2dc",size=17)
box(ax,9.55,.4,4,1.45,"迭代 t+1：优先恢复\n轨迹可能跨多个策略版本",size=17)
arrow(ax,(4.4,1.1),(4.85,1.1));arrow(ax,(9,1.1),(9.45,1.1))
save(fig,"06-posttraining")

fig, ax = canvas("07  KCP：每一段都是一个可组合的状态变换", "KDA 不能只把各段从零产生的状态相加；还要传播对输入状态的变换，Eq.17，p.18")
for x,i in [(.5,1),(5,2),(9.5,3)]:
    box(ax,x,4.2,3.8,1.8,f"设备 {i}：本地序列段\n独立计算 (M{i}, B{i})\nS 出 = M{i} S 入 + B{i}",size=18)
for x in [4.4,8.9]:arrow(ax,(x,5.1),(x+.45,5.1),TEAL)
box(ax,1,2.2,12,1.1,"有序前缀组合：(M₂M₁, M₂B₁ + B₂)\n具有结合律，可并行组合；一般不具有交换律",BLUE,LIGHT,size=19)
box(ax,1,.25,12,1.1,"标量教学例子：段1 = 0.5S + 2；段2 = 0.8S + 1\n两段合成 = 0.4S + 2.6；初始 S=3 时输出 3.8",size=18)
save(fig,"07-kcp")

fig, ax = canvas("08  前缀命中必须同时恢复 MLA 与 KDA", "沿用 Figure 12 的粒度示例；相同前缀长 2800 token，共同 checkpoint 位于 2560，pp.23–24")
x0, step = 1.35, .98
note(ax,.6,5.35,"MLA\nKV",size=18)
for i in range(12):
    ax.add_patch(Rectangle((x0+i*step,4.85),step-.035,1,facecolor=BLUE if i<5 else "#e1e7f0",edgecolor="white",linewidth=2))
    note(ax,x0+i*step+step/2,5.35,str(i+1),size=14,color="white" if i<5 else GRAY)
for i in [0,2,5,8,12]:
    note(ax,x0+i*step,4.4,str(i*512),size=13)
note(ax,7.1,6.35,"一个 6144-token 物理块 = 12 个 512-token 哈希块",size=19,color=NAVY)
note(ax,.6,3.25,"KDA\n状态",size=18)
for i in range(13):
    color=TEAL if i in [2,5] else "#b6c0cd"
    ax.plot(x0+i*step,3.25,"o",ms=15,mfc=color if i in [2,5] else "#f6f8fc",mec=color,mew=2)
ax.axvline(x0+5*step,ymin=.34,ymax=.87,ls="--",color=AMBER,lw=2)
note(ax,10.1,2.5,"实点：存在 checkpoint\n空心：此端点未保留",size=16)
arrow(ax,(x0+5*step,2.9),(x0+5*step,2.1),AMBER)
box(ax,1.3,.35,11.75,1.4,"在 B=2560 同时命中所有组，复制状态后继续 prefill\n前 2560 token 无需重算；剩余 240 个相同 token 仍需计算\n可复用边界 = MLA 匹配端点 ∩ 所有 KDA 组现存 checkpoint",AMBER,"#fff2dc",size=18)
save(fig,"08-prefix-cache")

labels=["CritPt","HLE 无工具","DeepSWE","ProgramBench","FrontierSWE","BrowseComp","AutomationBench","OSWorld 2.0"]
vals=np.array([[23.4,28.6,32.3],[43.5,53.3,44.5],[67.5,70,73],[77.8,76.8,77.6],[81.2,86.6,71.3],[91.2,88,90.4],[30.8,29.1,29.7],[58.3,66.1,62.6]])
fig, ax=plt.subplots(figsize=(14,10))
fig.subplots_adjust(left=.23,right=.95,bottom=.13,top=.83)
fig.text(.035,.95,"09  强项与短板：逐任务比较",fontsize=25,color=NAVY,weight="bold")
fig.text(.035,.895,"报告 Table 2，p.27；max / xhigh；Fable 含 fallback，GPT 含潜在 cyberguard 影响",fontsize=14,color=GRAY)
y=np.arange(len(labels))
for j,(name,col) in enumerate([("Kimi K3",TEAL),("Claude Fable 5",AMBER),("GPT-5.6 Sol",BLUE)]):
    yy=y+(j-1)*.24;ax.barh(yy,vals[:,j],height=.2,color=col,label=name)
    for k,v in enumerate(vals[:,j]):ax.text(v+1,yy[k],f"{v:.1f}",va="center",fontsize=11,color=col)
ax.set(yticks=y,yticklabels=labels,xlim=(0,100),xlabel="报告分数（每行独立比较，越高越好）")
ax.invert_yaxis();ax.legend(loc="upper center",bbox_to_anchor=(.5,1.1),ncol=3,fontsize=13)
ax.grid(axis="x",alpha=.18);ax.set_axisbelow(True);ax.spines[["top","right","left"]].set_visible(False)
fig.text(.035,.045,"BrowseComp 的 91.2 使用 300K 触发压缩；不同任务的指标含义与难度不同，不计算跨任务平均值。",fontsize=14,color=GRAY)
save(fig,"09-benchmarks")

fig,ax=plt.subplots(figsize=(14,7.5));fig.subplots_adjust(left=.27,right=.94,bottom=.2,top=.77)
fig.text(.035,.94,"10  工具增益：基础分数与工具分数一起看",fontsize=25,color=NAVY,weight="bold")
fig.text(.035,.88,"Kimi K3，报告 Table 2，p.27；HLE 使用一般工具，视觉任务使用 Python",fontsize=14,color=GRAY)
lab=["HLE-Full","MMMU-Pro","CharXiv RQ","Math-Vision","ZeroBench pass@5"]
base=np.array([43.5,81.6,84.8,94.3,23]);end=np.array([56,83.4,91.3,97.8,41]);y=np.arange(5)
ax.barh(y,base,color=BLUE,height=.44,label="无工具");ax.barh(y,end-base,left=base,color=TEAL,height=.44,label="工具增量")
for i,(a,b) in enumerate(zip(base,end)):
    ax.text(a-1.5,i,f"{a:.1f}",ha="right",va="center",color="white",fontsize=14)
    ax.text(b+1,i,f"{b:.1f}  (+{b-a:.1f})",va="center",fontsize=13,color=TEAL)
ax.set(yticks=y,yticklabels=lab,xlim=(0,117),xticks=[0,20,40,60,80,100],xlabel="分数；括号为百分点变化")
ax.invert_yaxis();ax.legend(loc="upper center",bbox_to_anchor=(.5,1.2),ncol=2,fontsize=14);ax.grid(axis="x",alpha=.18);ax.set_axisbelow(True);ax.spines[["top","right","left"]].set_visible(False)
fig.text(.035,.055,"ZeroBench 的 pass@5 是五次尝试指标，不是单次成功率。增益同时包含工具计算、观察与验证的作用。",fontsize=14,color=GRAY)
save(fig,"10-tool-gains")
print(f"Generated 10 SVG and 10 PNG figures in {args.output}")
