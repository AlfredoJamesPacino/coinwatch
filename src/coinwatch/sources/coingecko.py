"""CoinGecko public API source (no API key required)."""

from __future__ import annotations

from .base import Quote, Source


class CoinGecko(Source):
    name = "coingecko"
    BASE = "https://api.coingecko.com/api/v3/simple/price"

    def fetch(self, coin_ids: list[str], symbols: dict[str, str]) -> dict[str, Quote]:
        if not coin_ids:
            return {}
        ids = ",".join(coin_ids)
        url = (
            f"{self.BASE}?ids={ids}&vs_currencies=usd"
            "&include_24hr_change=true&include_24hr_vol=true"
        )
        data = self._get_json(url)

        out: dict[str, Quote] = {}
        for cid in coin_ids:
            row = data.get(cid) if isinstance(data, dict) else None
            if not row or "usd" not in row:
                continue
            out[cid] = Quote(
                coin_id=cid,
                symbol=symbols.get(cid, cid.upper()),
                price=float(row["usd"]),
                change_24h_pct=_opt_float(row.get("usd_24h_change")),
                volume_24h=_opt_float(row.get("usd_24h_vol")),
                source=self.name,
            )
        return out


def _opt_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
