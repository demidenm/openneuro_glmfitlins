"""Stage 3: build (or update) a BIDS Stats Models spec and check it against the design matrices.

Derived fields come from the per-dataset input files:
  Input.subject          <- ``{ds}-{label}_subjects.json``  ("Subjects")
  Input.run / session    <- ``{ds}_basic-details.json``      (Tasks[task].task_runs / task_sessions)
  Run-node Contrasts     <- ``{ds}-{label}_contrasts.json`` ("Contrasts")
Everything else (Transformations, Model, extra nodes) is hand-edited and is preserved by ``update_spec``.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Optional

from ..config import StudyPaths, read_json
from .summary import pull_contrast_conditions_spec

TEMPLATE = Path(__file__).parent / "templates" / "example_mod-specs.json"
DEFAULT_TR = 2.0
IGNORED = [r"sub-.*_physio\.(json|tsv\.gz)"]


def load_template(path: Optional[Path] = None) -> dict:
    return read_json(Path(path) if path else TEMPLATE)


def task_runs_sessions(basic_details: dict, task: str) -> tuple[list, list]:
    taskinfo = basic_details["Tasks"][task]
    return list(taskinfo.get("task_runs") or []), list(taskinfo.get("task_sessions") or [])


def find_node(spec: dict, level: str) -> Optional[dict]:
    for node in spec.get("Nodes", []):
        if node.get("Level", "").lower() == level.lower():
            return node
    return None


def build_spec(template: dict, study_id: str, task: str, subjects: list, basic_details: dict,
               contrasts: list) -> dict:
    """Fill the template with study, task, subjects, runs, sessions and Run-level contrasts."""
    spec = copy.deepcopy(template)
    runs, sessions = task_runs_sessions(basic_details, task)

    if "Name" in spec:
        spec["Name"] = f"{study_id}"
    if "Input" in spec:
        spec["Input"]["task"] = [task]
        spec["Input"]["subject"] = subjects
    if len(runs) > 1:
        spec["Input"]["run"] = runs
    if len(sessions) > 0:
        spec["Input"]["session"] = sessions

    run_node = find_node(spec, "Run")
    if run_node is not None:
        run_node["Contrasts"] = contrasts

    # one run per subject: nothing to average, so drop the Subject node
    if len(runs) < 2:
        subject_node = find_node(spec, "Subject")
        if subject_node is not None:
            print("Subject node is removed as the number of runs is less than 2 (no runs to average). "
                  "Confirm spec to ensure this behavior is correct")
            spec["Nodes"].remove(subject_node)

    # add session to every GroupBy
    if len(sessions) > 0:
        for node in spec["Nodes"]:
            group_by = node.get("GroupBy")
            if isinstance(group_by, list):
                if "session" not in group_by:
                    group_by.append("session")
            elif group_by is not None:
                print(f"GroupBy in node {node.get('Name')} is not a list; session not added")
    return spec


def update_spec(spec: dict, study_id: str, task: str, subjects: list, basic_details: dict,
                contrasts: list) -> tuple[dict, list[str]]:
    """Refresh only the derived fields of an existing spec. Returns (new_spec, list of changes)."""
    new = copy.deepcopy(spec)
    runs, sessions = task_runs_sessions(basic_details, task)
    inp = new.setdefault("Input", {})
    changes: list[str] = []

    def _set(key, value):
        old = inp.get(key)
        if value is None:
            if key in inp:
                inp.pop(key)
                changes.append(f"Input.{key}: removed (was {old})")
        elif old != value:
            inp[key] = value
            changes.append(f"Input.{key}: {old} -> {value}")

    if "Name" in new and new["Name"] != study_id:
        changes.append(f"Name: {new['Name']} -> {study_id}")
        new["Name"] = study_id
    _set("task", [task])
    _set("subject", subjects)
    _set("run", runs if len(runs) > 1 else None)
    _set("session", sessions if len(sessions) > 0 else None)

    run_node = find_node(new, "Run")
    if run_node is not None and run_node.get("Contrasts") != contrasts:
        old_names = [c.get("Name") for c in run_node.get("Contrasts", [])]
        run_node["Contrasts"] = contrasts
        changes.append(f"Run node Contrasts: {old_names} -> {[c.get('Name') for c in contrasts]}")
    return new, changes


def write_spec(spec: dict, path: Path) -> None:
    with open(path, "w") as f:
        json.dump(spec, f, indent=2)


def get_repetition_time(bids_dir: Path, task: str, default: float = DEFAULT_TR) -> float:
    """RepetitionTime from the task's BOLD sidecar (subject-level first, then the root task JSON)."""
    bids_dir = Path(bids_dir)
    candidates = []
    for pattern in (f"sub-*/func/*_task-{task}_*bold.json", f"sub-*/ses-*/func/*_task-{task}_*bold.json"):
        candidates.extend(sorted(bids_dir.glob(pattern)))
    candidates.append(bids_dir / f"task-{task}_bold.json")
    for path in candidates:
        try:
            tr = json.loads(path.read_text()).get("RepetitionTime")
        except (OSError, json.JSONDecodeError):
            continue
        if tr:
            return float(tr)
    print(f"WARNING: RepetitionTime for task '{task}' not found in {bids_dir}; using {default}s for the check.")
    return default


