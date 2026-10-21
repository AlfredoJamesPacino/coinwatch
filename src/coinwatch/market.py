"""Market data sources registry and failover-capable snapshot builder."""

from __future__ import annotations

from .sources.binance import Binance
from .sources.coingecko import CoinGecko
from .sources.okx import OKX
from .sources.base import Quote, Source

__all__ = ["Market", "Quote", "Source", "CoinGecko", "Binance", "OKX"]


class Market:
    """Aggregates several sources, falling back between them per coin.

    Sources are tried in order. A coin is satisfied by the first source that
    returns it, so a single broken provider never takes down the whole run.
    """

    def __init__(self, sources: list[Source] | None = None) -> None:
        self.sources: list[Source] = sources or [CoinGecko(), Binance(), OKX()]

    def snapshot(self, coin_ids: list[str], symbols: dict[str, str]) -> dict[str, Quote]:
        """Fetch every requested coin, using whichever source can answer."""
        results: dict[str, Quote] = {}
        pending = list(coin_ids)
        failures: dict[str, str] = {}

        for source in self.sources:
            if not pending:
                break
            try:
                got = source.fetch(pending, symbols)
            except RuntimeError as exc:
                failures[source.name] = str(exc)
                continue
            for cid in list(pending):
                quote = got.get(cid)
                if quote is not None:
                    results[cid] = quote
                    pending.remove(cid)

        self.last_failures = failures
        return results
