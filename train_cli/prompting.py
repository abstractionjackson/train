from __future__ import annotations
from prompt_toolkit import prompt
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import FuzzyCompleter, WordCompleter
from prompt_toolkit.validation import Validator
from typing import Iterable, Optional, Any, Dict, List
import calendar as _cal
from datetime import date as _date, timedelta as _timedelta


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


def _month_last_day(year: int, month: int) -> int:
    return _cal.monthrange(year, month)[1]


def _shift_month(d: _date, delta_months: int) -> _date:
    y = d.year + (d.month - 1 + delta_months) // 12
    m = (d.month - 1 + delta_months) % 12 + 1
    day = min(d.day, _month_last_day(y, m))
    return _date(y, m, day)


def pick_date(initial: Optional[_date] = None) -> Optional[_date]:
    """Interactive date picker in terminal. Arrow keys move by day/week, PgUp/PgDn by month, Enter selects, Esc cancels."""
    sel = [initial or _date.today()]  # boxed for closure mutation

    def _render() -> str:
        d = sel[0]
        cal = _cal.Calendar(firstweekday=0)  # Monday=0
        lines: List[str] = []
        title = d.strftime("%B %Y")
        lines.append(f"  {title}")
        lines.append("Mo Tu We Th Fr Sa Su")
        for week in cal.monthdayscalendar(d.year, d.month):
            parts = []
            for day in week:
                if day == 0:
                    parts.append("  ")
                else:
                    if day == d.day:
                        parts.append(f"[{day:2d}]")
                    else:
                        parts.append(f" {day:2d}")
            lines.append(" ".join(parts))
        lines.append("")
        lines.append("←/→ day  ↑/↓ week  PgUp/PgDn month  Home/End start/end  Enter OK  Esc cancel")
        return "\n".join(lines)

    kb = KeyBindings()

    @kb.add("left")
    def _left(event):
        sel[0] = sel[0] - _timedelta(days=1)

    @kb.add("right")
    def _right(event):
        sel[0] = sel[0] + _timedelta(days=1)

    @kb.add("up")
    def _up(event):
        sel[0] = sel[0] - _timedelta(days=7)

    @kb.add("down")
    def _down(event):
        sel[0] = sel[0] + _timedelta(days=7)

    @kb.add("pageup")
    def _pgup(event):
        sel[0] = _shift_month(sel[0], -1)

    @kb.add("pagedown")
    def _pgdn(event):
        sel[0] = _shift_month(sel[0], +1)

    @kb.add("home")
    def _home(event):
        s = sel[0]
        sel[0] = _date(s.year, s.month, 1)

    @kb.add("end")
    def _end(event):
        s = sel[0]
        sel[0] = _date(s.year, s.month, _month_last_day(s.year, s.month))

    @kb.add("enter")
    def _enter(event):
        event.app.exit(result=sel[0])

    @kb.add("escape")
    @kb.add("c-c")
    def _cancel(event):
        event.app.exit(result=None)

    body = Window(content=FormattedTextControl(lambda: _render()))
    layout = Layout(HSplit([body]))
    style = Style.from_dict({})
    app = Application(layout=layout, key_bindings=kb, style=style, full_screen=True)
    return app.run()
