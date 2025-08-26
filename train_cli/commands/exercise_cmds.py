from __future__ import annotations
import typer
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.console import Console
from ..storage import Storage
from .. import models
from ..prompting import choose

console = Console()
storage = Storage()

def add_exercise():
    data = storage.load()
    next_id = (max((e.id for e in data.exercises), default=0) + 1)
    movement = choose("Movement", ["Push","Pull"], default="Push")
    position = choose("Position", ["Seated","Standing","Kneeling","Supine","Prone","Erect","Hanging"], default="Standing")
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

def update_exercise(exercise_id: int = typer.Argument(...)):
    data = storage.load()
    ex = next((e for e in data.exercises if e.id == exercise_id), None)
    if not ex:
        console.print("Not found")
        raise typer.Exit(1)
    movement = choose("Movement", ["Push","Pull"], default=ex.movement)
    position = choose("Position", ["Seated","Standing","Kneeling","Supine","Prone","Erect","Hanging"], default=ex.position)
    if position == "Seated":
        default_angle = int(ex.angle) if ex.angle is not None else 90
        new_angle = choose("Seat angle (deg)", [90, 60, 45, 30, 0], default=default_angle)
    else:
        new_angle = None
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

def delete_exercise_by_key(key: str | None):
    data = storage.load()
    before = len(data.exercises)
    if key is not None:
        try:
            ex_id = int(key)
            data.exercises = [e for e in data.exercises if e.id != ex_id]
        except ValueError:
            name_l = key.strip().lower()
            data.exercises = [e for e in data.exercises if (e.displayName or "").strip().lower() != name_l]
        storage.save(data)
        console.print("Deleted" if len(data.exercises) < before else "No change")
    else:
        choices = [e.displayName for e in data.exercises if e.displayName]
        if not choices:
            console.print("No exercises with a display name found to delete.")
            raise typer.Exit(1)
        name = choose("Exercise to delete (display name)", choices)
        data.exercises = [e for e in data.exercises if (e.displayName or "").strip().lower() != str(name).strip().lower()]
        storage.save(data)
        console.print("Deleted" if len(data.exercises) < before else "No change")

def resolve_exercise_id_by_key(key: str | None) -> int:
    data = storage.load()
    if key is None:
        names = [e.displayName for e in data.exercises if e.displayName]
        if not names:
            console.print("No exercises found.")
            raise typer.Exit(1)
        chosen = choose("Exercise (display name)", names)
        for e in data.exercises:
            if (e.displayName or "").strip().lower() == str(chosen).strip().lower():
                return e.id
    else:
        try:
            return int(key)
        except ValueError:
            for e in data.exercises:
                if (e.displayName or "").strip().lower() == key.strip().lower():
                    return e.id
    console.print("Exercise not found.")
    raise typer.Exit(1)
