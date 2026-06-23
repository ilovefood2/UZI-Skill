"""Language control (US/English edition).

This edition is English-only. ``get_language()`` always returns ``"en"`` and
``language_instruction()`` always emits an English-output directive, so every
agent role-play, headline, verdict and commentary is produced in English
regardless of the ``UZI_LANG`` environment variable.

The ``zh`` code path from the upstream bilingual project has been removed.

Integration points:
- ``personas.build_system_message(lang=...)`` reads ``language_instruction()``
- May extend to stage2 report copy, fetcher error messages, etc.
"""
from __future__ import annotations

SUPPORTED_LANGS = ("en",)


def get_language() -> str:
    """Return the active language. Always English in this edition."""
    return "en"


def language_instruction(lang: str = "") -> str:
    """Return the system-prompt directive appended during agent role-play.

    Always English: all reasoning, headlines, verdicts and commentary must be
    written in English. Investor names stay in their conventional English form
    (Buffett, Munger, Lynch, Wood); financial terms use standard English.
    """
    return (
        "OUTPUT LANGUAGE: Write all reasoning, headlines, verdicts and commentary "
        "in English. Use standard English financial terminology (net margin, "
        "gross margin, P/E, free cash flow, moat, DCF, PEG, EPS). Investor names "
        "stay in their conventional English spelling (Buffett, Munger, Lynch, Wood)."
    )
