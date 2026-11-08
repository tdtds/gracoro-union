#!/usr/bin/env python3
"""
グラコロ同盟 公式サイト静的化ビルダー

現行サイト (Heroku/Sinatra) の描画済み HTML を取得し、死んでいる外部スクリプト
(Facebook SDK, 旧 Google Analytics, Twitter ウィジェット, jQuery) を除去して
site/ 以下に静的ページとして配置する。アーカイブとルールは内容が凍結しているため
この方式で十分。トップページは 2026 年用に新規生成する。

ランキング表示は site/standings.json (Muse の公式集計から毎時 push される) を
site/js/ranking.js が同一オリジンで読み込む方式。外部 API は呼ばない。

使い方:
  python3 tools/build_static.py [--raw-dir DIR] [--site-dir DIR]
  raw-dir に現行ページの HTML がなければ https://gracoro.tdtds.jp/ から取得する。
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

LIVE_BASE = "https://gracoro.tdtds.jp"
ARCHIVE_YEARS = list(range(2011, 2023))

CLEAN_PATTERNS = [
    # Facebook SDK (fb-root + 直後の script)
    (re.compile(r"<div id='fb-root'></div>\s*<script>.*?</script>", re.S), ""),
    # Twitter ウィジェット
    (re.compile(r"<script src='//platform\.twitter\.com/widgets\.js'></script>"), ""),
    # Facebook Like Box の li
    (re.compile(r"<li class='banner'>\s*<div class='fb-like-box'.*?</div>\s*</li>", re.S), ""),
    # 旧 Google Analytics (UA)
    (re.compile(r"<script>\s*var _gaq.*?</script>", re.S), ""),
    # jQuery 1.7 (静的化後は未使用)
    (re.compile(r"<script src='https://ajax\.googleapis\.com/ajax/libs/jquery/1\.7/jquery\.min\.js'></script>"), ""),
]


def fetch(name, raw_dir):
    p = raw_dir / f"{name}.html"
    if p.exists():
        return p.read_text(encoding="utf-8")
    url = f"{LIVE_BASE}/{name}"
    print(f"fetch {url}")
    with urllib.request.urlopen(url, timeout=30) as r:
        html = r.read().decode("utf-8")
    raw_dir.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    return html


# 絶対パス (/css/... 等) はドメイン直下でしか通用せず、GitHub Pages の
# プロジェクト配下 (tdtds.github.io/gracoro-union/) のステージングで壊れる。
# 全ページがサイトルートと同階層にあるため、相対パスに統一する。
RELATIVIZE = [
    ("href='/css/", "href='css/"),
    ("href='/img/", "href='img/"),
    ("src='/img/", "src='img/"),
    ("src='/js/", "src='js/"),
    ("href='/rule'", "href='rule'"),
    ("href='/'", "href='./'"),
]


def relativize(html):
    for a, b in RELATIVIZE:
        html = html.replace(a, b)
    return html


def clean(html):
    for pat, rep in CLEAN_PATTERNS:
        html = pat.sub(rep, html)
    return relativize(html)


def extract_footer(html):
    start = html.index("<div id='footer'>")
    end = html.rindex("</div>", 0, html.index("</body>")) + len("</div>")
    return html[start:end]


INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>グラコロ同盟2026</title>
<meta content='width=device-width,initial-scale=1' name='viewport'>
<meta content='https://gracoro.tdtds.jp/img/og-image.jpg' property='og:image'>
<link href='/css/default.css' media='all' rel='stylesheet' type='text/css'>
<link href='/css/site.css' media='all' rel='stylesheet' type='text/css'>
<link href='/img/gracoro20x20.png' rel='icon'>
<link href='/img/apple-touch-icon.png' rel='apple-touch-icon'>
<script defer src='/js/ranking.js'></script>
</head>
<body class='index'>
<h1>
<img alt='グラコロ同盟2026' src='/img/gracoro_union2023.jpg'>
</h1>
<div id='header'>
<div id='description'>
<p>
グラコロ同盟は、マクドナルド冬の定番メニュー「グラコロ」
(旧称「グラタンコロッケバーガー」)が大好きな人たちによるコミュニティです。
シーズン中はただひたすらグラコロを食べ、報告しあい、その数を競い合っています。
</p>
<p>
2026年シーズンは、近日開幕予定です。グラコロの発売日が発表され次第、ここでお知らせします。
今年も舞台は
<a href='https://bsky.app/' target='_blank'>Bluesky</a>
です。グラコロを食べた数だけハッシュタグ「#グラコロ同盟」をつけてPOSTするだけで、どなたでも参加できます。幸せな冬の数週間をいっしょに楽しみましょう！
</p>
<p>
シーズン中は、毎日正午に公式アカウント
<a href='https://bsky.app/profile/gracoro-union.bsky.social' target='_blank'>@gracoro-union.bsky.social</a>
が累積ランキングを発表します。このページのランキングも同じ公式集計で、1時間ごとに更新されます。
</p>
<p>
(※なお当同盟は日本マクドナルドとは無関係の非公式コミュニティです)
</p>
</div>
</div>
<div id='header'>
<div id='description'>
<p>
シーズン中の同盟員のPOSTは
<a href='https://bsky.app/profile/did:plc:gpxmc4do3afbktarbxxtdbxs/feed/aaaodidk6lkas' target='_blank'>グラコロ同盟フィード</a>
でまとめて読めます。
</p>
</div>
</div>
<div id='main'>
<div id='ranking'>
<h2>今期のランキング<span class='summary' id='ranking-summary'></span></h2>
<p id='ranking-status'>読み込み中…</p>
<ol id='ranking-list'></ol>
<p class='ranking-note'>
このランキングは公式の
<a href='/rule'>集計ルール</a>
による集計結果です。毎日正午に公式アカウントが発表する累積ランキングと同じ数字を表示しています。
</p>
</div>
</div>
__FOOTER__
</body>
</html>
"""

