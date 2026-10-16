"""Publish the Kimi K3 Markdown note into the existing generated Hexo site.

Uses the repository's existing Markdown/MathML renderer; creates only this
article and its discovery entries. Run after publish_jev_note.py if both notes
are rebuilt, because the older renderer regenerates the 2026 archive pages.
Requires tools/requirements-learning-notes.txt. Does not push or deploy.
"""
from __future__ import annotations
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote
import publish_jev_note as base

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / "learning-notes/2026-10-16-kimi-k3-deep-dive.md"
ROUTE = "/2026/10/16/learning/kimi-k3-deep-dive/"
TITLE = "Kimi K3 技术报告详解"
DESCRIPTION = "用 10 张原创图示解读 KDA、AttnRes、Stable LatentMoE、百万上下文强化学习和推理系统，并逐项说明评测条件与证据边界。"
COVER = "/img/learning-notes/kimi-k3/01-overview.svg"
ISO = "2026-10-16T16:00:00+08:00"
SOURCE_URL = "https://github.com/oneDuter/oneDuter.github.io/blob/main/learning-notes/2026-10-16-kimi-k3-deep-dive.md"

def write(path, content):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != content:
        path.write_text(content)
        print(path.relative_to(ROOT))

def strip_managed(source, key):
    begin, end = f"<!-- kimi-k3:{key}:start -->", f"<!-- kimi-k3:{key}:end -->"
    return re.sub(re.escape(begin)+r".*?"+re.escape(end), "", source, flags=re.S), begin, end

def insert(source, key, content, *, element_id=None, class_name=None, offset=None):
    source, begin, end = strip_managed(source, key)
    if offset is None:
        offset = base.ElementSpans(source).locate(element_id=element_id, class_name=class_name)[3]
    return source[:offset]+begin+content+end+source[offset:]

def refresh(source, total):
    source = re.sub(r'(<a href="/archives/"><div class="headline">Articles</div><div class="length-num">)\d+(</div>)',
                    lambda m:m[1]+str(total)+m[2], source)
    source = re.sub(r'(<span class="card-archive-list-date">十月 2026</span><span class="card-archive-list-count">)\d+(</span>)',
                    lambda m:m[1]+"2"+m[2], source)
    source = re.sub(r'(<a[^>]*href="'+re.escape(base.CATEGORY)+r'"[^>]*>机器学习</a><span class="category-list-count">)\d+(</span>)',
                    lambda m:m[1]+"3"+m[2], source)
    return source

def listing(source):
    source, begin, end = strip_managed(source,"listing")
    spans=base.ElementSpans(source)
    group=spans.locate(class_name="article-sort")
    years=[e for e in spans.elements if "year" in (e[1].get("class") or "").split()
           and group[3]<=e[2]<group[4] and "2026" in source[e[3]:e[4]]]
    offset=years[0][5] if years else group[3]
    year='' if years else '<div class="article-sort-item year">2026</div>'
    return source[:offset]+begin+year+base.listing_item()+end+source[offset:]

def main():
    for key,val in {"ROOT":ROOT,"NOTE":NOTE,"ROUTE":ROUTE,"TITLE":TITLE,"DESCRIPTION":DESCRIPTION,
                    "COVER":COVER,"ISO_DATE":ISO}.items(): setattr(base,key,val)
    content,toc=base.render_markdown()
    search=(ROOT/"search.xml").read_text()
    search,_,_=strip_managed(search,"search")
    xml=ET.fromstring(search)
    existing=xml.findall("entry")
    total=len(existing)+(0 if any(e.findtext("url")==ROUTE for e in existing) else 1)
    supplement=[{"title":TITLE,"content":content,"url":ROUTE}]
    write("search-kimi-k3.json",json.dumps(supplement,ensure_ascii=False,indent=2)+"\n")

    page=(ROOT/"2026/10/16/learning/jev-decision-models/index.html").read_text()
    page=base.metadata(page,TITLE,ROUTE)
    page=base.replace_element(page,content,element_id="article-container",inner=True)
    info='<h1 class="post-title">'+TITLE+'</h1><div id="post-meta"><time datetime="'+ISO+'">2026-10-16</time> · <a href="'+base.CATEGORY+'">机器学习</a> · <a href="'+SOURCE_URL+'">Markdown 原稿</a></div>'
    page=base.replace_element(page,info,element_id="post-info",inner=True)
    page=base.replace_element(page,'<div class="card-widget" id="card-toc"><div class="item-headline">文章目录</div><div class="toc-content is-expand">'+base.toc_html(toc)+'</div></div>',element_id="card-toc")
    config={"title":TITLE,"isPost":True,"isHome":False,"isHighlightShrink":False,"isToc":True,"postUpdate":"2026-10-16 16:00:00"}
    page=base.replace_element(page,'var GLOBAL_CONFIG_SITE = '+json.dumps(config,ensure_ascii=False),element_id="config-diff",inner=True)
    styles='<style id="kimi-k3-style">#article-container{font-size:17px;line-height:1.95}#article-container h2{margin-top:2.3em}#article-container img{max-height:none;width:100%;height:auto;border-radius:8px;background:#f6f8fc}#article-container .math-display{overflow-x:auto;padding:.7em 0}#article-container table{display:block;overflow:auto;font-size:15px}#article-container td,#article-container th{min-width:90px;white-space:normal}#article-container code{overflow-wrap:anywhere}@media(max-width:650px){#article-container{font-size:16px}#article-container math{font-size:.96em}#article-container table{font-size:14px}}</style>'
    page=page.replace("</head>",styles+"</head>",1)
    page=refresh(page,total)
    write(ROUTE.strip("/")+"/index.html",page)
    home=(ROOT/"index.html").read_text()
    card='<div class="recent-post-item"><div class="post_cover left"><a href="'+ROUTE+'"><img class="post-bg" src="'+COVER+'" alt="Kimi K3 技术报告详解架构图"></a></div><div class="recent-post-info"><a class="article-title" href="'+ROUTE+'">'+TITLE+'</a><div class="article-meta-wrap"><time datetime="'+ISO+'">2026-10-16</time> · <a href="'+base.CATEGORY+'">机器学习</a></div><div class="content">'+DESCRIPTION+'</div></div></div>'
    write("index.html",refresh(insert(home,"home",card,element_id="recent-posts"),total))
    for name in ["archives/index.html","archives/2026/index.html","archives/2026/10/index.html",
                 "categories/机器学习/index.html","tags/机器学习/index.html"]:
        source=listing((ROOT/name).read_text())
        if name.startswith("archives/"):
            count=2 if name!="archives/index.html" else total
            source=base.replace_element(source,"Articles - "+str(count),class_name="article-sort-title",inner=True)
        write(name,refresh(source,total))
    write("categories/index.html",refresh((ROOT/"categories/index.html").read_text(),total))
    write("search.xml",search)
    print(f"Validated historical search XML and supplement: {total} unique article routes.")

if __name__=="__main__":main()