def check_contrast_columns(outputs, spec: dict) -> tuple[list, list, set]:
    """Return (conditions missing from every design matrix, conditions missing from some, all columns)."""
    unique_conditions = pull_contrast_conditions_spec(spec)
    per_model_columns = [set(out.X.columns) for out in outputs]
    all_columns = set().union(*per_model_columns) if per_model_columns else set()
    missing = [c for c in unique_conditions if c not in all_columns]
    subset = [c for c in unique_conditions
              if any(c in cols for cols in per_model_columns) and not all(c in cols for cols in per_model_columns)]
    return missing, subset, all_columns


def check_design(bids_dir: Path, spec: dict, scan_length: float) -> int:
    """Build run-level design matrices and confirm every contrast condition is a column. Returns exit code."""
    from .graph import get_runnode

    print()
    print("Debugging check & confirming contrast conditions map to available design matrix columns.")
    try:
        outputs = get_runnode(str(bids_dir), spec, scan_length, ignored=IGNORED)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        outputs = None

    if outputs is None:
        print("\nFailed to generate run-level outputs. Please check the errors above.")
        print("Common debugging steps:")
        print("1. Verify your BIDS directory structure")
        print("2. Check that all required event files exist")
        print("3. Validate your model specification JSON")
        print("4. Ensure event files have consistent column names and data types")
        print("5. Ensure the subjects in your specification files contain the necessary files to groupby")
        return 1
    print("Successfully generated run-level outputs!")

    missing, subset, all_columns = check_contrast_columns(outputs, spec)
    status = 0
    if missing:
        print(f"{', '.join(missing)} values used in contrast are NOT available in ANY design matrices. "
              "Review and update contrasts.\n")
        print(f"All available columns across design matrices:\n{sorted(all_columns)}\n")
        status = 1
    else:
        print("** All contrast conditions are present in at least one design matrix. ** \n")
    if subset:
        print(f"{', '.join(subset)} conditions does not appear in all subjects' design matrices.\n")
        print("Contrasts with these values will be missing for subjects and cannot be estimated\n")
    else:
        print("Conditions used in contrasts specification exist in all design matrices.\n")
    return status


def scan_length_for(paths: StudyPaths, basic_details: dict, task: str) -> float:
    volumes = basic_details["Tasks"][task].get("bold_volumes")
    if not volumes:
        raise ValueError(f"bold_volumes is missing for task '{task}' in {paths.basic_details}")
    return int(volumes) * get_repetition_time(paths.bids_dir, task)


def run_spec_step(paths: StudyPaths, task: str, suffix: Optional[str] = None, update: bool = False,
                  check: bool = True, template: Optional[Path] = None) -> int:
    """Create the spec if missing (or refresh derived fields with ``update``), then check it."""
    spec_file = paths.spec_file(task, suffix)
    contrasts_file = paths.contrasts_file(task, suffix)
    subjects_file = paths.subjects_file(task, suffix)
    print(f"Spec file: {spec_file}")

    basic_details = read_json(paths.basic_details)
    if task not in basic_details.get("Tasks", {}):
        print(f"ERROR: task '{task}' not found in {paths.basic_details}")
        return 1

    needs_inputs = update or not spec_file.exists()
    if needs_inputs and not (contrasts_file.exists() and subjects_file.exists()):
        print("ERROR: Cannot create model specifications.")
        print(f"       Missing {contrasts_file.name} or {subjects_file.name} in {paths.spec_dir}.")
        return 1

    if spec_file.exists():
        spec = read_json(spec_file)
        if update:
            new, changes = update_spec(spec, paths.study_id, task, read_json(subjects_file)["Subjects"],
                                       basic_details, read_json(contrasts_file)["Contrasts"])
            if changes:
                write_spec(new, spec_file)
                print("UPDATED derived fields:")
                for c in changes:
                    print(f"  - {c}")
            else:
                print("Spec is up to date with subjects, contrasts and basic-details files.")
            spec = new
        else:
            print("Spec file exists, not overwriting. Use --update to refresh subjects/runs/sessions/contrasts, "
                  "or delete the spec file to recreate.\n")
    else:
        print(f"Creating spec from template {template or TEMPLATE}")
        spec = build_spec(load_template(template), paths.study_id, task, read_json(subjects_file)["Subjects"],
                          basic_details, read_json(contrasts_file)["Contrasts"])
        write_spec(spec, spec_file)
        print("SUCCESS: Model specs created, updated study name, task, subjects and contrasts.")

    if not check:
        return 0
    return check_design(paths.bids_dir, spec, scan_length_for(paths, basic_details, task))
