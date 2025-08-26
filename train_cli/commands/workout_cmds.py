from __future__ import annotations
import typer
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.console import Console
from rich.table import Table
from datetime import date
from ..storage import Storage
from .. import models
from ..prompting import choose, ask_number, pick_date

console = Console()
storage = Storage()

def list_workouts():
    from .list_cmds import list_workouts as _lw
    return _lw()

def add_workout():
    data = storage.load()
    picked = pick_date(date.today())
    if picked is None:
        console.print("Cancelled")
        raise typer.Exit()
    d = picked
    chosen: list[int] = []
    pending: list[models.ExercisePerformance] = []
    name_to_id = { (e.displayName or '').strip().lower(): e.id for e in data.exercises if e.displayName }
    name_choices = [e.displayName for e in data.exercises if e.displayName]
    while True:
        choices_with_new = ["new"] + name_choices
        name = choose("Add exercise (display name or 'new'; blank to finish)", choices_with_new, allow_blank=True, default="")
        if not name:
            break
        if str(name).strip().lower() == "new":
            before_ids = {e.id for e in data.exercises}
            from .exercise_cmds import add_exercise
            add_exercise()
            data = storage.load()
            after_ids = {e.id for e in data.exercises}
            new_ids = sorted(after_ids - before_ids)
            if not new_ids:
                console.print("No exercise was created.")
                continue
            i = new_ids[-1]
            name_to_id = { (e.displayName or '').strip().lower(): e.id for e in data.exercises if e.displayName }
            name_choices = [e.displayName for e in data.exercises if e.displayName]
        else:
            i = name_to_id.get(str(name).strip().lower())
            if i is None:
                console.print("Unknown exercise name")
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

def plan_workout():
    """Plan a workout by selecting a date and adding intended exercise performances.
    Uses the same name/new flow, saving to intendedExercisePerformance.
    """
    data = storage.load()
    picked = pick_date(date.today())
    if picked is None:
        console.print("Cancelled")
        raise typer.Exit()
    d = picked
    # Find existing workout on that date or create a new empty one
    w = next((w for w in data.workouts if w.date == d), None)
    if w is None:
        w = models.WorkoutPerformance(date=d)
        data.workouts.append(w)
    pending: list[models.ExercisePerformance] = []
    name_to_id = { (e.displayName or '').strip().lower(): e.id for e in data.exercises if e.displayName }
    name_choices = [e.displayName for e in data.exercises if e.displayName]
    while True:
        choices_with_new = ["new"] + name_choices
        name = choose("Add intended exercise (display name or 'new'; blank to finish)", choices_with_new, allow_blank=True, default="")
        if not name:
            break
        if str(name).strip().lower() == "new":
            before_ids = {e.id for e in data.exercises}
            from .exercise_cmds import add_exercise
            add_exercise()
            data = storage.load()
            after_ids = {e.id for e in data.exercises}
            new_ids = sorted(after_ids - before_ids)
            if not new_ids:
                console.print("No exercise was created.")
                continue
            i = new_ids[-1]
            name_to_id = { (e.displayName or '').strip().lower(): e.id for e in data.exercises if e.displayName }
            name_choices = [e.displayName for e in data.exercises if e.displayName]
        else:
            i = name_to_id.get(str(name).strip().lower())
            if i is None:
                console.print("Unknown exercise name")
                continue
        sets = int(ask_number("Sets", default=3))
        reps = int(ask_number("Reps", default=10))
        weight_num = ask_number("Weight (blank for none)", default=None, allow_blank=True)
        weight_val = float(weight_num) if weight_num is not None else None
        pending.append(models.ExercisePerformance(templateId=i, sets=sets, reps=reps, weight=weight_val))
    if not pending:
        console.print("No intended exercises added")
        raise typer.Exit()
    # Append to intendedExercisePerformance (preserve any existing intended list)
    w.intendedExercisePerformance.extend(pending)
    storage.save(data)
    console.print(f"Planned workout on {d.isoformat()} with {len(pending)} intended exercises")

def delete_workout(date_str: str):
    data = storage.load()
    before = len(data.workouts)
    data.workouts = [w for w in data.workouts if w.date.isoformat() != date_str]
    after = len(data.workouts)
    storage.save(data)
    console.print("Deleted" if after < before else "No change")

