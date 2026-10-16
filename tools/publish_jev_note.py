"""Render the editable Jev note into this already-generated static blog.

This updates only the article and its discovery pages. Managed blocks make
repeated runs idempotent, without regenerating unrelated historical pages.
Install requirements-learning-notes.txt first. Graphviz is only needed when
changing the separately committed diagram source, not for this renderer.
"""

from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit

import markdown
from latex2mathml.converter import convert
from markdown.extensions.toc import slugify_unicode

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / "learning-notes/2026-10-16-jev-decision-models.md"
ROUTE = "/2026/10/16/learning/jev-decision-models/"
SITE = "https://oneDuter.github.io"
TITLE = "Jev 决策模型学习记录：原理、概率校准与工程实践"
DESCRIPTION = "基于技术分享转写整理，纠正概率、ECE、Brier 与温度校准概念，比较开源路线，补充智能体评测与可运行练习。"
COVER = "/img/learning-notes/jev-decision-flow.svg"
DATE = "2026-10-16"
ISO_DATE = "2026-10-16T00:00:00+08:00"
CATEGORY = "/categories/" + quote("机器学习") + "/"
TAG = "/tags/" + quote("机器学习") + "/"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class ElementSpans(HTMLParser):
    """Locate original text spans, preserving unrelated generated HTML byte-for-byte."""

    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0]
        for match in re.finditer("\n", source):
            self.lines.append(match.end())
        self.stack: list[tuple[str, dict[str, str | None], int, int]] = []
        self.elements: list[tuple[str, dict[str, str | None], int, int, int, int]] = []
        self.feed(source)

    def source_offset(self) -> int:
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            start = self.source_offset()
            self.stack.append((tag, dict(attrs), start, start + len(self.get_starttag_text())))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                opened_tag, attrs, start, inner_start = self.stack[i]
                end_start = self.source_offset()
                end = self.source.index(">", end_start) + 1
                self.elements.append((opened_tag, attrs, start, inner_start, end_start, end))
                del self.stack[i:]
                break

    def locate(self, *, element_id=None, class_name=None, tag=None):
        matches = []
        for item in self.elements:
            element_tag, attrs = item[:2]
            if element_id is not None and attrs.get("id") != element_id:
                continue
            if class_name is not None and class_name not in (attrs.get("class") or "").split():
                continue
            if tag is not None and element_tag != tag:
                continue
            matches.append(item)
        if len(matches) != 1:
            raise ValueError(f"Expected one element: {element_id=}, {class_name=}, {tag=}; found {len(matches)}")
        return matches[0]


def replace_element(source, replacement, *, inner=False, **selector):
    item = ElementSpans(source).locate(**selector)
    start, end = (item[3], item[4]) if inner else (item[2], item[5])
    return source[:start] + replacement + source[end:]


def managed(source, key, content, *, container_id=None, container_class=None, xml=False):
    begin, end = f"<!-- jev-note:{key}:start -->", f"<!-- jev-note:{key}:end -->"
    source = re.sub(re.escape(begin) + r".*?" + re.escape(end), "", source, flags=re.S)
    block = begin + content + end
    if xml:
        match = re.search(r"<search\b[^>]*>[ \t]*", source)
        if not match:
            raise ValueError("Missing search root")
        offset = match.end()
    else:
        offset = ElementSpans(source).locate(element_id=container_id, class_name=container_class)[3]
    return source[:offset] + block + source[offset:]


def metadata(source, page_title, route, description=DESCRIPTION):
    source = re.sub(r"<title>.*?</title>", "<title>" + html.escape(page_title) + " | 早起星人</title>", source, count=1, flags=re.S)
    values = {
        "description": description, "og:title": page_title, "og:url": SITE + route,
        "og:description": description, "og:image": SITE + COVER,
        "twitter:image": SITE + COVER, "article:published_time": ISO_DATE,
        "article:modified_time": ISO_DATE, "article:tag": "机器学习",
    }

    def change_meta(match):
        tag = match.group()
        key = re.search(r'(?:name|property)="([^"]+)"', tag)
        if key and key[1] in values:
            tag = re.sub(r'content="[^"]*"', 'content="' + html.escape(values[key[1]], quote=True) + '"', tag)
        return tag

    source = re.sub(r"<meta\b[^>]*>", change_meta, source)
    source = re.sub(r'<link\b[^>]*rel="canonical"[^>]*>', '<link rel="canonical" href="' + SITE + route + '">', source)
    return source


