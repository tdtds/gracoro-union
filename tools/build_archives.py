#!/usr/bin/env python3
"""
アーカイブページ (2011-2022) の静的生成

views/archive{year}.haml (その年の紹介文) と data/people.{year}.json (最終集計) から、
現行サイト (Sinatra 版) の描画結果と等価な静的 HTML を生成する。
GitHub Actions のデプロイ workflow から _site へ向けて実行される。

使い方:
  python3 tools/build_archives.py --out-dir _site
"""
import argparse
import html
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
YEARS = list(range(2011, 2023))

A_TAG = re.compile(r"^%a\{href: '([^']+)'(, target: '_blank')?\}<(.*)$")

PAGE = """<!DOCTYPE html>
<html>
<head>
<title>グラコロ同盟 {year}</title>
<meta content='https://gracoro.tdtds.jp/img/og-image.jpg' property='og:image'>
<link href='css/default.css' media='all' rel='stylesheet' type='text/css'>
<link href='img/gracoro20x20.png' rel='icon'>
</head>
<body>
<h1>
<img alt='グラコロ同盟{year}' src='img/gracoro_union{year}.jpg'>
</h1>
<div id='header'>
<div id='description'>
{intro}
</div>
</div>
<div id='main'>
<div class='archive' id='ranking'>
<h2>{year}年シーズンのランキング</h2>
<ol>
{items}
</ol>
</div>
</div>
{footer}</body>
</html>
"""

ITEM = """<li class='show'>
<a href='https://twitter.com/{name}'>
<img alt='{name}' src="{icon}">
</a>
<div>
{icons}<span>{count}</span>
</div>
</li>"""

ICON = "<img alt='' src='img/gracoro20x20.png'>\n"


def intro_html(year):
    src = (BASE / "views" / f"archive{year}.haml").read_text(encoding="utf-8")
    paras = []
    current = None
    for raw in src.splitlines():
        line = raw.strip()
        if line == "%p":
            current = []
            paras.append(current)
            continue
        if current is None:
            continue
        m = A_TAG.match(line)
        if m:
            href, target, text = m.group(1), m.group(2) or "", m.group(3)
            t = " target='_blank'" if target else ""
            current.append(f"<a href='{href}'{t}>{text}</a>")
        elif line:
            current.append(line)
    return "\n".join("<p>\n" + "\n".join(p) + "\n</p>" for p in paras)


def ranking_items(year):
    people = json.loads(
        (BASE / "data" / f"people.{year}.json").read_text(encoding="utf-8")
    )
    people = [p for p in people if p.get("count", 0) >= 1]
    people.sort(key=lambda p: -p["count"])
    items = []
    for p in people:
        # リポジトリ内の JSON エクスポートは http のまま古いが、現行 DB は https。
        # HTTPS のサイトで混在コンテンツにもなるため、twimg のアイコンは https に揃える
        icon = re.sub(r"^http://([a-z0-9]+\.twimg\.com/)", r"https://\1", p["icon"])
        items.append(
            ITEM.format(
                name=html.escape(p["name"], quote=True),
                icon=html.escape(icon, quote=True),
                icons=ICON * p["count"],
                count=p["count"],
            )
        )
    return "\n".join(items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    footer = (BASE / "tools" / "footer.html").read_text(encoding="utf-8")
    for year in YEARS:
        page = PAGE.format(
            year=year,
            intro=intro_html(year),
            items=ranking_items(year),
            footer=footer,
        )
        (out_dir / f"{year}.html").write_text(page, encoding="utf-8")
        print(f"generated {year}.html")


if __name__ == "__main__":
    main()
