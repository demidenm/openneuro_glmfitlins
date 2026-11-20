"""Stage 2: trim dummy volumes, apply the dataset's event fixes, check for missing events."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import pandas as pd

from .common import EventsContext
from .registry import get_events_fixer

BACKUP_SUFFIX = ".orig"


def backup_path(events_path: Path) -> Path:
    events_path = Path(events_path)
    return events_path.with_name(events_path.name + BACKUP_SUFFIX)


def alt_path(path: Path, deriv_dir: Path, alt_dir: Path) -> Path:
    """Map ``deriv_dir/<rel>`` to ``alt_dir/<rel>``; raise ValueError if ``path`` is not under ``deriv_dir``."""
    return Path(alt_dir) / Path(path).resolve().relative_to(Path(deriv_dir).resolve())


def apply_events_fix(fixer, events_path: Path, task: str, study_id: str, bids_layout=None) -> str:
    """Apply ``fixer`` to one events file. Returns 'modified' or 'unchanged'.

    The fix is always applied to the original content: on the first write the file is copied to
    ``<name>.orig``, and later runs read from that backup. Re-running therefore gives the same
    result and never stacks fixes. The file is rewritten only if the result differs from what is
    on disk.
    """
    events_path = Path(events_path)
    orig = backup_path(events_path)
    source = orig if orig.exists() else events_path
    events_df = pd.read_csv(source, sep="\t")
    ctx = EventsContext(path=events_path, study_id=study_id, task=task, bids_layout=bids_layout)

    result = fixer(events_df, task, ctx)
    if result is None:
        if source == orig and events_path.exists():
            # fix says the original needs no change, so restore it if it was modified earlier
            if orig.read_bytes() != events_path.read_bytes():
                shutil.copy2(orig, events_path)
                return "modified"
        return "unchanged"

    new_text = result.to_csv(sep="\t", index=False)
    if events_path.exists() and events_path.read_text() == new_text:
        return "unchanged"
    if not orig.exists() and events_path.exists():
        shutil.copy2(events_path, orig)
    result.to_csv(events_path, sep="\t", index=False)
    return "modified"


def _layout(root: Path, derivatives: bool):
    from bids.layout import BIDSLayout

    try:
        return BIDSLayout(str(root), derivatives=derivatives)
    except FileNotFoundError as e:
        raise RuntimeError(f"Path '{root}' not found or missing dataset_description.json. "
                           "Please check that the directory exists and is a valid BIDS folder.") from e
    except Exception as e:
        raise RuntimeError(f"Failed to initialize BIDSLayout for '{root}'. Error: {e}") from e


def trim_task_derivatives(task: str, dummy_volumes: int, deriv_dir: Path, alt_dir: Path) -> list[str]:
    """Write BOLD and confounds with the first ``dummy_volumes`` removed into ``alt_dir``.

    Returns a list of error messages (empty on success).
    """
    from ..io.bids import get_numvolumes
    from ..io.trim import trim_calibration_volumes, trim_confounds

    errors: list[str] = []
    root = Path(deriv_dir).parent
    print(f"\tGenerating Layout of Derivatives {root}/")
    preproc_layout = _layout(root, derivatives=True)

    task_bold_files = preproc_layout.get(task=task, suffix="bold", extension=".nii.gz")
    task_conf_files = preproc_layout.get(task=task, suffix="timeseries", extension=".tsv")
    if not task_bold_files or not task_conf_files:
        raise ValueError(f"No BOLD and/or confounds files found for task: {task} in {root}")

    for bold_file in task_bold_files:
        print(f"\tBOLD volumes: {get_numvolumes(bold_file.path)} | Adjusting by: {dummy_volumes}.")
        try:
            new_path = alt_path(bold_file.path, deriv_dir, alt_dir)
        except ValueError:
            errors.append(f"BOLD file {bold_file.path} is not under {deriv_dir}; not trimmed")
            continue
        try:
            trimmed_nifti = trim_calibration_volumes(bold_path=bold_file.path, num_voltotrim=dummy_volumes)
            new_path.parent.mkdir(parents=True, exist_ok=True)
            trimmed_nifti.to_filename(new_path)
            print(f"Trimmed BOLD file written to {new_path.name}")

            json_file = Path(bold_file.path.replace(".nii.gz", ".json"))
            if json_file.exists():
                shutil.copy(json_file, new_path.parent / json_file.name)
                print(f"Copied associated JSON file to {json_file.name}")
            else:
                print(f"No associated JSON file found for {bold_file.filename}")
        except Exception as e:
            errors.append(f"Error processing BOLD file {bold_file.filename}: {e}")

    for conf_file in task_conf_files:
        n_rows = len(pd.read_csv(conf_file.path, sep="\t"))
        print(f"\tConfounds rows: {n_rows} | Adjusting by: {dummy_volumes}.")
        try:
            new_path = alt_path(conf_file.path, deriv_dir, alt_dir)
        except ValueError:
            errors.append(f"Confounds file {conf_file.path} is not under {deriv_dir}; not trimmed")
            continue
        try:
            trimmed = trim_confounds(confounds_path=conf_file.path, num_rowstotrim=dummy_volumes)
            new_path.parent.mkdir(parents=True, exist_ok=True)
            trimmed.to_csv(new_path, sep="\t", index=False)
            print(f"Trimmed confounds file {new_path.name}")
        except Exception as e:
            errors.append(f"Error processing confounds file {conf_file.filename}: {e}")

    desc = Path(deriv_dir) / "dataset_description.json"
    if Path(alt_dir).is_dir() and desc.exists():
        shutil.copy(desc, Path(alt_dir) / desc.name)
    return errors


def fix_task_events(study_id: str, task: str, bids_dir: Path, bids_layout=None) -> list[str]:
    """Apply the registered fix to every events file of ``task``. Returns error messages."""
    errors: list[str] = []
    fixer = get_events_fixer(study_id)
    bids_layout = bids_layout or _layout(Path(bids_dir), derivatives=False)
    for f in bids_layout.get(task=task, suffix="events", extension=".tsv"):
        try:
            status = apply_events_fix(fixer, Path(f.path), task, study_id, bids_layout=bids_layout)
            if status == "modified":
                print(f"Modified events file for {Path(f.path).name}")
            else:
                print(f"No changes made to {Path(f.path).name}")
        except Exception as e:
            errors.append(f"Error processing events file {f.filename}: {e!r}")
    return errors


def run_events_step(study_id: str, task: str, basic_details: dict, bids_dir: Path,
                    deriv_dir: Path, alt_dir: Path, check_missing: bool = True) -> int:
    """Run stage 2 for one task. Returns a process exit code (0 = no errors)."""
    taskspecs = (basic_details.get("Tasks") or {}).get(task)
    if taskspecs is None:
        print(f"ERROR: task '{task}' not found in basic-details Tasks: {list(basic_details.get('Tasks', {}))}")
        return 1

    dummy_volumes = int(taskspecs.get("dummy_volumes") or 0)
    preproc_events = taskspecs.get("preproc_events")
    errors: list[str] = []

    if dummy_volumes > 0:
        errors += trim_task_derivatives(task, dummy_volumes, deriv_dir, alt_dir)
    else:
        print(f"Dummy volumes of {dummy_volumes}. Not modifying BOLD or confounds.tsv files.\n")

    bids_layout: Optional[object] = None
    if preproc_events:
        print(f"\tGenerating Layout of BIDS Directory: {bids_dir}/")
        bids_layout = _layout(Path(bids_dir), derivatives=False)
        errors += fix_task_events(study_id, task, bids_dir, bids_layout=bids_layout)
    else:
        print(f"Preprocessing events files is {preproc_events}. Not modifying *_events.tsv files.\n")

    if check_missing:
        from ..qc.file_checks import eval_missing_events

        print("\n\nChecking missing events files across subjects, runs and/or sessions. This will take a moment.")
        # fresh layout: event fixes may have created or renamed files
        eval_missing_events(dir_layout=_layout(Path(bids_dir), derivatives=False), taskname=task)
        print()

    if errors:
        print(f"\n{len(errors)} error(s) during stage 2:")
        for e in errors:
            print(f"  - {e}")
        return 1
    return 0
