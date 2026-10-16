# 学习记录

这里保存博客文章对应的可编辑 Markdown，以及不依赖收费 API 的学习示例。

| 日期 | 主题 | 记录与练习 |
| --- | --- | --- |
| 2026-10-16 | Jev 决策模型、概率校准与工程实践 | [学习记录](2026-10-16-jev-decision-models.md) · [博客文章](https://oneDuter.github.io/2026/10/16/learning/jev-decision-models/) · [校准练习](examples/jev_calibration_demo.py) |

本仓库保存的是 Hexo 生成后的静态站点，没有原始 Hexo 项目。此篇文章采用仓库现有页面样式发布，Markdown 是本篇记录的编辑源；后续若从其他 Hexo 源项目重新生成站点，应先把这篇文章迁回该源项目，避免覆盖手工增加的内容。

本次只公开整理、纠错与补充后的技术记录，原始会议 PDF 不纳入仓库。未核实的架构、价格、发布日期和评测说法在记录中单独标注。

运行示例：

```bash
python3 learning-notes/examples/jev_calibration_demo.py --self-test
python3 learning-notes/examples/jev_calibration_demo.py
```

更新 Markdown 后，使用专用虚拟环境安装渲染依赖，再重新生成这篇文章及其首页、归档、机器学习分类/标签和搜索索引入口：

```bash
python3 -m venv /tmp/jev-note-render
/tmp/jev-note-render/bin/python -m pip install -r tools/requirements-learning-notes.txt
/tmp/jev-note-render/bin/python tools/publish_jev_note.py
```

渲染器使用原生 MathML 展示公式，无需额外加载数学排版 CDN。流程图的 SVG 已提交；修改 `.dot` 源文件后，可用 Graphviz 重新生成：

```bash
dot -Tsvg learning-notes/jev-decision-flow.dot -o img/learning-notes/jev-decision-flow.svg
```
