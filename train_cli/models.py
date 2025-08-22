from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

@dataclass
class ExerciseTemplate:
    id: int
    movement: str
    position: str
    equipment: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    displayName: Optional[str] = None

@dataclass
class ExercisePerformance:
    templateId: int
    sets: int
    reps: int
    weight: Optional[float] = None
    notes: Optional[str] = None

@dataclass
class WorkoutPerformance:
    date: date
    exercisePerformance: List[ExercisePerformance] = field(default_factory=list)

@dataclass
class RootData:
    workouts: List[WorkoutPerformance] = field(default_factory=list)
    exercises: List[ExerciseTemplate] = field(default_factory=list)
