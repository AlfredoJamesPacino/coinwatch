"""Binance public REST API source (no API key required)."""

from __future__ import annotations

import json
import urllib.parse

from .base import Quote, Source

_TIMEOUT = 10.0


class Binance(Source):
    name = "binance"
    BASE = "https://api.binance.com/api/v3/ticker/24hr"

    def fetch(self, coin_ids: list[str], symbols: dict[str, str]) -> dict[str, Quote]:
        if not coin_ids:
            return {}
        # Mapbase symbol -> coin id, restricted to the coins actually requested.
        wanted = {sym.upper(): cid for cid, sym in symbols.items() if cid in coin_ids}
        if not wanted:
            return {}

        pairs = [f"{base}USDT" for base in wanted]
        # Compact separators keep spaces (which urlencode turns into "+") out of the JSON.
        query = urllib.parse.urlencode({"symbols": json.dumps(pairs, separators=(",", ":"))})
        data = self._get_json(f"{self.BASE}?{query}")

        # Binance answers API errors with an object instead of an array.
        if isinstance(data, dict):
            return {}

        out: dict[str, Quote] = {}
        for row in data:
            pair = row.get("symbol", "")
            if not pair.endswith("USDT"):
                continue
            cid = wanted.get(pair[: -len("USDT")])
            if cid is None:
                continue
            try:
                out[cid] = Quote(
                    coin_id=cid,
                    symbol=symbols.get(cid, pair[: -len("USDT")]),
                    price=float(row["lastPrice"]),
                    change_24h_pct=_opt_float(row.get("priceChangePercent")),
                    volume_24h=_opt_float(row.get("quoteVolume")),
                    source=self.name,
                )
            except KeyError:
                continue
        return out


def _opt_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
