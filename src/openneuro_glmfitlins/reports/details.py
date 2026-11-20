"""Stage 1 study summary: basic-details JSON, starter subjects/contrasts files, count plots, README."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd
from bids.layout import BIDSLayout

from ..io.bids import get_session_metadata
from ..specs.scaffold import create_gencontrast_json, create_subjects_json
from .plots import create_task_plots
from .readme import generate_studysummary


def generate_study_details(study_id: str, bids_dir: Path, fmriprep_dir: Optional[Path], spec_dir: Path,
                           minimal_fp: bool, out_dir: Optional[Path] = None,
                           mriqc_url_path: Optional[str] = None) -> dict:
    """Summarise subjects/sessions/tasks and write the stage-1 files.

    Inputs for later stages (``*_basic-details.json``, ``*_subjects.json``, ``*_contrasts.json``)
    go to ``spec_dir`` and are never overwritten. Generated figures (``basics_out/``) and the
    README go to ``out_dir`` (default: ``spec_dir``).
    """
    bids_path = Path(bids_dir).resolve()
    fmriprep_path = Path(fmriprep_dir).resolve() if fmriprep_dir else bids_path
    spec_path = Path(spec_dir).resolve()
    out_path = Path(out_dir).resolve() if out_dir else spec_path
    spec_path.mkdir(parents=True, exist_ok=True)
    out_path.mkdir(parents=True, exist_ok=True)

    bids_layout = BIDSLayout(bids_path)
    preproc_layout = BIDSLayout(fmriprep_path, derivatives=not minimal_fp)

    bids_sub_n = bids_layout.get_subjects()
    bids_tasks = bids_layout.get_tasks()
    sessions = bids_layout.get_sessions()
    preproc_sub_n = preproc_layout.get_subjects()
    preproc_tasks = preproc_layout.get_tasks()

    print(f"\n{study_id} Details for BIDS Input versus fMRIPrep")
    print("============ Subjects ============")
    print(f"Number of Subjects in BIDS Input: {len(bids_sub_n)}")
    print(f"Number of Subjects in fMRIPrep: {len(preproc_sub_n)}\n")
    if len(sessions) > 1:
        print("============ Sessions ============")
        print(f"Sessions in BIDS Input: {sessions}\n")
    print("============ Tasks ============")
    print(f"Tasks in BIDS Input: {bids_tasks}")
    print(f"Tasks in fMRIPrep: {preproc_tasks}\n")

    data = {
        "Subjects": bids_sub_n,
        "Sessions": sessions if len(sessions) > 1 else [],
        "Tasks": {},
    }

    for task_name in bids_tasks:
        task_metadata = get_session_metadata(task_name, bids_layout, Sessions=sessions, preproc_layout=preproc_layout)
        if task_metadata is None:
            continue

        task_event_files = task_metadata["task_event_files"]
        num_volumes = task_metadata["num_volumes"]
        subject_data_by_session = task_metadata["subject_data_by_session"]
        task_runs = bids_layout.get_runs(task=task_name)
        task_sessions = bids_layout.get_sessions(task=task_name)

        if not task_event_files:
            print(f"\033[91mNo event files found for task: {task_name}\033[0m")
            continue

        group_df = pd.concat([pd.read_csv(f.path, sep="\t") for f in task_event_files], ignore_index=True)
        column_names = list(group_df.columns)
        column_data_types = {col: str(dtype) for col, dtype in zip(group_df.columns, group_df.dtypes)}
        trial_type_values = group_df["trial_type"].unique().tolist() if "trial_type" in group_df.columns else []

        data["Tasks"][task_name] = {
            "cite_links": [],
            "plot_coords": [0, 0, 0],
            "bold_volumes": num_volumes,
            "dummy_volumes": 0,
            "preproc_events": False,
            "task_runs": task_runs,
            "task_sessions": task_sessions,
            "column_names": column_names,
            "column_data_types": column_data_types,
            "trial_type_values": trial_type_values,
        }

        print(f"\033[92mTask: {task_name}\033[0m")
        print(f"BOLD Volumes: {num_volumes}")
        print(f"Number of event files: {len(task_event_files)}")
        print(f"Column names: {column_names}")
        print(f"Column data types: {column_data_types}")
        print(f"Unique 'trial_type' values: {trial_type_values}")

        basics_out_dir = out_path / "basics_out"
        basics_out_dir.mkdir(parents=True, exist_ok=True)
        combined_df = pd.concat(
            [df if "Session" in df.columns else df.assign(Session="ses-all")
             for df in subject_data_by_session.values()],
            ignore_index=True,
        )
        combined_df.to_csv(basics_out_dir / f"{task_name}_subject_session_run_summary.csv", index=False)
        create_task_plots(taskname=task_name, subj_data=subject_data_by_session, sess_list=sessions,
                          output_dir=basics_out_dir)

        total_subjects = sum(len(df) for df in subject_data_by_session.values())
        print(f"Total subjects: {total_subjects}")
        if sessions and len(sessions) > 1:
            for session, df in subject_data_by_session.items():
                print(f"  Session {session}: {len(df)} subjects")
            total_runs = sum(df["num_runs"].sum() for df in subject_data_by_session.values() if not df.empty)
            print(f"Summary for {task_name}:\n  - Total subjects across all sessions: {total_subjects}\n"
                  f"  - Total runs: {total_runs}")
        else:
            df = list(subject_data_by_session.values())[0]
            print(f"Summary for {task_name}:\n  - Total subjects: {len(df)}\n  - Total runs: {df['num_runs'].sum()}")

        subjects_file = spec_path / f"{study_id}-{task_name}_subjects.json"
        contrasts_file = spec_path / f"{study_id}-{task_name}_contrasts.json"
        if not subjects_file.exists():
            create_subjects_json(subj_list=bids_sub_n, studyid=study_id, taskname=task_name, specpath=spec_path)
        else:
            print(f"Subjects file already exists: {subjects_file}")
        if not contrasts_file.exists():
            create_gencontrast_json(studyid=study_id, taskname=task_name, specpath=spec_path)
        else:
            print(f"Contrasts file already exists: {contrasts_file}")

    detail_json = spec_path / f"{study_id}_basic-details.json"
    if not detail_json.exists():
        with open(detail_json, "w") as f:
            json.dump(data, f, indent=4)
    else:
        print(f"Basic details file already exists: {detail_json}")

    generate_studysummary(out_path, study_id, data, mriqc_dir=spec_path / "mriqc_summary",
                          mriqc_url_path=mriqc_url_path)
    return data
