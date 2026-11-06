"""Reproduced upstream behavior plus clearly labeled, in-memory teaching candidates."""

import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from .contracts import require

OPTIONS = [
    "--enable-verbose-logging",
    "--output-file-path",
    "--max-retry-count",
    "--disable-cache-mode",
    "--config-file-location",
    "--user-auth-token",
    "--auto-update-interval",
    "--force-overwrite-existing",
    "--network-timeout-seconds",
    "--debug-trace-enabled",
]


def source_root():
    root = Path(__file__).resolve().parents[2]
    for candidate in (root.parent, root / ".work/click-source"):
        if (candidate / "src/click/formatting.py").is_file():
            return candidate
    raise ValueError("Click source copy is missing; see PREWORK.md")


def click_module():
    location = source_root() / "src"
    sys.path.insert(0, str(location))
    import click

    require(
        Path(click.__file__).resolve().is_relative_to(location),
        "Tests must use the workspace Click source, not an installed package",
    )
    return click


@contextmanager
def candidate(mode):
    """These candidates are workshop hypotheses, not an endorsed upstream Click change."""
    click = click_module()
    if mode == "native":
        yield click
        return
    from click._textwrap import TextWrapper

    settings = {
        "baseline": {"break_on_hyphens": True, "break_long_words": True},
        "partial": {"break_on_hyphens": False, "break_long_words": True},
        "repaired": {"break_on_hyphens": False, "break_long_words": False},
    }
    require(mode in settings, "Unknown teaching candidate")

    def wrapper(*args, **kwargs):
        kwargs.update(settings[mode])
        return TextWrapper(*args, **kwargs)

    with patch("click._textwrap.TextWrapper", wrapper):
        yield click


def observe(mode):
    with candidate(mode) as click:
        formatter = click.HelpFormatter(width=65)
        formatter.write_usage("program", " ".join(OPTIONS))
        output = formatter.getvalue()
        long_token = "X" * 90
        long_output = click.formatting.wrap_text(long_token, width=30)
        ordinary = click.formatting.wrap_text("alpha beta gamma delta", width=12)
    return {
        "candidate": mode,
        "usage": output,
        "hyphen_tokens_intact": all(option in output for option in OPTIONS),
        "long_token_intact": long_token in long_output,
        "ordinary_text_wraps": "\n" in ordinary,
        "hypothesis_not_production_fix": True,
    }
