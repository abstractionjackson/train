from __future__ import annotations
import typer
from rich.console import Console
from .validators import validate_instance, logical_validate
from .storage import Storage
from .commands.list_cmds import list_exercises, list_workouts
from .commands.exercise_cmds import (
    add_exercise,
    update_exercise,
    delete_exercise_by_key,
    resolve_exercise_id_by_key,
)
from .commands.workout_cmds import (
    add_workout,
    update_workout,
    delete_workout,
    resolve_workout_date_key,
    plan_workout,
    update_workout_plan,
    add_workout_plan,
    add_workout_performance,
    update_workout_date,
)
from .commands.detail_cmds import (
    detail_exercise_by_id,
    detail_workout_by_date,
)

app = typer.Typer(help="Manage workout chronology data")
console = Console()
storage = Storage()

@app.command(name="list")
def list_cmd(
    entity: str = typer.Argument(..., metavar="exercise|workout", case_sensitive=False),
    has_exercise: str | None = typer.Option(None, "--has-exercise", "--he", help="CSV of exercise aliases/display names to filter workouts"),
):
    entity_l = entity.lower()
    if entity_l in ("exercise", "exercises"):
        list_exercises()
    elif entity_l in ("workout", "workouts"):
        list_workouts(has_exercise)
    else:
        console.print("Unknown entity. Use 'exercise' or 'workout'.")
        raise typer.Exit(1)

@app.command(name="plan")
def plan_cmd(
    entity: str = typer.Argument(..., metavar="workout", case_sensitive=False),
):
    entity_l = entity.lower()
    if entity_l in ("workout", "workouts"):
        plan_workout()
    else:
        console.print("Unknown entity. Use 'workout'.")
        raise typer.Exit(1)

@app.command(name="add")
def add_cmd(
    entity: str = typer.Argument(..., metavar="exercise|workout", case_sensitive=False),
):
    entity_l = entity.lower()
    if entity_l in ("exercise", "exercises"):
        add_exercise()
    elif entity_l in ("workout", "workouts"):
        add_workout()
    else:
        console.print("Unknown entity. Use 'exercise' or 'workout'.")
        raise typer.Exit(1)

@app.command(name="delete")
def delete_cmd(
    entity: str = typer.Argument(..., metavar="exercise|workout", case_sensitive=False),
    key: str | None = typer.Argument(None),
):
    entity_l = entity.lower()
    if entity_l in ("exercise", "exercises"):
        delete_exercise_by_key(key)
    elif entity_l in ("workout", "workouts"):
        if key is None:
            key = resolve_workout_date_key(None)
        delete_workout(key)
    else:
        console.print("Unknown entity. Use 'exercise' or 'workout'.")
        raise typer.Exit(1)

@app.command(name="update")
def update_cmd(
    entity: str = typer.Argument(..., metavar="exercise|workout", case_sensitive=False),
    sub: str | None = typer.Argument(None, help="For workouts: 'date' or 'plan'. Omit to edit performed."),
    key: str | None = typer.Argument(None, help="Workout date (ISO) or exercise key"),
    add: bool = typer.Option(False, "--add", help="Add instead of edit (for workouts)"),
):
    entity_l = entity.lower()
    if entity_l in ("exercise", "exercises"):
        ex_id = resolve_exercise_id_by_key(sub or key)
        update_exercise(ex_id)
    elif entity_l in ("workout", "workouts"):
        # sub-arg controls mode: 'date' | 'plan' | None (performed)
        mode = (sub or "").lower() or None
        if mode in ("date", "plan"):
            # date argument may be in 'key'; if missing, prompt
            date_arg = key
            date_sel = resolve_workout_date_key(date_arg)
            if mode == "date":
                update_workout_date(date_sel)
            else:  # plan
                if add:
                    add_workout_plan(date_sel)
                else:
                    update_workout_plan(date_sel)
        else:
            # Performed branch. If 'sub' is actually a date, treat it as key; else fall back to key.
            date_input = sub if sub else key
            date_sel = resolve_workout_date_key(date_input)
            if add:
                add_workout_performance(date_sel)
            else:
                update_workout(date_sel)
    else:
        console.print("Unknown entity. Use 'exercise' or 'workout'.")
        raise typer.Exit(1)

@app.command()
def validate():
    raw = storage._read()  # internal but fine for CLI
    validate_instance(raw)
    logical_validate(raw)
    console.print("Data valid against schema and logical rules")

@app.command(name="detail")
def detail_cmd(
    entity: str = typer.Argument(..., metavar="exercise|workout", case_sensitive=False),
    key: str | None = typer.Argument(None),
    history: bool = typer.Option(False, "--history", "--hist", help="Show exercise performance history across workouts"),
):
    entity_l = entity.lower()
    if entity_l in ("exercise", "exercises"):
        ex_id = resolve_exercise_id_by_key(key)
        if history:
            from .commands.detail_cmds import detail_exercise_history
            detail_exercise_history(ex_id)
        else:
            detail_exercise_by_id(ex_id)
    elif entity_l in ("workout", "workouts"):
        key = resolve_workout_date_key(key)
        detail_workout_by_date(key)
    else:
        console.print("Unknown entity. Use 'exercise' or 'workout'.")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
