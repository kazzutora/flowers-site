"""Section 19: every user facing string exists in both languages.

`makemessages` fills a new entry with the translation of a similar one and
marks it fuzzy. msgfmt then drops it, so the string quietly falls back to
English while the catalogue holds text belonging to a different message. This
test is here so that never ships unnoticed.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = ("uk", "ru")

FUZZY = re.compile(r"^#,.*\bfuzzy\b", re.M)


def _blocks(language: str) -> list[str]:
    catalogue = ROOT / "locale" / language / "LC_MESSAGES" / "django.po"
    return catalogue.read_text(encoding="utf-8").split("\n\n")


def _text(lines: list[str]) -> str:
    parts = [match.group(1) for line in lines if (match := re.search(r'"(.*)"\s*$', line))]
    return "".join(parts)


def _entries(language: str) -> list[tuple[str, str]]:
    """(msgid, joined msgstr) for every entry but the header."""
    found = []
    for block in _blocks(language):
        lines = block.splitlines()
        if not any(line.startswith("msgid ") for line in lines):
            continue

        msgid: list[str] = []
        msgstr: list[str] = []
        state = None
        for line in lines:
            if line.startswith("msgid_plural"):
                state = "plural"
            elif line.startswith("msgid"):
                state = "msgid"
                msgid.append(line)
            elif line.startswith("msgstr"):
                state = "msgstr"
                msgstr.append(line)
            elif line.startswith('"'):
                if state == "msgid":
                    msgid.append(line)
                elif state == "msgstr":
                    msgstr.append(line)

        identifier = _text(msgid)
        if identifier:
            found.append((identifier, _text(msgstr)))
    return found


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_string_is_left_untranslated(language: str) -> None:
    empty = [msgid for msgid, msgstr in _entries(language) if not msgstr.strip()]

    assert not empty, f"{language}: {empty}"


@pytest.mark.parametrize("language", LANGUAGES)
def test_no_entry_is_left_fuzzy(language: str) -> None:
    """A fuzzy entry is worse than an empty one: it looks translated."""
    guessed = [block.splitlines()[-2:] for block in _blocks(language) if FUZZY.search(block)]

    assert not guessed, f"{language}: {guessed}"
