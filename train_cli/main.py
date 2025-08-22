from __future__ import annotations
import typer
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.console import Console
from datetime import date
from typing import Optional
from .storage import Storage
from . import models
from .validators import validate_instance, logical_validate, SCHEMA
import json
from .prompting import choose, ask_number, pick_date

app = typer.Typer(help="Manage workout chronology data")
console = Console()
storage = Storage()

def list_exercises():
    data = storage.load()
    table = Table(title="Exercises")
    table.add_column("ID", justify="right")
    table.add_column("Display")
    table.add_column("Movement")
    table.add_column("Position")
    table.add_column("Equipment")
    for e in data.exercises:
        table.add_row(str(e.id), e.displayName or ",".join(e.aliases), e.movement, e.position, e.equipment or "-")
    console.print(table)

def add_exercise():
    data = storage.load()
    next_id = (max((e.id for e in data.exercises), default=0) + 1)
    movement = choose("Movement", ["Push","Pull"], default="Push")
    position = choose("Position", ["Seated","Standing","Kneeling","Supine","Prone","Erect","Hanging"], default="Standing")
    # Ask for angle immediately if seated
    angle = None
    if position == "Seated":
        angle = choose("Seat angle (deg)", [90, 60, 45, 30, 0], default=90)
    equipment_choice = choose("Equipment (blank for none)", ["", "Barbell","Dumbbells","Kettlebell","Cable","Pulley"], default="", allow_blank=True)
    equipment = equipment_choice or None
    aliases_raw = Prompt.ask("Aliases (comma separated)")
    aliases = [a.strip() for a in aliases_raw.split(",") if a.strip()]
    display = choose("Display name", aliases, default=aliases[0]) if aliases else None
    ex = models.ExerciseTemplate(id=next_id, movement=movement, position=position, equipment=equipment, angle=angle, aliases=aliases, displayName=display)
    data.exercises.append(ex)
    storage.save(data)
    console.print(f"Added exercise {ex.id} -> {ex.displayName}")

def delete_exercise(exercise_id: int = typer.Argument(..., help="Exercise id")):
    data = storage.load()
    before = len(data.exercises)
    data.exercises = [e for e in data.exercises if e.id != exercise_id]
    after = len(data.exercises)
    storage.save(data)
    console.print("Deleted" if after < before else "No change")

def update_exercise(exercise_id: int = typer.Argument(..., help="Exercise id to update")):
    data = storage.load()
    ex = next((e for e in data.exercises if e.id == exercise_id), None)
    if not ex:
        console.print("Not found")
        raise typer.Exit(1)
    movement = choose("Movement", ["Push","Pull"], default=ex.movement)
    position = choose("Position", ["Seated","Standing","Kneeling","Supine","Prone","Erect","Hanging"], default=ex.position)
    # Ask for angle immediately if seated (compute now, assign later)
    if position == "Seated":
        default_angle = int(ex.angle) if ex.angle is not None else 90
        new_angle = choose("Seat angle (deg)", [90, 60, 45, 30, 0], default=default_angle)
    else:
        new_angle = None
    equipment_choices = ["Barbell","Dumbbells","Kettlebell","Cable","Pulley",""]
    equipment_choice = choose("Equipment (blank for none)", ["", "Barbell","Dumbbells","Kettlebell","Cable","Pulley"], default=ex.equipment or "", allow_blank=True)
    equipment = equipment_choice or None
    aliases_raw = Prompt.ask("Aliases (comma separated)", default=",".join(ex.aliases))
    aliases = [a.strip() for a in aliases_raw.split(",") if a.strip()]
    display = choose("Display name", aliases, default=ex.displayName or (aliases[0] if aliases else "")) if aliases else None
    ex.movement = movement
    ex.position = position
    ex.angle = new_angle
    ex.equipment = equipment
    ex.aliases = aliases
    ex.displayName = display
    storage.save(data)
    console.print(f"Updated exercise {ex.id}")

