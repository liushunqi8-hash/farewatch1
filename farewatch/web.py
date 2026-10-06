"""Web dashboard for farewatch — Python standard library only, no extra dependencies."""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from . import __version__
from .watcher import Watcher


class Dashboard:
    """Holds config/provider/notifiers and exposes dashboard state."""

    def __init__(self, config, provider, notifiers):
        self.config = config
        self.provider = provider
        self.notifiers = notifiers
        self.state_path = os.path.expanduser(config.state_file)
        self._lock = threading.Lock()
        self.last_check = None  # {"time": ..., "checked": n, "alerts": [...]}

    def route_summary(self) -> list[dict]:
        return [
            {
                "origin": r.origin,
                "destination": r.destination,
                "dates": r.all_dates(),
                "target_price": r.target_price,
                "currency": r.currency,
                "adults": r.adults,
            }
            for r in self.config.routes
        ]

    def status(self) -> dict:
        return {
            "version": __version__,
            "provider": self.config.provider,
            "routes": self.route_summary(),
            "state_file": self.state_path,
            "last_check": self.last_check,
        }

    def run_check(self) -> dict:
        """Run one check exactly like `farewatch check` (same Watcher, same dedup)."""
        with self._lock:
            alerts = Watcher(self.config, self.provider, self.notifiers).check()
            checked = sum(len(r.all_dates()) for r in self.config.routes)
            self.last_check = {
                "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "checked": checked,
                "alerts": alerts,
            }
            return self.last_check

    def history(self) -> dict:
        try:
            with open(self.state_path, encoding="utf-8") as f:
                keys = json.load(f).get("alerted", [])
        except (OSError, ValueError):
            keys = []
        return {"alerts": [self._parse_key(k) for k in keys]}

    @staticmethod
    def _parse_key(key: str) -> dict:
        # Watcher dedup key format: ORIGIN-DEST-DATE-PRICE, e.g. WUH-CDG-2027-03-08-1234
        parts = key.split("-")
        try:
            return {
                "key": key,
                "origin": parts[0],
                "destination": parts[1],
                "date": "-".join(parts[2:5]),
                "price": float(parts[5]),
            }
        except (IndexError, ValueError):
            return {"key": key}


PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>farewatch \u00b7 \u673a\u7968\u4ef7\u683c\u76d1\u63a7</title>
<style>
  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         max-width: 860px; margin: 0 auto; padding: 24px 16px 64px; line-height: 1.6; }
  h1 { font-size: 1.6em; margin-bottom: 4px; }
  .badges span { display: inline-block; padding: 2px 12px; margin: 2px 6px 2px 0;
                 border-radius: 999px; background: #eef2ff; font-size: .85em; }
  table { border-collapse: collapse; width: 100%; margin: 12px 0; }
  th, td { border: 1px solid #ccc; padding: 8px 10px; text-align: left; font-size: .92em; }
  th { background: #f5f5f5; }
  button { font-size: 1.05em; padding: 10px 30px; border: none; border-radius: 8px;
           background: #1677ff; color: #fff; cursor: pointer; }
  button:disabled { background: #999; cursor: default; }
  .alert { border-left: 4px solid #52c41a; background: #f6ffed;
           padding: 8px 12px; margin: 8px 0; }
  .muted { color: #888; font-size: .9em; }
  ul#alerts { padding-left: 20px; }
</style>
</head>
<body>
<h1>\u2708\ufe0f farewatch <span class="muted">\u673a\u7968\u4ef7\u683c\u76d1\u63a7 Flight fare watcher</span></h1>
<div class="badges" id="badges"></div>

<h2>\u822a\u7ebf Routes</h2>
<table id="routes">
  <thead><tr><th>\u822a\u7ebf Route</th><th>\u65e5\u671f Dates</th><th>\u76ee\u6807\u4ef7 Target</th></tr></thead>
  <tbody></tbody>
</table>

<h2>\u68c0\u67e5 Check</h2>
<p><button id="checkBtn" onclick="runCheck()">\u7acb\u5373\u68c0\u67e5 Check now</button></p>
<div id="result" class="muted">\u5c1a\u672a\u68c0\u67e5 No check yet.</div>

<h2>\u5386\u53f2\u544a\u8b66 Alert history</h2>
<ul id="alerts"></ul>
<p class="muted" id="statePath"></p>

<script>
function esc(s){ return String(s).replace(/[&<>"']/g, function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }

async function loadStatus(){
  const r = await fetch('/api/status');
  const s = await r.json();
  document.getElementById('badges').innerHTML =
    '<span>\u7248\u672c version: ' + esc(s.version) + '</span>' +
    '<span>\u6570\u636e\u6e90 provider: ' + esc(s.provider) + '</span>';
  const tb = document.querySelector('#routes tbody');
  tb.innerHTML = s.routes.map(function(rt){
    let dates = rt.dates.join(', ');
    if (rt.dates.length > 6)
      dates = rt.dates.slice(0, 6).join(', ') + ' \u2026(+' + (rt.dates.length - 6) + ')';
    return '<tr><td>' + esc(rt.origin) + ' \u2192 ' + esc(rt.destination) + '</td>' +
      '<td>' + esc(dates) + '</td>' +
      '<td>\u2264 ' + esc(rt.target_price) + ' ' + esc(rt.currency) + '</td></tr>';
  }).join('');
  document.getElementById('statePath').textContent =
    '\u72b6\u6001\u6587\u4ef6 state file: ' + s.state_file;
  if (s.last_check) showResult(s.last_check);
}

function showResult(res){
  const el = document.getElementById('result');
  let h = '\u68c0\u67e5\u65f6\u95f4 ' + esc(res.time) + ' \u00b7 ' +
    res.checked + ' \u4e2a\u7ec4\u5408 combinations \u00b7 <b>' +
    res.alerts.length + '</b> \u6761\u65b0\u544a\u8b66 new alert(s)';
  h += res.alerts.map(function(a){
    const stops = a.stops === 0 ? '\u76f4\u98de nonstop' : esc(a.stops) + ' \u7ecf\u505c stop(s)';
    return '<div class="alert">\u2708\ufe0f ' + esc(a.route) + ' ' + esc(a.date) +
      ' \u2014 <b>' + esc(a.price) + ' ' + esc(a.currency) + '</b> \u00b7 ' +
      esc(a.airline) + ' \u00b7 ' + stops + '</div>';
  }).join('');
  el.innerHTML = h;
}

async function loadAlerts(){
  const r = await fetch('/api/alerts');
  const j = await r.json();
  const ul = document.getElementById('alerts');
  if (!j.alerts.length){
    ul.innerHTML = '<li class="muted">\u6682\u65e0\u5386\u53f2\u544a\u8b66 No alerts yet.</li>';
    return;
  }
  ul.innerHTML = j.alerts.slice().reverse().map(function(a){
    return a.date
      ? '<li>' + esc(a.origin) + ' \u2192 ' + esc(a.destination) + ' \u00b7 ' +
        esc(a.date) + ' \u00b7 <b>' + esc(a.price) + '</b></li>'
      : '<li>' + esc(a.key) + '</li>';
  }).join('');
}

async function runCheck(){
  const btn = document.getElementById('checkBtn');
  btn.disabled = true;
  btn.textContent = '\u68c0\u67e5\u4e2d Checking\u2026';
  try {
    const r = await fetch('/api/check', {method: 'POST'});
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || ('HTTP ' + r.status));
    showResult(j);
    loadAlerts();
  } catch (e) {
    document.getElementById('result').textContent = '\u51fa\u9519 Error: ' + e.message;
  }
  btn.disabled = false;
  btn.textContent = '\u7acb\u5373\u68c0\u67e5 Check now';
}

loadStatus();
loadAlerts();
</script>
</body>
</html>
"""


def _make_handler(dashboard: Dashboard):
    class DashboardHandler(BaseHTTPRequestHandler):
        server_version = "farewatch/" + __version__

        def _send_json(self, obj, status: int = 200) -> None:
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, text: str, status: int = 200) -> None:
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/":
                self._send_html(PAGE)
            elif path == "/api/status":
                self._send_json(dashboard.status())
            elif path == "/api/alerts":
                self._send_json(dashboard.history())
            else:
                self._send_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path != "/api/check":
                self._send_json({"error": "not found"}, status=404)
                return
            length = int(self.headers.get("Content-Length", 0) or 0)
            if length:
                self.rfile.read(length)
            try:
                result = dashboard.run_check()
            except Exception as exc:  # noqa: BLE001 - surface check errors as JSON
                self._send_json({"error": str(exc)}, status=500)
                return
            self._send_json(result)

    return DashboardHandler


def serve(config, provider, notifiers, host: str = "127.0.0.1", port: int = 8080) -> None:
    """Start the dashboard web server. Blocks until interrupted."""
    dashboard = Dashboard(config, provider, notifiers)
    server = ThreadingHTTPServer((host, port), _make_handler(dashboard))
    print(f"farewatch {__version__} dashboard at http://{host}:{port}/  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
