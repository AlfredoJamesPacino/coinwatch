"""Source parsing tests. No network access required."""

from __future__ import annotations

import pytest

from coinwatch.alert import evaluate
from coinwatch.config import Config
from coinwatch.sources.base import Quote
from coinwatch.sources.binance import Binance
from coinwatch.sources.coingecko import CoinGecko
from coinwatch.sources.okx import OKX


def test_coingecko_parses_payload(monkeypatch):
    sample = {"bitcoin": {"usd": 65000.0, "usd_24h_change": 2.5, "usd_24h_vol": 30000.0}}
    monkeypatch.setattr(CoinGecko, "_get_json", staticmethod(lambda url: sample))

    out = CoinGecko().fetch(["bitcoin"], {"bitcoin": "BTC"})
    assert "bitcoin" in out
    quote = out["bitcoin"]
    assert quote.price == 65000.0
    assert quote.change_24h_pct == 2.5
    assert quote.source == "coingecko"


def test_coingecko_skips_missing_coins(monkeypatch):
    monkeypatch.setattr(CoinGecko, "_get_json", staticmethod(lambda url: {}))
    assert CoinGecko().fetch(["bitcoin"], {"bitcoin": "BTC"}) == {}


def test_binance_parses_payload(monkeypatch):
    sample = [
        {
            "symbol": "BTCUSDT",
            "lastPrice": "65000.0",
            "priceChangePercent": "2.5",
            "quoteVolume": "30000.0",
        }
    ]
    monkeypatch.setattr(Binance, "_get_json", staticmethod(lambda url: sample))

    out = Binance().fetch(["bitcoin"], {"bitcoin": "BTC"})
    assert out["bitcoin"].price == 65000.0
    assert out["bitcoin"].change_24h_pct == 2.5


def test_binance_ignores_error_object(monkeypatch):
    monkeypatch.setattr(
        Binance, "_get_json", staticmethod(lambda url: {"code": -1121, "msg": "Invalid symbol."})
    )
    assert Binance().fetch(["bitcoin"], {"bitcoin": "BTC"}) == {}


def test_okx_parses_payload_and_computes_change(monkeypatch):
    sample = {"data": [{"instId": "BTC-USDT", "last": "65000", "open24h": "63000", "quoteVol24h": "30000"}]}
    monkeypatch.setattr(OKX, "_get_json", staticmethod(lambda url: sample))

    out = OKX().fetch(["bitcoin"], {"bitcoin": "BTC"})
    quote = out["bitcoin"]
    assert quote.price == 65000.0
    assert quote.change_24h_pct == pytest.approx((65000 - 63000) / 63000 * 100)


def test_change_threshold_triggers(tmp_path):
    config = Config(watchlist={"bitcoin": "BTC"}, thresholds={"change_pct_alert": 5.0})
    quotes = {"bitcoin": Quote("bitcoin", "BTC", 65000.0, change_24h_pct=7.5, source="test")}

    alerts = evaluate(config, quotes, state_path=tmp_path / "state.json")
    assert len(alerts) == 1
    assert "BTC" in alerts[0]


def test_change_threshold_stays_silent(tmp_path):
    config = Config(watchlist={"bitcoin": "BTC"}, thresholds={"change_pct_alert": 5.0})
    quotes = {"bitcoin": Quote("bitcoin", "BTC", 65000.0, change_24h_pct=1.0, source="test")}

    assert evaluate(config, quotes, state_path=tmp_path / "state.json") == []


def test_price_barriers(tmp_path):
    config = Config(
        watchlist={"ethereum": "ETH"},
        thresholds={"price_above": {"ethereum": 5000}, "price_below": {"ethereum": 500}},
    )

    hi = {"ethereum": Quote("ethereum", "ETH", 5200.0, source="test")}
    lo = {"ethereum": Quote("ethereum", "ETH", 400.0, source="test")}
    mid = {"ethereum": Quote("ethereum", "ETH", 3000.0, source="test")}

    assert len(evaluate(config, hi, state_path=tmp_path / "s.json")) == 1
    assert len(evaluate(config, lo, state_path=tmp_path / "s.json")) == 1
    assert evaluate(config, mid, state_path=tmp_path / "s.json") == []