def update_workout(date_str: str):
    data = storage.load()
    w = next((w for w in data.workouts if w.date.isoformat() == date_str), None)
    if not w:
        console.print("Not found")
        raise typer.Exit(1)
    console.print("Editing performed exercises. Enter to keep, 'd' to delete, 'e' to edit (name, weight, sets, reps). Use '--add' to add new entries.")
    new_eps = []
    id_to_name = {e.id: (e.displayName or ",".join(e.aliases) or str(e.id)) for e in data.exercises}
    for ep in w.exercisePerformance:
        ex_name = id_to_name.get(ep.templateId, str(ep.templateId))
        action = Prompt.ask(
            f"Exercise {ex_name} (id {ep.templateId}) sets={ep.sets} reps={ep.reps} (enter keep / d delete / e edit)",
            default="",
        )
        if action == "d":
            continue
        elif action == "e":
            # Show a small table of current values
            t = Table(title="Edit Exercise Performance")
            t.add_column("Field")
            t.add_column("Value")
            t.add_row("Name", ex_name)
            t.add_row("Weight", "-" if ep.weight is None else str(ep.weight))
            t.add_row("Sets", str(ep.sets))
            t.add_row("Reps", str(ep.reps))
            console.print(t)

            # 1) Name (exercise): allow choosing existing or create new; default to current name
            name_to_id = { (e.displayName or '').strip().lower(): e.id for e in data.exercises if e.displayName }
            name_choices = [e.displayName for e in data.exercises if e.displayName]
            choices_with_new = ["new"] + name_choices
            new_name = choose("Exercise name (or 'new')", choices_with_new, default=ex_name)
            new_template_id = ep.templateId
            if str(new_name).strip().lower() == "new":
                before_ids = {e.id for e in data.exercises}
                from .exercise_cmds import add_exercise
                add_exercise()
                data = storage.load()
                after_ids = {e.id for e in data.exercises}
                new_ids = sorted(after_ids - before_ids)
                if new_ids:
                    new_template_id = new_ids[-1]
                else:
                    console.print("No exercise was created; keeping current exercise.")
            else:
                resolved = name_to_id.get(str(new_name).strip().lower())
                if resolved is not None:
                    new_template_id = resolved

            # 2) Weight
            weight_in = Prompt.ask("Weight (blank to keep / none to clear)", default="")
            if weight_in == "none":
                weight_val = None
            elif weight_in == "":
                weight_val = ep.weight
            else:
                weight_val = float(weight_in)

            # 3) Sets
            sets = IntPrompt.ask("Sets", default=ep.sets)

            # 4) Reps
            reps = IntPrompt.ask("Reps", default=ep.reps)

            new_eps.append(models.ExercisePerformance(templateId=new_template_id, sets=sets, reps=reps, weight=weight_val, notes=ep.notes))
        else:
            new_eps.append(ep)
    w.exercisePerformance = new_eps
    storage.save(data)
    console.print("Workout updated")

def add_workout_performance(date_str: str):
    data = storage.load()
    w = next((w for w in data.workouts if w.date.isoformat() == date_str), None)
    if not w:
        console.print("Not found")
        raise typer.Exit(1)
    added = 0
    while True:
        name_to_id = { (e.displayName or '').strip().lower(): e.id for e in data.exercises if e.displayName }
        name_choices = [e.displayName for e in data.exercises if e.displayName]
        choices_with_new = ["new"] + name_choices
        name = choose("Add exercise performance (display name or 'new'; blank to finish)", choices_with_new, allow_blank=True, default="")
        if not name:
            break
        if str(name).strip().lower() == "new":
            before_ids = {e.id for e in data.exercises}
            from .exercise_cmds import add_exercise
            add_exercise()
            data = storage.load()
            after_ids = {e.id for e in data.exercises}
            new_ids = sorted(after_ids - before_ids)
            if not new_ids:
                console.print("No exercise was created.")
                continue
            i = new_ids[-1]
        else:
            i = name_to_id.get(str(name).strip().lower())
            if i is None:
                console.print("Unknown exercise name")
                continue
        sets = int(ask_number("Sets", default=3))
        reps = int(ask_number("Reps", default=10))
        weight_num = ask_number("Weight (blank for none)", default=None, allow_blank=True)
        weight_val = float(weight_num) if weight_num is not None else None
        w.exercisePerformance.append(models.ExercisePerformance(templateId=i, sets=sets, reps=reps, weight=weight_val))
        added += 1
    storage.save(data)
    console.print(f"Added {added} exercise performance(s)")

