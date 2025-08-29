from __future__ import annotations
import typer
from rich.table import Table
from rich.console import Console
from ..storage import Storage
from ..prompting import choose

console = Console()
storage = Storage()

def detail_exercise_by_id(exercise_id: int):
    data = storage.load()
    ex = next((e for e in data.exercises if e.id == exercise_id), None)
    if not ex:
        console.print("Exercise not found")
        raise typer.Exit(1)
    title = f"Exercise: {ex.displayName or ','.join(ex.aliases) or ex.id}"
    table = Table(title=title)
    table.add_column("Property")
    table.add_column("Value")
    table.add_row("id", str(ex.id))
    table.add_row("name", ex.displayName or ",".join(ex.aliases) or str(ex.id))
    table.add_row("aliases", ",".join(ex.aliases))
    table.add_row("movement", ex.movement)
    table.add_row("position", ex.position)
    table.add_row("equipment", ex.equipment or "-")
    table.add_row("angle", "-" if ex.angle is None else str(int(ex.angle)))
    console.print(table)

def detail_workout_by_date(date_str: str):
    data = storage.load()
    w = next((w for w in data.workouts if w.date.isoformat() == date_str), None)
    if not w:
        console.print("Workout not found")
        raise typer.Exit(1)
    # Metadata table without header row; capitalized property and M/D date
    meta = Table(title="Workout", show_header=False)
    meta.add_column()
    meta.add_column()
    pretty_date = f"{w.date.month}/{w.date.day}"
    meta.add_row("Date", pretty_date)
    console.print(meta)
    id_to_name = {e.id: (e.displayName or ",".join(e.aliases) or str(e.id)) for e in data.exercises}
    # If there are intended exercises, show them first
    if getattr(w, "intendedExercisePerformance", None):
        intended = Table(title="Intended Exercises")
        intended.add_column("Name")
        intended.add_column("Weight")
        intended.add_column("Sets", justify="right")
        intended.add_column("Reps", justify="right")
        for ep in w.intendedExercisePerformance:
            name = id_to_name.get(ep.templateId, str(ep.templateId))
            weight_str = "-" if ep.weight is None else str(ep.weight)
            intended.add_row(name, weight_str, str(ep.sets), str(ep.reps))
        console.print(intended)
    perf = Table(title="Exercises Performed")
    perf.add_column("Name")
    perf.add_column("Weight")
    perf.add_column("Sets", justify="right")
    perf.add_column("Reps", justify="right")
    for ep in w.exercisePerformance:
        name = id_to_name.get(ep.templateId, str(ep.templateId))
        weight_str = "-" if ep.weight is None else str(ep.weight)
        perf.add_row(name, weight_str, str(ep.sets), str(ep.reps))
    console.print(perf)

def detail_exercise_history(exercise_id: int):
    """Show a table of this exercise's performances across workouts, newest first."""
    data = storage.load()
    # Collect (date, ep) pairs for matching templateId
    rows = []
    for w in data.workouts:
        for ep in w.exercisePerformance:
            if ep.templateId == exercise_id:
                rows.append((w.date, ep))
    if not rows:
        console.print("No history found for this exercise.")
        return
    # Sort by date descending
    rows.sort(key=lambda r: r[0], reverse=True)
    title = "Exercise History"
    table = Table(title=title)
    table.add_column("Date")
    table.add_column("Weight")
    table.add_column("Sets", justify="right")
    table.add_column("Reps", justify="right")
    for d, ep in rows:
        pretty_date = f"{d.month}/{d.day}"
        weight_str = "-" if ep.weight is None else str(ep.weight)
        table.add_row(pretty_date, weight_str, str(ep.sets), str(ep.reps))
    console.print(table)

def detail_performance_by_name(exercise_name: str):
    """Show performance history for an exercise by name (displayName or alias)."""
    data = storage.load()
    # Find exercise by name
    target_exercise = None
    for e in data.exercises:
        if e.displayName and e.displayName.lower() == exercise_name.lower():
            target_exercise = e
            break
        for alias in e.aliases:
            if alias.lower() == exercise_name.lower():
                target_exercise = e
                break
        if target_exercise:
            break
    
    if not target_exercise:
        console.print(f"Exercise '{exercise_name}' not found")
        raise typer.Exit(1)
    
    # Collect (date, ep) pairs for matching templateId
    rows = []
    for w in data.workouts:
        for ep in w.exercisePerformance:
            if ep.templateId == target_exercise.id:
                rows.append((w.date, ep))
    
    if not rows:
        console.print(f"No performance history found for {target_exercise.displayName or exercise_name}")
        return
    
    # Sort by date descending
    rows.sort(key=lambda r: r[0], reverse=True)
    title = f"Performance History: {target_exercise.displayName or exercise_name}"
    table = Table(title=title)
    table.add_column("Date")
    table.add_column("Weight")
    table.add_column("Sets", justify="right")
    table.add_column("Reps", justify="right")
    
    for d, ep in rows:
        pretty_date = f"{d.month}/{d.day}"
        weight_str = "-" if ep.weight is None else str(ep.weight)
        table.add_row(pretty_date, weight_str, str(ep.sets), str(ep.reps))
    
    console.print(table)