RANKING_JS = """/*
 * ranking.js : トップページのランキング表示
 *
 * 同一オリジンの standings.json (Muse の公式集計から生成され、シーズン中は
 * 1時間ごとに GitHub へ push される) を読み込んで描画するだけ。
 * 外部 API の呼び出しや認証情報は一切含まない。
 */
(function () {
  'use strict';

  function fmtDateTime(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    function p(n) { return (n < 10 ? '0' : '') + n; }
    return d.getFullYear() + '/' + p(d.getMonth() + 1) + '/' + p(d.getDate()) +
           ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  function render(data) {
    var status = document.getElementById('ranking-status');
    var list = document.getElementById('ranking-list');
    var summary = document.getElementById('ranking-summary');
    if (!status || !list) return;

    if (!data.season_start) {
      status.textContent = '2026シーズンは近日開幕予定です。開幕すると、ここにランキングが表示されます。';
      return;
    }
    var standings = data.standings || [];
    if (standings.length === 0) {
      status.textContent = 'シーズンは開幕しましたが、まだ報告がありません。最初の1個をどうぞ!';
      return;
    }
    if (summary) {
      summary.textContent = ' ' + data.participants + '人で食べたグラコロ、ただいま' + data.total_count;
    }
    status.textContent = '公式集計 ' + fmtDateTime(data.generated_at) + ' 時点 (1時間ごとに更新)';

    standings.slice(0, 50).forEach(function (person) {
      var li = document.createElement('li');

      var a = document.createElement('a');
      a.href = 'https://bsky.app/profile/' + encodeURIComponent(person.handle);
      a.target = '_blank';
      a.rel = 'noopener';
      var img = document.createElement('img');
      img.src = person.avatar || 'img/gracoro200x200.png';
      img.alt = person.handle;
      img.width = 48;
      img.height = 48;
      img.loading = 'lazy';
      a.appendChild(img);
      li.appendChild(a);

      var div = document.createElement('div');
      var name = document.createElement('span');
      name.className = 'pname';
      name.textContent = person.display_name || person.handle;
      div.appendChild(name);
      div.appendChild(document.createElement('br'));
      var icons = document.createElement('span');
      icons.className = 'icons';
      var html = '';
      for (var i = 0; i < person.count; i++) {
        html += '<img src="img/gracoro20x20.png" alt="">';
      }
      icons.innerHTML = html;
      div.appendChild(icons);
      var count = document.createElement('span');
      count.textContent = person.count;
      div.appendChild(count);
      li.appendChild(div);

      list.appendChild(li);
    });
    if (standings.length > 50) {
      var more = document.createElement('p');
      more.textContent = 'ほか ' + (standings.length - 50) + '人';
      list.parentNode.appendChild(more);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    fetch('standings.json', { cache: 'no-cache' })
      .then(function (r) {
        if (!r.ok) throw new Error('standings.json: ' + r.status);
        return r.json();
      })
      .then(render)
      .catch(function () {
        var status = document.getElementById('ranking-status');
        if (status) status.textContent = 'ランキングを読み込めませんでした。';
      });
  });
})();
"""

