from __future__ import annotations
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from typing import Iterable, Optional


def choose(
    message: str,
    choices: Iterable[str],
    default: Optional[str] = None,
    allow_blank: bool = False,
    case_insensitive: bool = True,
) -> str:
    words = list(choices)
    # Build a case-insensitive completer with fuzzy matching
    base = WordCompleter(words, ignore_case=case_insensitive)
    completer = FuzzyCompleter(base)

    allowed_lower = {w.lower() for w in words}
    def validate_text(text: str) -> bool:
        # Allow empty input when a default is provided or blanks are explicitly allowed
        if text == "":
            return allow_blank or (default is not None)
        if case_insensitive:
            return text.lower() in allowed_lower
        return text in words

    v = Validator.from_callable(
        validate_text,
        move_cursor_to_end=True,
        error_message=f"Choose one of: {', '.join(words)}",
    )
    default_disp = f" [{default}]" if default else ""
    result = prompt(
        f"{message}:{default_disp} ",
        completer=completer,
        validator=v,
        validate_while_typing=False,
    )
    if result == "":
        if allow_blank:
            return ""
        if default is not None:
            result = default
    # normalize to canonical casing if needed
    lookup = {w.lower(): w for w in words}
    return lookup.get(result.lower(), result)


def ask_number(message: str, default: Optional[int | float] = None, allow_blank: bool = False) -> Optional[float]:
    default_disp = f" [{default}]" if default is not None else ""
    while True:
        text = prompt(f"{message}:{default_disp} ")
        if text == "" and allow_blank:
            return None
        if text == "" and default is not None:
            return float(default)
        try:
            return float(text)
        except ValueError:
            print("Enter a number or leave blank.")
