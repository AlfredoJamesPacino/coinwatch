"""Text and JSON report rendering."""

from __future__ import annotations

from .sources.base import Quote


def render_text(quotes: dict[str, Quote], alerts: list[str]) -> str:
    lines = ["", "=== CoinWatch 行情快照 ===", ""]
    if quotes:
        lines.append(f"{'SYMBOL':<8}{'PRICE':>14}{'24H':>10}   SOURCE")
        lines.append("-" * 46)
        for quote in quotes.values():
            change = f"{quote.change_24h_pct:+.2f}%" if quote.change_24h_pct is not None else "n/a"
            lines.append(
                f"{quote.symbol:<8}{'$' + format(quote.price, ',.2f'):>14}"
                f"{change:>10}   {quote.source}"
            )
    else:
        lines.append("(无数据 — 所有行情源均不可用)")
    lines.append("")

    if alerts:
        lines.append("--- 告警 ---")
        lines.extend(f"* {a}" for a in alerts)
    else:
        lines.append("--- 无告警 ---")
    lines.append("")
    return "\n".join(lines)


def render_json(quotes: dict[str, Quote], alerts: list[str]) -> dict:
    return {
        "quotes": {cid: q.as_dict() for cid, q in quotes.items()},
        "alerts": alerts,
    }
