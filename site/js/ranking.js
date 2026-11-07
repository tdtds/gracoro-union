/*
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
