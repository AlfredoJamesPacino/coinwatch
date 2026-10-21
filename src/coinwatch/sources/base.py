"""Base abstractions for market data sources."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

USER_AGENT = "CoinWatch/0.1 (+https://github.com/AlfredoJamesPacino/coinwatch)"
DEFAULT_TIMEOUT = 10.0


class Quote:
    """A normalized single-coin quote, independent of which source produced it."""

    __slots__ = ("coin_id", "symbol", "price", "change_24h_pct", "volume_24h", "source")

    def __init__(
        self,
        coin_id: str,
        symbol: str,
        price: float,
        change_24h_pct: float | None = None,
        volume_24h: float | None = None,
        source: str = "",
    ) -> None:
        self.coin_id = coin_id
        self.symbol = symbol
        self.price = price
        self.change_24h_pct = change_24h_pct
        self.volume_24h = volume_24h
        self.source = source

    def as_dict(self) -> dict[str, Any]:
        return {
            "coin_id": self.coin_id,
            "symbol": self.symbol,
            "price": self.price,
            "change_24h_pct": self.change_24h_pct,
            "volume_24h": self.volume_24h,
            "source": self.source,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Quote {self.symbol} ${self.price} via {self.source}>"


class SourceError(RuntimeError):
    """Raised when a source cannot be reached or returns unparseable data."""


class Source:
    """Base class for a market data source."""

    name = "base"

    def fetch(self, coin_ids: list[str], symbols: dict[str, str]) -> dict[str, Quote]:
        """Return quotes for as many of ``coin_ids`` as this source can provide."""
        raise NotImplementedError

    @staticmethod
    def _get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> Any:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise SourceError(f"{url} -> {exc}") from exc