def list_workouts():
    data = storage.load()
    table = Table(title="Workouts")
    table.add_column("Date")
    table.add_column("Exercises")
    for w in data.workouts:
        table.add_row(w.date.isoformat(), ",".join(str(ep.templateId) for ep in w.exercisePerformance))
    console.print(table)

# Unified, human-friendly commands
@app.command(name="list")
def list_cmd(
    entity: str = typer.Argument(..., metavar="exercise|workout", case_sensitive=False),
):
    entity_l = entity.lower()
    if entity_l in ("exercise", "exercises"):
        list_exercises()
    elif entity_l in ("workout", "workouts"):
        list_workouts()
    else:
        console.print("Unknown entity. Use 'exercise' or 'workout'.")
        raise typer.Exit(1)

def add_workout():
    data = storage.load()
    picked = pick_date(date.today())
    if picked is None:
        console.print("Cancelled")
        raise typer.Exit()
    d_str = picked.isoformat()
    try:
        d = date.fromisoformat(d_str)
    except ValueError:
        console.print("Invalid date format. Expected YYYY-MM-DD.")
        raise typer.Exit(1)
    ex_ids = [e.id for e in data.exercises]
    if not ex_ids:
        console.print("No exercises defined. Add exercises first.")
        raise typer.Exit(1)
    chosen: list[int] = []
    pending: list[models.ExercisePerformance] = []
    while True:
        # Exercise id with completion
        id_choices = [str(i) for i in ex_ids]
        id_str = choose("Add exercise id (blank to finish)", id_choices, allow_blank=True, default="")
        if not id_str:
            break
        try:
            i = int(id_str)
        except ValueError:
            console.print("Not an integer")
            continue
        if i not in ex_ids:
            console.print("Unknown id")
            continue
        sets = int(ask_number("Sets", default=3))
        reps = int(ask_number("Reps", default=10))
        weight_num = ask_number("Weight (blank for none)", default=None, allow_blank=True)
        weight_val = float(weight_num) if weight_num is not None else None
        data_workout = models.ExercisePerformance(templateId=i, sets=sets, reps=reps, weight=weight_val)
        chosen.append(i)
        pending.append(data_workout)
    if not pending:
        console.print("No exercises added")
        raise typer.Exit()
    w = models.WorkoutPerformance(date=d, exercisePerformance=pending)
    data.workouts.append(w)
    storage.save(data)
    console.print(f"Added workout on {d.isoformat()} with {len(pending)} exercises")

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

def delete_workout(date_str: str = typer.Argument(..., help="Workout date YYYY-MM-DD")):
    data = storage.load()
    before = len(data.workouts)
    data.workouts = [w for w in data.workouts if w.date.isoformat() != date_str]
    after = len(data.workouts)
    storage.save(data)
    console.print("Deleted" if after < before else "No change")

@app.command(name="delete")
def delete_cmd(
    entity: str = typer.Argument(..., metavar="exercise|workout", case_sensitive=False),
    key: str | None = typer.Argument(None),
):
    entity_l = entity.lower()
    if entity_l in ("exercise", "exercises"):
        data = storage.load()
        choices = [e.displayName for e in data.exercises if e.displayName]
        if not choices:
            console.print("No exercises with a display name found to delete.")
            raise typer.Exit(1)
        name = choose("Exercise to delete (display name)", choices)
        before = len(data.exercises)
        data.exercises = [e for e in data.exercises if (e.displayName or "").strip().lower() != str(name).strip().lower()]
        after = len(data.exercises)
        storage.save(data)
        console.print("Deleted" if after < before else "No change")
    elif entity_l in ("workout", "workouts"):
        # If no key provided, prompt for a date from existing workouts
        if key is None:
            data = storage.load()
            dates = [w.date.isoformat() for w in data.workouts]
            if not dates:
                console.print("No workouts found.")
                raise typer.Exit(1)
            key = choose("Workout date to delete", dates)
        delete_workout(key)
    else:
        console.print("Unknown entity. Use 'exercise' or 'workout'.")
        raise typer.Exit(1)

