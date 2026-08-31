#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把日报内容 JSON 渲染成钉钉文档报纸版 JSONML。

用法：
    python3 build-dingdoc-jsonml.py <content.json> <out.json>
    dws doc update --node <DOC_ID> --content-file <out.json> --content-format jsonml --mode overwrite

content.json 结构见 ~/.follow-builders/prompts/digest-intro.md「报纸版内容 JSON」一节。
"""
import json
import sys

INK = "#1A1A1A"
GREY = "#6B6B6B"
RED = "#8C1C13"
PAPER = "#F7F4ED"
RULE = "#D8D2C4"

_seq = [0]


def uid(prefix="n"):
    _seq[0] += 1
    return "%s%d" % (prefix, _seq[0])


def leaf(text, **attrs):
    a = {"data-type": "leaf"}
    a.update(attrs)
    return ["span", a, text]


def text_run(*leaves):
    return ["span", {"data-type": "text"}, *leaves]


def para(leaves, tag="p", **attrs):
    a = {"uuid": uid("p")}
    a.update(attrs)
    return [tag, a, text_run(*leaves)]


def spaced(s, gap="\u2009"):
    """字间距：用窄空格拉开标题，报头/栏目名用。"""
    return gap.join(list(s))


def anchor(label, href):
    """a 节点的子元素必须是 text/leaf 三层结构，裸字符串会被服务端拒绝。"""
    return ["a", {"href": href},
            text_run(leaf(label, sz=9, szUnit="pt", color=RED))]


def link_para(links, align=None):
    """一行内并排放多个链接，用 · 分隔。"""
    a = {"uuid": uid("p")}
    if align:
        a["jc"] = align
    kids = [text_run(leaf("", sz=9, szUnit="pt"))]
    for i, (label, href) in enumerate(links):
        if i:
            kids.append(text_run(leaf("  ·  ", sz=9, szUnit="pt", color=GREY)))
        kids.append(anchor(label, href))
    return ["p", a, *kids]


def hr():
    return ["hr", {"uuid": uid("hr")}]


def cell(blocks):
    return ["tc", {"uuid": uid("tc"), "colSpan": 1, "rowSpan": 1}, *blocks]


def columns(col_blocks, widths=None):
    n = len(col_blocks)
    widths = widths or [int(660 / n)] * n
    return ["table", {"uuid": uid("cols"), "sr": True, "colsWidth": widths},
            ["tr", {"uuid": uid("tr")}, *[cell(b) for b in col_blocks]]]


def callout(blocks, bg=PAPER, border=RULE):
    return ["container",
            {"uuid": uid("co"), "subType": "colorBlocks",
             "metadata": {"bgcolor": bg, "border": border}},
            *blocks]


# ---------- 版面构件 ----------

def masthead(d):
    out = [hr()]
    out.append(para([leaf(spaced(d["masthead"]), bold=True, sz=26, szUnit="pt",
                          color=INK)], jc="center"))
    out.append(para([leaf(d["dateline"] + "　·　" + d["stats"], sz=9,
                          szUnit="pt", color=GREY)], jc="center"))
    out.append(hr())
    return out


def section_head(name):
    return [para([leaf(spaced(name), bold=True, sz=12, szUnit="pt", color=RED)],
                 jc="center", spacing={"before": 16, "after": 4}),
            hr()]


def headline(h):
    out = [para([leaf(h["title"], bold=True, sz=20, szUnit="pt", color=INK)],
                jc="center")]
    if h.get("deck"):
        out.append(para([leaf(h["deck"], italic=True, sz=11, szUnit="pt",
                              color=GREY)], jc="center"))
    body = [para([leaf(p, sz=11, szUnit="pt", color=INK)]) for p in h["paras"]]
    half = (len(body) + 1) // 2
    left, right = body[:half], body[half:]
    if right:
        out.append(columns([left, right], widths=[330, 330]))
    else:
        out.extend(left)
    if h.get("links"):
        out.append(link_para(h["links"], align="center"))
    return out


def wire_item(it):
    blocks = [para([leaf(it["lead"], bold=True, sz=11, szUnit="pt", color=INK),
                    leaf("　" + it["body"], sz=10, szUnit="pt", color=INK)],
                   spacing={"before": 10})]
    if it.get("links"):
        blocks.append(link_para(it["links"]))
    return blocks


def wire_section(sec):
    out = section_head(sec["name"])
    items = sec["items"]
    if sec.get("layout") == "columns" and len(items) > 1:
        flat = [wire_item(i) for i in items]
        half = (len(flat) + 1) // 2
        left = [b for grp in flat[:half] for b in grp]
        right = [b for grp in flat[half:] for b in grp]
        out.append(columns([left, right], widths=[330, 330]))
    else:
        for it in items:
            out.extend(wire_item(it))
    return out


def feature(f):
    out = section_head(f.get("name", "深度"))
    out.append(para([leaf(f["title"], bold=True, sz=15, szUnit="pt", color=INK)]))
    if f.get("deck"):
        out.append(para([leaf(f["deck"], italic=True, sz=10, szUnit="pt",
                             color=GREY)]))
    body = [para([leaf(p, sz=10, szUnit="pt", color=INK)]) for p in f["paras"]]
    half = (len(body) + 1) // 2
    out.append(columns([body[:half], body[half:]], widths=[330, 330]))
    if f.get("links"):
        out.append(link_para(f["links"]))
    return out


def quotes(qs):
    out = section_head("今日金句")
    blocks = []
    for i, q in enumerate(qs):
        if i:
            blocks.append(para([leaf("", sz=6, szUnit="pt")]))
        blocks.append(para([leaf("\u201c" + q["quote"] + "\u201d", italic=True,
                                 sz=12, szUnit="pt", color=INK)],
                           blockquote=True))
        blocks.append(para([leaf("\u2014\u2014 " + q["attrib"], bold=True, sz=9,
                                 szUnit="pt", color=RED),
                            leaf("　" + q["zh"], sz=9, szUnit="pt", color=GREY)]))
        if q.get("link"):
            blocks.append(link_para([("原文", q["link"])]))
    out.append(callout(blocks))
    return out


def colophon(c):
    return [hr(),
            para([leaf(c, sz=8, szUnit="pt", color=GREY)], jc="center")]


def build(d):
    root = ["root", {"sectPr": {}}]
    root += masthead(d)
    root += headline(d["headline"])
    for sec in d.get("sections", []):
        root += wire_section(sec)
    for f in d.get("features", []):
        root += feature(f)
    if d.get("quotes"):
        root += quotes(d["quotes"])
    root += colophon(d.get("colophon", ""))
    return {"jsonml": root}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(build(data), f, ensure_ascii=False)
    print("ok ->", dst)


if __name__ == "__main__":
    main()
