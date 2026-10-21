"""Minimal local dashboard, powered by the standard library only."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .alert import evaluate
from .config import Config
from .market import Market
from .sources.base import Quote


def build_page(quotes: dict[str, Quote], alerts: list[str]) -> str:
    rows = ""
    for quote in quotes.values():
        change = f"{quote.change_24h_pct:+.2f}%" if quote.change_24h_pct is not None else "n/a"
        color = "#ffffff"
        if quote.change_24h_pct is not None:
            # Chinese market convention: up = red, down = green.
            color = "#ff4d4f" if quote.change_24h_pct >= 0 else "#0ecb81"
        rows += (
            f"<tr><td><b>{quote.symbol}</b></td>"
            f"<td>${quote.price:,.2f}</td>"
            f'<td style="color:{color}">{change}</td>'
            f"<td>{quote.source}</td></tr>"
        )
    if not rows:
        rows = '<tr><td colspan="4">无数据 — 所有行情源均不可用</td></tr>'

    alert_html = (
        "<br>".join(f"&bull; {a}" for a in alerts) if alerts else "当前无告警"
    )

    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<meta http-equiv="refresh" content="60">
<title>CoinWatch</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; background:#0f1115;
         color:#e6e6e6; padding:2rem; max-width:900px; margin:0 auto; }}
  h1 {{ color:#f7931a; margin-bottom:.2rem; }}
  table {{ border-collapse:collapse; width:100%; margin-top:1rem; }}
  th, td {{ padding:.6rem .8rem; border-bottom:1px solid #2a2f3a; text-align:left; }}
  th {{ color:#8b93a7; font-weight:600; }}
  .card {{ background:#161a22; border:1px solid #232833; border-radius:10px;
           padding:1rem 1.2rem; margin-top:1.5rem; }}
  .alert {{ color:#ff6b6b; }}
  small {{ color:#6b7280; }}
</style></head>
<body>
  <h1>CoinWatch</h1>
  <small>本地优先 · 数据来源：CoinGecko / Binance / OKX 公开 API · 自动刷新 60s</small>
  <table>
    <tr><th>币种</th><th>价格</th><th>24h</th><th>数据源</th></tr>
    {rows}
  </table>
  <div class="card"><b>告警</b><div class="alert">{alert_html}</div></div>
  <p class="card small">本项目仅做行情监控与告警，不构成任何投资建议。加密货币市场高风险，请自行判断并控制风险。</p>
</body></html>"""


def make_handler(config: Config, market: Market):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib naming
            quotes = market.snapshot(config.coin_ids, config.watchlist)
            alerts = evaluate(config, quotes)
            body = build_page(quotes, alerts).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args, **kwargs) -> None:
            pass  # keep the console clean; alerts already go through notify()

    return Handler


def run_web(config: Config, market: Market) -> None:
    host = config.web.get("host", "127.0.0.1")
    port = int(config.web.get("port", 8080))
    server = ThreadingHTTPServer((host, port), make_handler(config, market))
    print(f"CoinWatch dashboard: http://{host}:{port}  (Ctrl+C 退出)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()
