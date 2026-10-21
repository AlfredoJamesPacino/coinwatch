"""CLI surface tests. No network access required."""

from __future__ import annotations

import pytest

from coinwatch import __version__
from coinwatch.cli import build_parser


def test_version_flag_reports_package_version(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_subcommands_are_registered():
    parser = build_parser()
    args = parser.parse_args(["list"])
    assert args.command == "list"


def test_config_path_defaults_to_none():
    """argparse default must stay None so load_config() can fall back itself."""
    parser = build_parser()
    assert parser.parse_args(["list"]).config is None