def render_markdown():
    original = NOTE.read_text()
    source = original.split("\n", 1)[1]  # The article header already carries the H1.
    chunks = re.split(r"(^```[^\n]*\n.*?^```[ \t]*$)", source, flags=re.M | re.S)
    for index in range(0, len(chunks), 2):
        text = re.sub(
            r"\$\$\s*\n(.*?)\n\s*\$\$",
            lambda match: '<div class="math-display">' + convert(match[1].strip(), display="block") + "</div>",
            chunks[index], flags=re.S,
        )
        chunks[index] = re.sub(
            r"(?<!\\)\$(?!\$)([^\n$]+?)(?<!\\)\$",
            lambda match: convert(match[1], display="inline"), text,
        )
    renderer = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        extension_configs={"toc": {"slugify": slugify_unicode}},
    )
    content = renderer.convert("".join(chunks))

    def rewrite_link(match):
        attribute, value = match[1], html.unescape(match[2])
        if value.startswith(("/", "#")) or urlsplit(value).scheme:
            return match.group()
        path = (NOTE.parent / value).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError(f"Relative link leaves checkout: {value}")
        relative = path.relative_to(ROOT).as_posix()
        destination = (
            "https://github.com/oneDuter/oneDuter.github.io/blob/main/" + quote(relative)
            if path.suffix in {".md", ".py", ".dot"} else "/" + quote(relative)
        )
        return attribute + '="' + destination + '"'

    content = re.sub(r'(href|src)="([^"]+)"', rewrite_link, content)
    return content, renderer.toc_tokens


def toc_html(tokens, child=False):
    result = '<ol class="toc-child">' if child else '<ol class="toc">'
    for token in tokens:
        result += (
            '<li class="toc-item toc-level-' + str(token["level"]) + '"><a class="toc-link" href="#'
            + quote(token["id"]) + '"><span class="toc-text">' + html.escape(token["name"]) + "</span></a>"
        )
        if token.get("children"):
            result += toc_html(token["children"], True)
        result += "</li>"
    return result + "</ol>"


def listing_item():
    return (
        '<div class="article-sort-item"><a class="article-sort-item-img" href="' + ROUTE
        + '" title="' + html.escape(TITLE) + '"><img src="' + COVER + '" alt="Jev 决策模型学习记录"></a>'
        + '<div class="article-sort-item-info"><div class="article-sort-item-time"><time class="post-meta-date-created" datetime="'
        + ISO_DATE + '">' + DATE + '</time></div><a class="article-sort-item-title" href="' + ROUTE + '">'
        + html.escape(TITLE) + "</a></div></div>"
    )


def refresh_counts(source, total):
    source = re.sub(r'(<a href="/archives/"><div class="headline">Articles</div><div class="length-num">)\d+(</div>)',
                    lambda match: match[1] + str(total) + match[2], source)
    category_pattern = r'(<a[^>]*href="' + re.escape(CATEGORY) + r'"[^>]*>机器学习</a><span class="category-list-count">)\d+(</span>)'
    source = re.sub(category_pattern, lambda match: match[1] + "2" + match[2], source)
    return source


def add_archive_widget(source):
    if 'class="card-archive-list"' not in source:
        return source
    item = ('<li class="card-archive-list-item"><a class="card-archive-list-link" href="/archives/2026/10/">'
            '<span class="card-archive-list-date">十月 2026</span><span class="card-archive-list-count">1</span></a></li>')
    return managed(source, "archive-widget", item, container_class="card-archive-list")


def write(relative, content, *, clean_lines=False):
    if clean_lines:
        content = re.sub(r"[ \t]+$", "", content, flags=re.M)
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != content:
        path.write_text(content)
        print(relative)


