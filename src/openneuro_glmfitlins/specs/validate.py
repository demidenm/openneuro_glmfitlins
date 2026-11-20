"""Validate a spec against its subjects/contrasts/basic-details files (drift) and internal consistency.

Errors (exit 1):
  - Input.task differs from the task
  - Input.subject differs from subjects.json
  - Run-node Contrasts differ from contrasts.json
  - a contrast's Weights length differs from its ConditionList length
  - (with --check-design) a contrast condition is not a column in any design matrix
Warnings:
  - Input.run / Input.session differ from basic-details (may be an intentional restriction)
  - a difference contrast (positive and negative weights) whose weights do not sum to 0
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..config import StudyPaths, read_json
from .build import find_node, task_runs_sessions


@dataclass(frozen=True)
class Issue:
    level: str  # "error" | "warning"
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper()}: {self.message}"


def _diff(label: str, have, want) -> str:
    have_s, want_s = set(map(str, have or [])), set(map(str, want or []))
    parts = [f"{label} differs"]
    if want_s - have_s:
        parts.append(f"missing from spec: {sorted(want_s - have_s)}")
    if have_s - want_s:
        parts.append(f"extra in spec: {sorted(have_s - want_s)}")
    if have_s == want_s:
        parts.append("(same values, different order or type)")
    return "; ".join(parts)


def _same(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return sorted(map(str, a)) == sorted(map(str, b))


def _weight_rows(weights) -> list:
    if weights and all(isinstance(w, list) for w in weights):
        return weights  # F-test: one row per condition set
    return [weights]


def check_contrast_weights(spec: dict) -> list[Issue]:
    issues = []
    for node in spec.get("Nodes", []):
        for con in node.get("Contrasts", []) or []:
            name = f"{node.get('Name', node.get('Level'))}:{con.get('Name')}"
            conds = con.get("ConditionList", [])
            for row in _weight_rows(con.get("Weights", [])):
                if len(row) != len(conds):
                    issues.append(Issue("error", f"contrast {name}: {len(row)} weights for {len(conds)} conditions"))
                    continue
                nums = [w for w in row if isinstance(w, (int, float))]
                if any(w > 0 for w in nums) and any(w < 0 for w in nums) and abs(sum(nums)) > 1e-8:
                    issues.append(Issue("warning", f"contrast {name}: difference weights {row} sum to {sum(nums):g}, not 0"))
    return issues


def validate_spec(spec: dict, task: str, subjects: Optional[list], basic_details: Optional[dict],
                  contrasts: Optional[list]) -> list[Issue]:
    """Return all issues found. Pass None for an input file that is not available to skip that check."""
    issues: list[Issue] = []
    inp = spec.get("Input", {})

    if inp.get("task") != [task]:
        issues.append(Issue("error", f"Input.task is {inp.get('task')}, expected {[task]}"))

    if subjects is not None and not _same(inp.get("subject", []), subjects):
        issues.append(Issue("error", _diff("Input.subject vs subjects.json", inp.get("subject"), subjects)))

    if basic_details is not None and task in basic_details.get("Tasks", {}):
        runs, sessions = task_runs_sessions(basic_details, task)
        want_runs = runs if len(runs) > 1 else None
        want_sessions = sessions if len(sessions) > 0 else None
        for key, want in (("run", want_runs), ("session", want_sessions)):
            have = inp.get(key)
            if _same(have, want):
                continue
            label = f"Input.{key} vs basic-details task_{key}s"
            if have is None:
                msg = (f"Input.{key} is not set, so all {key}s found in the data are used by default; "
                       f"basic-details lists {sorted(map(str, want))}. Harmless if that is intended; "
                       f"run `glmfitlins spec --update` to pin them.")
            else:
                msg = _diff(label, have, want)
            issues.append(Issue("warning", msg))

    if contrasts is not None:
        run_node = find_node(spec, "Run")
        if run_node is None:
            issues.append(Issue("error", "spec has no Run-level node"))
        elif run_node.get("Contrasts") != contrasts:
            have = [c.get("Name") for c in run_node.get("Contrasts", [])]
            want = [c.get("Name") for c in contrasts]
            detail = _diff("Run-node Contrasts vs contrasts.json", have, want) if have != want \
                else "Run-node Contrasts vs contrasts.json differ in ConditionList/Weights/Test"
            issues.append(Issue("error", detail))

    issues.extend(check_contrast_weights(spec))
    return issues


def run_validate(paths: StudyPaths, task: str, suffix: Optional[str] = None, check_design: bool = False) -> int:
    spec_file = paths.spec_file(task, suffix)
    if not spec_file.exists():
        print(f"ERROR: spec file not found: {spec_file}")
        return 1
    spec = read_json(spec_file)

    def _maybe(path, key):
        if path.exists():
            return read_json(path)[key] if key else read_json(path)
        print(f"NOTE: {path.name} not found; skipping that check")
        return None

    subjects = _maybe(paths.subjects_file(task, suffix), "Subjects")
    contrasts = _maybe(paths.contrasts_file(task, suffix), "Contrasts")
    basic = _maybe(paths.basic_details, None)

    print(f"Validating {spec_file}")
    issues = validate_spec(spec, task, subjects, basic, contrasts)
    for issue in issues:
        print(f"  {issue}")
    n_err = sum(i.level == "error" for i in issues)
    n_warn = len(issues) - n_err
    print(f"{n_err} error(s), {n_warn} warning(s)."
          + (" Run `glmfitlins spec ... --update` to refresh derived fields." if n_err else ""))

    status = 1 if n_err else 0
    if check_design and basic is not None:
        from .build import check_design as _check_design, scan_length_for

        status = max(status, _check_design(paths.bids_dir, spec, scan_length_for(paths, basic, task)))
    return status
