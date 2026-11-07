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


def clean(html):
    for pat, rep in CLEAN_PATTERNS:
        html = pat.sub(rep, html)
    return html


def extract_footer(html):
    start = html.index("<div id='footer'>")
    end = html.rindex("</div>", 0, html.index("</body>")) + len("</div>")
    return html[start:end]


INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
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
      img.src = person.avatar || '/img/gracoro200x200.png';
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
        html += '<img src="/img/gracoro20x20.png" alt="">';
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
 * site.css : 静的化にあたって追加した補正 (default.css は原形のまま残す)
 */

/* ランキング見出しの集計サマリには (個) の装飾を付けない */
#ranking h2 span.summary {
  font-size: small;
  font-weight: normal;
}
#ranking h2 span.summary:before { content: ""; }
#ranking h2 span.summary:after { content: ""; }

/* ランキングの表示名と状態表示 */
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
"""

NOT_FOUND = """<!DOCTYPE html>
<html>
<head>
<title>ページが見つかりません - グラコロ同盟</title>
<meta content='width=device-width,initial-scale=1' name='viewport'>
<link href='/css/default.css' media='all' rel='stylesheet' type='text/css'>
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
        out = site_dir / f"{name}.html"
        out.write_text(html, encoding="utf-8")
        print(f"wrote {out} ({len(html)} bytes)")
        if name == "rule":
            footer = extract_footer(html)

    index = INDEX_TEMPLATE.replace("__FOOTER__", footer)
    (site_dir / "index.html").write_text(index, encoding="utf-8")
    (site_dir / "404.html").write_text(NOT_FOUND, encoding="utf-8")
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
