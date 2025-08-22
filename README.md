# Train CLI

A small interactive CLI to manage a workout chronology conforming to `schema.json`.

## Install (editable)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

List commands:

```bash
train --help
```

Add an exercise:

```bash
train add exercise
```

List items:

```bash
train list exercise
train list workout
```

Add items:

```bash
train add exercise
train add workout
```

Validate stored data:

```bash
train validate
```

Data stored in `data.json` in project root.
