from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
from . import models
from .validators import validate_instance, logical_validate
from datetime import date

DATA_FILE = Path("data.json")
SCHEMA_FILE = Path("schema.json")

class Storage:
    def __init__(self, path: Path = DATA_FILE):
        self.path = path
        if not self.path.exists():
            self._write({"workouts": [], "exercises": []})

    def _read(self) -> Dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> models.RootData:
        raw = self._read()
        # Simple parsing
        workouts = []
        for w in raw.get("workouts", []):
            workouts.append(
                models.WorkoutPerformance(
                    date=date.fromisoformat(w["date"]),
                    exercisePerformance=[
                        models.ExercisePerformance(**ep) for ep in w.get("exercisePerformance", [])
                    ],
                )
            )
        exercises = [models.ExerciseTemplate(**e) for e in raw.get("exercises", [])]
        return models.RootData(workouts=workouts, exercises=exercises)

    def save(self, root: models.RootData) -> None:
        data = {
            "workouts": [
                {
                    "date": w.date.isoformat(),
                    "exercisePerformance": [ep.__dict__ for ep in w.exercisePerformance],
                }
                for w in root.workouts
            ],
            "exercises": [e.__dict__ for e in root.exercises],
        }
        # Validate before persisting
        validate_instance(data)
        logical_validate(data)
        self._write(data)
