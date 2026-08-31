#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把日报内容 JSON 渲染成双栏 HTML 报纸。

用法：
    python3 render-html.py <content.json> <out.html>
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "newspaper.html")


def extract_iso_date(dateline):
    """从 '2026年8月27日 星期四' 提取 '2026-08-27'。"""
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", dateline or "")
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return ""


def paragraphs_to_html(paras):
    return "\n".join(f"<p>{p}</p>" for p in paras or [])


def render_sections(sections):
    blocks = []
    for sec in sections or []:
        items_html = []
        for it in sec.get("items", []):
            links = it.get("links") or []
            link_html = ""
            if links:
                link_html = f'<a class="src" href="{links[0][1]}">{links[0][1]}</a>'
            items_html.append(
                f'<div class="brief">\n'
                f'  <span class="who">{it.get("lead", "")}</span>\n'
                f'  <p>{it.get("body", "")}</p>\n'
                f'  {link_html}\n'
                f'</div>'
            )
        items_joined = "\n".join(items_html)
        blocks.append(
            f'<section class="block">\n'
            f'  <h3>{sec.get("name", "").replace("【", "").replace("】", "")}</h3>\n'
            f'  {items_joined}\n'
            f'</section>'
        )
    return "\n".join(blocks)


def render_quotes(quotes):
    figures = []
    for q in quotes or []:
        figures.append(
            f'<figure class="q">\n'
            f'  <blockquote>{q.get("quote", "")}</blockquote>\n'
            f'  <figcaption>\n'
            f'    —— {q.get("attrib", "")}\n'
            f'    <span class="cn">{q.get("zh", "")}</span>\n'
            f'    <a href="{q.get("link", "")}">{q.get("link", "")}</a>\n'
            f'  </figcaption>\n'
            f'</figure>'
        )
    return "\n".join(figures)


def render_feature(feature):
    paras = feature.get("paras", [])
    takeaway = paras[0] if paras else ""
    body = paragraphs_to_html(paras[1:] if paras else [])
    links = feature.get("links") or []
    url = links[0][1] if links else ""
    return (
        f'<article class="deep">\n'
        f'  <span class="tag">深度</span>\n'
        f'  <h3>{feature.get("title", "")}</h3>\n'
        f'  <p class="show">{feature.get("deck", "")}</p>\n'
        f'  <div class="deep-body">\n'
        f'    <p class="takeaway">{takeaway}</p>\n'
        f'    {body}\n'
        f'    <p><a class="src" href="{url}">{url}</a></p>\n'
        f'  </div>\n'
        f'</article>'
    )


def build_html(data):
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        tpl = f.read()

    dateline = data.get("dateline", "")
    iso = extract_iso_date(dateline)
    headline = data.get("headline", {})
    lead_links = headline.get("links") or []
    lead_url = lead_links[0][1] if lead_links else ""

    replacements = {
        "DATE_CN": dateline,
        "DATE_ISO": iso,
        "ISSUE_META": data.get("stats", ""),
        "LEAD_KICKER": "头条",
        "LEAD_TITLE": headline.get("title", ""),
        "LEAD_LEDE": headline.get("deck", ""),
        "LEAD_BODY": paragraphs_to_html(headline.get("paras", [])),
        "LEAD_URL": lead_url,
        "SECTIONS": render_sections(data.get("sections", [])),
        "QUOTES": render_quotes(data.get("quotes", [])),
    }

    for key, val in replacements.items():
        tpl = tpl.replace(f"{{{{{key}}}}}", val)

    features = data.get("features", [])
    if features:
        deep_html = render_feature(features[0])
        tpl = re.sub(
            r"<article class=\"deep\">.*?</article>",
            deep_html,
            tpl,
            flags=re.DOTALL,
            count=1,
        )
    else:
        # 没有深度稿时删除整块及前后的空行
        tpl = re.sub(
            r"\s*<article class=\"deep\">.*?</article>\s*",
            "\n\n",
            tpl,
            flags=re.DOTALL,
            count=1,
        )

    return tpl


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    html = build_html(data)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(html)
    print("ok ->", dst)


if __name__ == "__main__":
    main()
