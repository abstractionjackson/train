from __future__ import annotations
from rich.table import Table
from rich.console import Console
from ..storage import Storage
from typing import Iterable, Set

console = Console()
storage = Storage()

def list_exercises():
    data = storage.load()
    table = Table(title="Exercises")
    table.add_column("Name")
    def disp(e):
        return (e.displayName or ",".join(e.aliases) or str(e.id))
    for name in sorted((disp(e) for e in data.exercises), key=lambda s: s.lower()):
        table.add_row(name)
    console.print(table)

def list_workouts(has_exercise: str | None = None):
    data = storage.load()
    table = Table(title="Workouts")
    table.add_column("Date")
    table.add_column("Exercises")
    id_to_name = {e.id: (e.displayName or ",".join(e.aliases) or str(e.id)) for e in data.exercises}
    # Optional filter: CSV of exercise aliases/display names (case-insensitive)
    filter_ids: Set[int] | None = None
    if has_exercise:
        terms = [t.strip().lower() for t in has_exercise.split(",") if t.strip()]
        if terms:
            alias_to_ids: dict[str, Set[int]] = {}
            def add_key(k: str, vid: int):
                kl = k.lower()
                s = alias_to_ids.get(kl)
                if s is None:
                    s = set()
                    alias_to_ids[kl] = s
                s.add(vid)
            for e in data.exercises:
                if e.displayName:
                    add_key(e.displayName, e.id)
                for a in e.aliases:
                    add_key(a, e.id)
            matched: Set[int] = set()
            for t in terms:
                matched.update(alias_to_ids.get(t, set()))
            filter_ids = matched if matched else set()
    # Sort by date descending
    for w in sorted(data.workouts, key=lambda w: w.date, reverse=True):
        if filter_ids is not None:
            # Skip workouts without any matching exercise templateId
            if not any(ep.templateId in filter_ids for ep in w.exercisePerformance):
                continue
        # Format as M/D (no leading zeros), e.g., 8/24
        pretty_date = f"{w.date.month}/{w.date.day}"
        names = [id_to_name.get(ep.templateId, str(ep.templateId)) for ep in w.exercisePerformance]
        table.add_row(pretty_date, ",".join(names))
    console.print(table)
