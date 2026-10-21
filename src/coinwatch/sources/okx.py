"""OKX public REST API source (no API key required)."""

from __future__ import annotations

from .base import Quote, Source


class OKX(Source):
    name = "okx"
    BASE = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"

    def fetch(self, coin_ids: list[str], symbols: dict[str, str]) -> dict[str, Quote]:
        if not coin_ids:
            return {}
        wanted = {f"{sym.upper()}-USDT": cid for cid, sym in symbols.items() if cid in coin_ids}
        if not wanted:
            return {}

        data = self._get_json(self.BASE)
        rows = data.get("data") if isinstance(data, dict) else None
        if not rows:
            return {}

        out: dict[str, Quote] = {}
        for row in rows:
            cid = wanted.get(row.get("instId", ""))
            if cid is None:
                continue
            try:
                last = float(row["last"])
                open24h = float(row.get("open24h", last))
                change = ((last - open24h) / open24h * 100) if open24h else None
                out[cid] = Quote(
                    coin_id=cid,
                    symbol=symbols.get(cid, row["instId"].split("-")[0]),
                    price=last,
                    change_24h_pct=change,
                    volume_24h=_opt_float(row.get("quoteVol24h")),
                    source=self.name,
                )
            except (KeyError, ValueError, ZeroDivisionError):
                continue
        return out


def _opt_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