SITE_CSS = """/*
 * site.css : 静的化にあたっての補正 + 2026年デザイン刷新レイヤー
 * default.css (2011年の原形) の上書きとして読み込む。
 * 方針: 温かみのあるオレンジを基調に、書体と余白と階層を現代化する。
 * 端末がダークモードのときは、温かい暗色に追従する。
 */

/* ---- ランキング見出し・表示名まわり（従来の補正） ---- */
#ranking h2 span.summary {
  font-size: small;
  font-weight: normal;
}
#ranking h2 span.summary:before { content: ""; }
#ranking h2 span.summary:after { content: ""; }

#ranking .pname {
  font-size: medium;
  font-weight: bold;
}
#ranking .pname:before { content: ""; }
#ranking .pname:after { content: ""; }
#ranking span.icons:before { content: ""; }
#ranking span.icons:after { content: ""; }

#ranking-status {
  margin-top: 8px;
  color: #555;
  font-size: small;
}

#ranking .ranking-note {
  margin-top: 16px;
  color: #555;
  font-size: small;
}

/* ---- 書体と地の色 ---- */
body {
  font-family: "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Noto Sans JP",
    "Yu Gothic UI", "Yu Gothic", Meiryo, sans-serif;
  line-height: 1.8;
  color: #2b2118;
  background: linear-gradient(165deg, #f9a94e 0%, #f07c00 48%, #df6500 100%);
  -webkit-font-smoothing: antialiased;
}

::selection { background: #ffd9a3; }

a { color: #b35400; text-underline-offset: 3px; }
a:hover { color: #f07c00; }
a:focus-visible { outline: 3px solid #ffb066; outline-offset: 2px; }

/* ---- カードの質感 ---- */
h1 img {
  border-radius: 0 0 16px 16px;
  box-shadow: 0 12px 32px rgba(96, 42, 0, 0.28);
}

#header {
  background-color: #fff7ea;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 10px 28px rgba(96, 42, 0, 0.18);
}

#main {
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 10px 28px rgba(96, 42, 0, 0.18);
}

#main h2, #header h2 {
  font-size: 1.3rem;
  line-height: 1.5;
  letter-spacing: 0.02em;
  border-left: 6px solid #f07c00;
  padding-left: 0.55em;
  margin-bottom: 0.6em;
}

#main dt { color: #a34d00; }

/* ---- ランキング行 ---- */
#ranking ol {
  margin-left: 0;
  counter-reset: rank;
}

#ranking li {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  overflow: visible;
  margin-bottom: 2px;
  padding: 10px 12px;
  border-radius: 12px;
}
#ranking li:after { content: none; }
#ranking li:nth-child(odd) { background: rgba(240, 124, 0, 0.055); }
#ranking li:hover { background: rgba(240, 124, 0, 0.11); }

#ranking li::before {
  counter-increment: rank;
  content: counter(rank);
  flex: 0 0 auto;
  width: 28px;
  height: 28px;
  margin-top: 8px;
  border-radius: 50%;
  background: #e8790a;
  color: #fff;
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 28px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}
#ranking li:nth-child(1)::before { background: linear-gradient(160deg, #eec21a, #c99600); }
#ranking li:nth-child(2)::before { background: linear-gradient(160deg, #c3cbd1, #8f979e); }
#ranking li:nth-child(3)::before { background: linear-gradient(160deg, #d59a58, #a56a35); }
#ranking li:nth-child(1) { background: rgba(238, 194, 26, 0.13); }
#ranking li:nth-child(2) { background: rgba(160, 170, 178, 0.13); }
#ranking li:nth-child(3) { background: rgba(213, 154, 88, 0.14); }

#ranking li a {
  float: none;
  width: 48px;
  height: 48px;
  flex: 0 0 48px;
  border-radius: 50%;
  background: #f6ddba;
  font-size: 10px;
  line-height: 1.25;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #a34d00;
  overflow: hidden;
}
#ranking li a img {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}
#ranking div { margin-left: 0; flex: 1 1 auto; min-width: 0; }
#ranking .icons img { vertical-align: -3px; }
#ranking div > span:last-child {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: #a34d00;
}


/* ランキング内の本文リンク・全表示リンクはアバター用ルールの対象外にする */
#ranking p a {
  display: inline;
  float: none;
  width: auto;
  font-weight: inherit;
}
#ranking a.showall {
  display: inline-block;
  float: none;
  width: auto;
  margin: 8px 0 0 44px;
  font-weight: 700;
}

/* ---- フッター ---- */
#footer {
  background-color: #2e1d12;
  margin-top: 24px;
}
.footer-item h2 { color: #ffb066; font-size: 0.95rem; letter-spacing: 0.04em; }
.footer-item a { color: #f3e3d3; }

/* ---- 狭い画面 ---- */
@media screen and (max-width: 640px) {
  #header, #main { padding: 16px; border-radius: 12px; }
  h1 img { border-radius: 0 0 12px 12px; }
  #main dl { margin: 16px 4px 32px 4px; }
  #main dd { margin-left: 20px; }
  #ranking li { gap: 10px; padding: 8px; }
  #ranking li::before { width: 24px; height: 24px; line-height: 24px; font-size: 0.78rem; }
  .footer-item { margin-right: 16px; margin-left: 16px; }
}

/* ---- ダークモード ---- */
@media (prefers-color-scheme: dark) {
  body {
    color: #f3e9df;
    background: linear-gradient(165deg, #3a2312 0%, #251509 55%, #180d05 100%);
  }
  ::selection { background: #7a4a17; }
  a { color: #ffa54d; }
  a:hover { color: #ffc07d; }

  #header { background-color: #2d1e13; box-shadow: 0 10px 28px rgba(0, 0, 0, 0.45); }
  #main { background-color: #261a11; box-shadow: 0 10px 28px rgba(0, 0, 0, 0.45); }
  #main dt { color: #ffb066; }

  #ranking-status, #ranking .ranking-note { color: #cdb49c; }
  #ranking li:nth-child(odd) { background: rgba(255, 150, 60, 0.06); }
  #ranking li:hover { background: rgba(255, 150, 60, 0.12); }
  #ranking li:nth-child(1) { background: rgba(238, 194, 26, 0.13); }
  #ranking li:nth-child(2) { background: rgba(190, 198, 205, 0.12); }
  #ranking li:nth-child(3) { background: rgba(213, 154, 88, 0.15); }
  #ranking div > span:last-child { color: #ffb066; }
  #ranking li a { background: #4a3220; }
  #description p.alert { color: #ff9d8a; }

  #footer { background-color: #140b05; }
}
"""