def main():
    content, toc = render_markdown()
    search = (ROOT / "search.xml").read_text()
    entry = (
        "\n<entry><title>" + html.escape(TITLE) + '</title><link href="' + ROUTE + '"/><url>' + ROUTE
        + '</url><content type="html"><![CDATA[' + content.replace("]]>", "]]]]><![CDATA[>") + "]]></content></entry>\n"
    )
    search = managed(search, "search", entry, xml=True)
    total = len(ET.fromstring(search).findall("entry"))

    page = (ROOT / "2023/07/13/Java/Spring/index.html").read_text()
    page = metadata(page, TITLE, ROUTE)
    page = replace_element(page, content, element_id="article-container", inner=True)
    info = ('<h1 class="post-title">' + html.escape(TITLE) + '</h1><div id="post-meta"><time datetime="'
            + ISO_DATE + '">' + DATE + '</time> · <a href="' + CATEGORY + '">机器学习</a> · '
            '<a href="https://github.com/oneDuter/oneDuter.github.io/blob/main/learning-notes/2026-10-16-jev-decision-models.md">Markdown 学习记录</a></div>')
    page = replace_element(page, info, element_id="post-info", inner=True)
    for class_name in ("post-copyright", "tag_share", "post-reward", "pagination-post", "relatedPosts"):
        page = replace_element(page, "", class_name=class_name)
    page = replace_element(page,
        '<div class="card-widget" id="card-toc"><div class="item-headline">文章目录</div>'
        '<div class="toc-content is-expand">' + toc_html(toc) + '</div></div>', element_id="card-toc")
    config = {"title": TITLE, "isPost": True, "isHome": False, "isHighlightShrink": False,
              "isToc": True, "postUpdate": "2026-10-16 00:00:00"}
    page = replace_element(page, 'var GLOBAL_CONFIG_SITE = ' + json.dumps(config, ensure_ascii=False), element_id="config-diff", inner=True)
    page = re.sub(r'(<header[^>]*id="page-header"[^>]*\s)style="[^"]*"',
                  r'\1style="background:linear-gradient(120deg,#142f45,#356d83)"', page, count=1)
    avatar_name = quote("微信图片_20230511141236.png")
    page = page.replace("https://lgj-duter.oss-cn-beijing.aliyuncs.com/img/" + avatar_name, "/img/" + avatar_name)
    page = re.sub(r'<link\b[^>]*rel="shortcut icon"[^>]*>', '<link rel="shortcut icon" href="/img/favicon.png">', page, count=1)
    styles = ('<style>#article-container .math-display{overflow-x:auto;margin:1.4em 0;padding:.3em 0}'
              '#article-container math{font-size:1.08em}#article-container pre{overflow:auto;padding:1em;border-radius:6px;background:var(--hl-bg,#f4f6f8)}'
              '#article-container td,#article-container th{vertical-align:top}#article-container img{max-height:750px;object-fit:contain}'
              '#post-meta{line-height:2}#post-meta a{color:inherit;text-decoration:underline}'
              '@media(max-width:600px){#post-info .post-title{font-size:24px;line-height:1.5;text-wrap:balance}}</style>')
    page = page.replace("</head>", styles + "</head>", 1)
    page = add_archive_widget(refresh_counts(page, total))
    write(ROUTE.strip("/") + "/index.html", page, clean_lines=True)

    home = (ROOT / "index.html").read_text()
    card = ('<div class="recent-post-item"><div class="post_cover left"><a href="' + ROUTE + '"><img class="post-bg" src="'
            + COVER + '" alt="Jev 决策模型学习记录"></a></div><div class="recent-post-info"><a class="article-title" href="' + ROUTE
            + '">' + html.escape(TITLE) + '</a><div class="article-meta-wrap"><time datetime="' + ISO_DATE + '">' + DATE
            + '</time> · <a href="' + CATEGORY + '">机器学习</a></div><div class="content">' + DESCRIPTION + '</div></div></div>')
    home = managed(home, "home", card, container_id="recent-posts")
    write("index.html", add_archive_widget(refresh_counts(home, total)))

    group = '<div class="article-sort-item year"><a href="/archives/2026/">2026</a></div>' + listing_item()
    for relative in ("archives/index.html", "categories/机器学习/index.html", "tags/机器学习/index.html"):
        collection = (ROOT / relative).read_text()
        collection = managed(collection, "listing", group, container_class="article-sort")
        if relative == "archives/index.html":
            collection = replace_element(collection, "Articles - " + str(total), class_name="article-sort-title", inner=True)
        write(relative, add_archive_widget(refresh_counts(collection, total)))

    archive = (ROOT / "archives/index.html").read_text()
    for relative, route, heading in (
        ("archives/2026/index.html", "/archives/2026/", "2026"),
        ("archives/2026/10/index.html", "/archives/2026/10/", "十月 2026"),
    ):
        collection = metadata(archive, heading, route, "2026 年 Jev 决策模型学习记录归档")
        collection = replace_element(collection, heading, element_id="site-title", inner=True)
        collection = replace_element(collection, group, class_name="article-sort", inner=True)
        collection = replace_element(collection, "Articles - 1", class_name="article-sort-title", inner=True)
        collection = replace_element(collection, "", element_id="pagination")
        write(relative, collection, clean_lines=True)

    categories = (ROOT / "categories/index.html").read_text()
    write("categories/index.html", add_archive_widget(refresh_counts(categories, total)))
    write("search.xml", search)


if __name__ == "__main__":
    main()
