from __future__ import annotations
from prompt_toolkit import prompt
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.validation import Validator
from typing import Iterable, Optional, Any, Dict, List


def choose(
    message: str,
    choices: Iterable[Any],
    default: Optional[Any] = None,
    allow_blank: bool = False,
    case_insensitive: bool = True,
) -> Optional[Any]:
    # Create display strings and a map back to original values
    values: List[Any] = list(choices)
    displays: List[str] = [str(v) for v in values]
    if case_insensitive:
        display_to_value: Dict[str, Any] = {str(v).lower(): v for v in values}
        allowed = set(display_to_value.keys())
    else:
        display_to_value = {str(v): v for v in values}
        allowed = set(display_to_value.keys())

    base = WordCompleter(displays, ignore_case=case_insensitive)
    completer = FuzzyCompleter(base)

    def validate_text(text: str) -> bool:
        if text == "":
            return allow_blank or (default is not None)
        key = text.lower() if case_insensitive else text
        return key in allowed

    v = Validator.from_callable(
        validate_text,
        move_cursor_to_end=True,
        error_message=f"Choose one of: {', '.join(displays)}",
    )
    default_disp = f" [{default}]" if default is not None else ""
    text = prompt(
        f"{message}:{default_disp} ",
        completer=completer,
        validator=v,
        validate_while_typing=False,
    )
    if text == "":
        if allow_blank:
            return None
        return default
    key = text.lower() if case_insensitive else text
    return display_to_value[key]


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