NOT_FOUND = """<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>ページが見つかりません - グラコロ同盟</title>
<meta content='width=device-width,initial-scale=1' name='viewport'>
<link href='/css/default.css' media='all' rel='stylesheet' type='text/css'>
<link href='/css/site.css' media='all' rel='stylesheet' type='text/css'>
<link href='/img/gracoro20x20.png' rel='icon'>
</head>
<body>
<div id='main'>
<h2>ページが見つかりません</h2>
<p>お探しのページは存在しません。<a href='/'>サイトトップ</a>へどうぞ。</p>
</div>
</body>
</html>
"""

INITIAL_STANDINGS = {
    "season": "2026",
    "season_start": None,
    "season_end": None,
    "generated_at": None,
    "participants": 0,
    "total_count": 0,
    "counted_posts": 0,
    "standings": [],
}


def main():
    ap = argparse.ArgumentParser()
    base = Path(__file__).resolve().parent.parent
    ap.add_argument("--raw-dir", default=str(base / "tools" / "raw_live"))
    ap.add_argument("--site-dir", default=str(base / "site"))
    args = ap.parse_args()
    raw_dir = Path(args.raw_dir)
    site_dir = Path(args.site_dir)
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / "js").mkdir(exist_ok=True)
    (site_dir / "css").mkdir(exist_ok=True)

    footer = None
    for name in ["rule"] + [str(y) for y in ARCHIVE_YEARS]:
        html = clean(fetch(name, raw_dir))
        if name == "rule":
            # ルールページにも文字コード指定とデザイン刷新レイヤーを適用する
            html = html.replace("<head>", "<head>\n<meta charset='utf-8'>", 1)
            html = html.replace(
                "<link href='css/default.css' media='all' rel='stylesheet' type='text/css'>",
                "<link href='css/default.css' media='all' rel='stylesheet' type='text/css'>\n"
                "<link href='css/site.css' media='all' rel='stylesheet' type='text/css'>",
                1,
            )
        out = site_dir / f"{name}.html"
        out.write_text(html, encoding="utf-8")
        print(f"wrote {out} ({len(html)} bytes)")
        if name == "rule":
            footer = extract_footer(html)

    index = relativize(INDEX_TEMPLATE.replace("__FOOTER__", footer))
    (site_dir / "index.html").write_text(index, encoding="utf-8")
    (site_dir / "404.html").write_text(relativize(NOT_FOUND), encoding="utf-8")
    (base / "tools" / "footer.html").write_text(footer + "\n", encoding="utf-8")
    (site_dir / "js" / "ranking.js").write_text(RANKING_JS, encoding="utf-8")
    (site_dir / "css" / "site.css").write_text(SITE_CSS, encoding="utf-8")
    (site_dir / "CNAME").write_text("gracoro.tdtds.jp\n", encoding="utf-8")
    standings_path = site_dir / "standings.json"
    if not standings_path.exists():
        standings_path.write_text(
            json.dumps(INITIAL_STANDINGS, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print("done")


if __name__ == "__main__":
    sys.exit(main())