def update_workout_plan(date_str: str):
    data = storage.load()
    w = next((w for w in data.workouts if w.date.isoformat() == date_str), None)
    if not w:
        console.print("Not found")
        raise typer.Exit(1)
    console.print("Editing intended exercises. Select an entry to edit or delete; use '--add' to add new entries.")
    if not getattr(w, "intendedExercisePerformance", None):
        console.print("No intended exercises. Use '--add' to add.")
        raise typer.Exit(1)
    id_to_name = {e.id: (e.displayName or ",".join(e.aliases) or str(e.id)) for e in data.exercises}
    while True:
        # Build dropdown of intended entries
        options = []
        index_by_opt = {}
        for i, ep in enumerate(w.intendedExercisePerformance, start=1):
            name = id_to_name.get(ep.templateId, str(ep.templateId))
            weight_str = "-" if ep.weight is None else str(ep.weight)
            opt = f"{i}. {name} — {ep.sets}x{ep.reps} @ {weight_str}"
            options.append(opt)
            index_by_opt[opt.lower()] = i - 1
        sel = choose("Choose intended to edit/delete (blank to finish)", options, allow_blank=True, default="")
        if not sel:
            break
        idx = index_by_opt.get(str(sel).lower())
        if idx is None:
            console.print("Invalid selection")
            continue
        ep = w.intendedExercisePerformance[idx]
        action = choose("Action", ["edit", "delete"], default="edit")
        if action == "delete":
            del w.intendedExercisePerformance[idx]
            storage.save(data)
            console.print("Deleted intended exercise")
            continue
        # Edit
        ex_name = id_to_name.get(ep.templateId, str(ep.templateId))
        t = Table(title="Edit Intended Exercise")
        t.add_column("Field")
        t.add_column("Value")
        t.add_row("Name", ex_name)
        t.add_row("Weight", "-" if ep.weight is None else str(ep.weight))
        t.add_row("Sets", str(ep.sets))
        t.add_row("Reps", str(ep.reps))
        console.print(t)
        name_to_id = { (e.displayName or '').strip().lower(): e.id for e in data.exercises if e.displayName }
        name_choices = [e.displayName for e in data.exercises if e.displayName]
        choices_with_new = ["new"] + name_choices
        new_name = choose("Exercise name (or 'new')", choices_with_new, default=ex_name)
        new_template_id = ep.templateId
        if str(new_name).strip().lower() == "new":
            before_ids = {e.id for e in data.exercises}
            from .exercise_cmds import add_exercise
            add_exercise()
            data = storage.load()
            after_ids = {e.id for e in data.exercises}
            new_ids = sorted(after_ids - before_ids)
            if new_ids:
                new_template_id = new_ids[-1]
            else:
                console.print("No exercise was created; keeping current exercise.")
        else:
            resolved = name_to_id.get(str(new_name).strip().lower())
            if resolved is not None:
                new_template_id = resolved
        weight_in = Prompt.ask("Weight (blank to keep / none to clear)", default="")
        if weight_in == "none":
            weight_val = None
        elif weight_in == "":
            weight_val = ep.weight
        else:
            weight_val = float(weight_in)
        sets = IntPrompt.ask("Sets", default=ep.sets)
        reps = IntPrompt.ask("Reps", default=ep.reps)
        w.intendedExercisePerformance[idx] = models.ExercisePerformance(templateId=new_template_id, sets=sets, reps=reps, weight=weight_val, notes=ep.notes)
        storage.save(data)
        console.print("Intended exercise updated")

def add_workout_plan(date_str: str):
    data = storage.load()
    w = next((w for w in data.workouts if w.date.isoformat() == date_str), None)
    if not w:
        console.print("Not found")
        raise typer.Exit(1)
    added = 0
    while True:
        name_to_id = { (e.displayName or '').strip().lower(): e.id for e in data.exercises if e.displayName }
        name_choices = [e.displayName for e in data.exercises if e.displayName]
        choices_with_new = ["new"] + name_choices
        name = choose("Add intended exercise (display name or 'new'; blank to finish)", choices_with_new, allow_blank=True, default="")
        if not name:
            break
        if str(name).strip().lower() == "new":
            before_ids = {e.id for e in data.exercises}
            from .exercise_cmds import add_exercise
            add_exercise()
            data = storage.load()
            after_ids = {e.id for e in data.exercises}
            new_ids = sorted(after_ids - before_ids)
            if not new_ids:
                console.print("No exercise was created.")
                continue
            i = new_ids[-1]
        else:
            i = name_to_id.get(str(name).strip().lower())
            if i is None:
                console.print("Unknown exercise name")
                continue
        sets = int(ask_number("Sets", default=3))
        reps = int(ask_number("Reps", default=10))
        weight_num = ask_number("Weight (blank for none)", default=None, allow_blank=True)
        weight_val = float(weight_num) if weight_num is not None else None
        if not hasattr(w, 'intendedExercisePerformance'):
            w.intendedExercisePerformance = []
        w.intendedExercisePerformance.append(models.ExercisePerformance(templateId=i, sets=sets, reps=reps, weight=weight_val))
        added += 1
    storage.save(data)
    console.print(f"Added {added} intended exercise(s)")

def update_workout_date(date_str: str):
    data = storage.load()
    w = next((w for w in data.workouts if w.date.isoformat() == date_str), None)
    if not w:
        console.print("Not found")
        raise typer.Exit(1)
    new_d = pick_date(w.date)
    if new_d is None:
        console.print("Cancelled")
        raise typer.Exit()
    w.date = new_d
    storage.save(data)
    console.print(f"Workout date updated to {new_d.isoformat()}")

def resolve_workout_date_key(key: str | None) -> str:
    data = storage.load()
    if key is None:
        # Sort by date descending and keep ISO format for choices
        workouts_sorted = sorted(data.workouts, key=lambda w: w.date, reverse=True)
        dates = [w.date.isoformat() for w in workouts_sorted]
        if not dates:
            console.print("No workouts found.")
            raise typer.Exit(1)
        return choose("Workout date", dates)
    return key
