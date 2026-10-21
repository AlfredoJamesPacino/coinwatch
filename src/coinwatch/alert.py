"""Threshold evaluation and alert generation."""

from __future__ import annotations

import json
from pathlib import Path

from .config import Config
from .sources.base import Quote

STATE_FILE = Path(".coinwatch_state.json")


def load_baselines(path: Path = STATE_FILE) -> dict[str, float]:
    try:
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return {k: float(v) for k, v in raw.items()}
    except (OSError, ValueError):
        pass
    return {}


def save_baselines(baselines: dict[str, float], path: Path = STATE_FILE) -> None:
    try:
        path.write_text(json.dumps(baselines, indent=2), encoding="utf-8")
    except OSError:
        pass


def evaluate(
    config: Config,
    quotes: dict[str, Quote],
    state_path: Path = STATE_FILE,
) -> list[str]:
    """Return a list of human-readable alert strings for the given quotes."""
    alerts: list[str] = []
    baselines = load_baselines(state_path)
    next_baselines = dict(baselines)

    for cid, quote in quotes.items():
        # 1. Absolute 24h move.
        if config.change_pct_alert > 0 and quote.change_24h_pct is not None:
            if abs(quote.change_24h_pct) >= config.change_pct_alert:
                direction = "涨" if quote.change_24h_pct >= 0 else "跌"
                alerts.append(
                    f"[{quote.symbol}] 24h {direction} {quote.change_24h_pct:+.2f}% "
                    f"(阈值 ±{config.change_pct_alert:.1f}%) 现价 ${quote.price:,.2f}"
                )

        # 2. Static price barriers.
        above = config.price_above.get(cid)
        if above is not None and quote.price >= above:
            alerts.append(f"[{quote.symbol}] 现价 ${quote.price:,.2f} 突破上方 ${above:,.2f}")

        below = config.price_below.get(cid)
        if below is not None and quote.price <= below:
            alerts.append(f"[{quote.symbol}] 现价 ${quote.price:,.2f} 跌破下方 ${below:,.2f}")

        # 3. Volume spike against a rolling baseline.
        if config.volume_spike_pct > 0 and quote.volume_24h:
            base = baselines.get(cid)
            if base is None:
                next_baselines[cid] = quote.volume_24h
            else:
                if quote.volume_24h >= base * (1 + config.volume_spike_pct / 100.0):
                    alerts.append(
                        f"[{quote.symbol}] 成交量异动 +{(quote.volume_24h / base - 1) * 100:.0f}% "
                        f"(基线 ${base:,.0f} -> 现 ${quote.volume_24h:,.0f})"
                    )
                # Gentle exponential moving average keeps the baseline fresh.
                next_baselines[cid] = base * 0.9 + quote.volume_24h * 0.1

    save_baselines(next_baselines, state_path)
    return alerts
