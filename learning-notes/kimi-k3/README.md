# Kimi K3 解读配套资料

[中文解读](../2026-10-16-kimi-k3-deep-dive.md) · [博客文章](https://oneDuter.github.io/2026/10/16/learning/kimi-k3-deep-dive/)

图示由代码重新绘制。教学数字与函数切片不是模型内部测量；评测图依据报告的 Table 2，p.27。CSV 保留相应设置，价格与排名不作为实时信息。

| 图示 | 内容 | 报告依据 |
| --- | --- | --- |
| 01 | 三种信息流与架构 | pp.3、11 |
| 02 | KDA 误差更新玩具例子 | p.4 |
| 03 | Block AttnRes | p.6 |
| 04 | LatentMoE 与两种负载平衡 | pp.7–9、19–20 |
| 05 | 衰减门与 SiTU 的函数曲线 | pp.5、7–8、43 |
| 06 | 九位教师与 rollout 恢复 | pp.12–14、21–22 |
| 07 | KCP 仿射状态组合 | p.18 |
| 08 | 混合前缀缓存 | pp.23–24 |
| 09 | 部分任务的三模型比较 | p.27 |
| 10 | 有无工具的比较 | p.27 |

SVG 和 PNG 位于 [img/learning-notes/kimi-k3](../../img/learning-notes/kimi-k3/)。SVG 保留文本，可编辑并无损缩放；PNG 便于下载分享。生成脚本需要 Python、matplotlib、numpy 以及中文字体：

```bash
python3 tools/generate_kimi_k3_figures.py
# Linux 可指定字体
python3 tools/generate_kimi_k3_figures.py --font /path/to/NotoSansCJK-Regular.ttc
```

文章继续使用仓库已有 Markdown 与原生 MathML 渲染方式：

新文章另存小型 `search-kimi-k3.json` 搜索索引，搜索脚本将其与历史 `search.xml` 合并，并按 URL 去重。补充索引请求失败时，旧文搜索仍可用。

```bash
python3 -m pip install -r tools/requirements-learning-notes.txt
python3 tools/publish_kimi_k3_note.py
```

此仓库是已生成的 Hexo 静态站点；重新从外部源项目生成站点前，应迁入这些新增文章和图示。若同时运行两篇学习笔记的专用渲染器，先运行 `publish_jev_note.py`，再运行 `publish_kimi_k3_note.py`，以保留新文章的归档入口。脚本只生成文件，不执行 GitHub 上传。

原文：[官方报告](https://github.com/MoonshotAI/Kimi-K3/blob/main/k3_tech_report.pdf)。原报告版权与模型许可属于作者；这里上传解读、数据摘录和教学重绘，不包含原 PDF。

核对版本：47 页；源 PDF 的 SHA-256 为 `1a21e4d15de52eb0d4cf09cdbffc6248c497ba6897572cc5574af237c13da51d`。
