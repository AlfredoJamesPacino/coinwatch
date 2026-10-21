"""TOML configuration loading."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_NAME = "config.toml"


@dataclass
class Config:
    """Runtime configuration."""

    watchlist: dict[str, str] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    notify: dict[str, Any] = field(default_factory=dict)
    web: dict[str, Any] = field(default_factory=dict)
    schedule: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def coin_ids(self) -> list[str]:
        return list(self.watchlist.keys())

    @property
    def change_pct_alert(self) -> float:
        return _as_float(self.thresholds.get("change_pct_alert"))

    @property
    def volume_spike_pct(self) -> float:
        return _as_float(self.thresholds.get("volume_spike_pct"))

    @property
    def price_above(self) -> dict[str, float]:
        return {k: _as_float(v) for k, v in (self.thresholds.get("price_above") or {}).items()}

    @property
    def price_below(self) -> dict[str, float]:
        return {k: _as_float(v) for k, v in (self.thresholds.get("price_below") or {}).items()}

    @property
    def interval_seconds(self) -> int:
        return int(_as_float(self.schedule.get("interval_seconds"), 300))


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_config(path: str | Path | None = None) -> Config:
    """Parse a TOML config file into a Config object."""
    p = Path(path or DEFAULT_CONFIG_NAME)
    if not p.exists():
        raise FileNotFoundError(
            f"Config not found: {p}\n"
            "Copy config.example.toml -> config.toml and edit it first: "
            "`coinwatch init` can do that for you."
        )
    with p.open("rb") as fh:
        data = tomllib.load(fh)
    return Config(
        watchlist=data.get("watchlist") or {},
        thresholds=data.get("thresholds") or {},
        notify=data.get("notify") or {},
        web=data.get("web") or {},
        schedule=data.get("schedule") or {},
        raw=data,
    )