def update_workout(date_str: str = typer.Argument(..., help="Workout date YYYY-MM-DD to update")):
    data = storage.load()
    w = next((w for w in data.workouts if w.date.isoformat() == date_str), None)
    if not w:
        console.print("Not found")
        raise typer.Exit(1)
    console.print("Editing workout. Leave blank to keep existing values for each exercise or enter 'd' to delete an entry.")
    new_eps = []
    for ep in w.exercisePerformance:
        action = Prompt.ask(f"Exercise {ep.templateId} sets={ep.sets} reps={ep.reps} (enter to keep / d delete / e edit)", default="")
        if action == "d":
            continue
        elif action == "e":
            sets = IntPrompt.ask("Sets", default=ep.sets)
            reps = IntPrompt.ask("Reps", default=ep.reps)
            weight_in = Prompt.ask("Weight (blank to keep / none to clear)", default="")
            if weight_in == "none":
                weight_val = None
            elif weight_in == "":
                weight_val = ep.weight
            else:
                weight_val = float(weight_in)
            new_eps.append(models.ExercisePerformance(templateId=ep.templateId, sets=sets, reps=reps, weight=weight_val, notes=ep.notes))
        else:
            new_eps.append(ep)
    # Add new exercise performances
    while Confirm.ask("Add another exercise performance?", default=False):
        ex_ids = [e.id for e in data.exercises]
        id_str = choose("Exercise id", [str(i) for i in ex_ids])
        i = int(id_str)
        sets = int(ask_number("Sets", default=3))
        reps = int(ask_number("Reps", default=10))
        weight_num = ask_number("Weight (blank for none)", default=None, allow_blank=True)
        weight_val = float(weight_num) if weight_num is not None else None
        new_eps.append(models.ExercisePerformance(templateId=i, sets=sets, reps=reps, weight=weight_val))
    w.exercisePerformance = new_eps
    storage.save(data)
    console.print("Workout updated")

@app.command(name="update")
def update_cmd(
    entity: str = typer.Argument(..., metavar="exercise|workout", case_sensitive=False),
    key: str | None = typer.Argument(None),
):
    entity_l = entity.lower()
    if entity_l in ("exercise", "exercises"):
        data = storage.load()
        # If key provided, allow id or display name; otherwise prompt by display name
        ex_id: int | None = None
        if key is None:
            names = [e.displayName for e in data.exercises if e.displayName]
            if not names:
                console.print("No exercises found.")
                raise typer.Exit(1)
            chosen = choose("Exercise to update (display name)", names)
            # map to id (first match ignoring case)
            for e in data.exercises:
                if (e.displayName or "").strip().lower() == str(chosen).strip().lower():
                    ex_id = e.id
                    break
        else:
            # try id first
            try:
                ex_id = int(key)
            except ValueError:
                # treat as display name
                for e in data.exercises:
                    if (e.displayName or "").strip().lower() == key.strip().lower():
                        ex_id = e.id
                        break
        if ex_id is None:
            console.print("Exercise not found.")
            raise typer.Exit(1)
        update_exercise(ex_id)
    elif entity_l in ("workout", "workouts"):
        if key is None:
            data = storage.load()
            dates = [w.date.isoformat() for w in data.workouts]
            if not dates:
                console.print("No workouts found.")
                raise typer.Exit(1)
            key = choose("Workout date to update", dates)
        update_workout(key)
    else:
        console.print("Unknown entity. Use 'exercise' or 'workout'.")
        raise typer.Exit(1)

@app.command()
def validate():
    raw = storage._read()  # internal but fine for CLI
    validate_instance(raw)
    logical_validate(raw)
    console.print("Data valid against schema and logical rules")

if __name__ == "__main__":
    app()
