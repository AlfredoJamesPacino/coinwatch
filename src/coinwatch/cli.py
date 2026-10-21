"""Command line interface."""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

from . import __version__
from . import web as web_module
from .alert import evaluate
from .config import DEFAULT_CONFIG_NAME, Config, load_config
from .market import Market
from .notifier import notify
from .report import render_text


def _render_alerts(alerts: list[str]) -> str:
    return "\n".join(f"* {a}" for a in alerts)


def _print_source_failures(market: Market) -> None:
    """Surface *why* a snapshot came back empty instead of leaving users guessing."""
    failures = getattr(market, "last_failures", {}) or {}
    if not failures:
        return
    print("行情源不可用：")
    for name, err in failures.items():
        print(f"  ! {name}: {err}")
    print("  -> 常见原因：本机网络到该 API 不通（部分地区需代理）、或被限流。")
    print()


def cmd_check(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    market = Market()
    quotes = market.snapshot(config.coin_ids, config.watchlist)
    alerts = evaluate(config, quotes)

    _print_source_failures(market)
    print(render_text(quotes, []))
    if alerts:
        notify(config, "CoinWatch 告警:\n" + _render_alerts(alerts))
    else:
        print("无告警。")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    market = Market()
    quotes = market.snapshot(config.coin_ids, config.watchlist)
    _print_source_failures(market)
    print(render_text(quotes, []))
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    market = Market()
    interval = args.interval or config.interval_seconds
    print(f"每 {interval}s 轮询一次。Ctrl+C 退出。")
    # Report source outages once, not once per tick.
    reported_failures = False
    try:
        while True:
            quotes = market.snapshot(config.coin_ids, config.watchlist)
            alerts = evaluate(config, quotes)
            if not reported_failures:
                _print_source_failures(market)
                reported_failures = True
            print(render_text(quotes, []))
            if alerts:
                notify(config, "CoinWatch 告警:\n" + _render_alerts(alerts))
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n已停止。")
    return 0


def cmd_web(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    market = Market()
    web_module.run_web(config, market)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    example = Path("config.example.toml")
    target = Path(args.config or DEFAULT_CONFIG_NAME)
    if target.exists():
        print(f"{target} 已存在，未覆盖。")
        return 0
    if not example.exists():
        print("未找到 config.example.toml（请在项目根目录运行）。")
        return 1
    shutil.copy(example, target)
    print(f"已生成 {target}，请编辑其中的 watchlist / 阈值 / 通知渠道后使用。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coinwatch",
        description="本地优先的加密货币行情监控与告警引擎。",
    )
    parser.add_argument(
        "--version", action="version", version=f"coinwatch {__version__}"
    )
    parser.add_argument("--config", default=None, help=f"配置文件路径（默认 {DEFAULT_CONFIG_NAME}）")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="单次快照并触发告警")
    sub.add_parser("list", help="列出自选行情")
    watcher = sub.add_parser("watch", help="循环监控")
    watcher.add_argument("--interval", type=int, default=None, help="轮询间隔（秒）")
    sub.add_parser("web", help="启动本地 Web 面板")
    sub.add_parser("init", help="从示例生成 config.toml")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    handlers = {
        "check": cmd_check,
        "list": cmd_list,
        "watch": cmd_watch,
        "web": cmd_web,
        "init": cmd_init,
    }
    try:
        return handlers[args.command](args)
    except FileNotFoundError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
