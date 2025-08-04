import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from bids.layout import BIDSLayout
from create_readme import generate_studysummary
from utils import get_numvolumes, create_subjects_json, create_gencontrast_json, create_task_plots, get_session_metadata


# Set up argument parsing
parser = argparse.ArgumentParser(description="Setup OpenNeuro study variables")
parser.add_argument("--openneuro_study", type=str, required=True, help="OpenNeuro study ID")
parser.add_argument("--bids_dir", type=str, required=True, help="Base BIDS Directory")
parser.add_argument("--fmriprep_dir", type=str, required=False, help="Base fMRIPrep derivatives directory if different from bids_dir")
parser.add_argument("--spec_dir", type=str, required=True, help="Directory where model specs are")
parser.add_argument("--minimal_fp", type=str, required=True, help="Are outputs minimal yes/no")
args = parser.parse_args()

# Convert paths to Path objects
bids_path = Path(args.bids_dir).resolve()
fmriprep_path = Path(args.fmriprep_dir).resolve() if args.fmriprep_dir else bids_path
spec_path = Path(args.spec_dir).resolve()
minimal_deriv = args.minimal_fp
study_id = args.openneuro_study

# Get layouts
bids_layout = BIDSLayout(bids_path)
preproc_layout = BIDSLayout(fmriprep_path, derivatives=(minimal_deriv.lower() != "yes"))

# Extract info from BIDS and fMRIPrep
bids_sub_n = bids_layout.get_subjects()
bids_run_n = bids_layout.get_runs()
bids_tasks = bids_layout.get_tasks()
bids_runs_array = [run for run in bids_run_n]
bids_sessions = bids_layout.get_sessions()

preproc_sub_n = preproc_layout.get_subjects()
preproc_run_n = preproc_layout.get_runs()
preproc_tasks = preproc_layout.get_tasks()
preproc_runs_array = [run for run in preproc_run_n]

Subjects = bids_sub_n
Tasks = bids_tasks
Sessions = bids_sessions

print(f"\n{study_id} Details for BIDS Input versus fMRIPrep")
print("============ Subjects ============")
print(f"Number of Subjects in BIDS Input: {len(bids_sub_n)}")
print(f"Number of Subjects in fMRIPrep: {len(preproc_sub_n)}\n")

if len(Sessions) > 1:
    print("============ Sessions ============")
    print(f"Sessions in BIDS Input: {Sessions}\n")

print("============ Tasks ============")
print(f"Tasks in BIDS Input: {bids_tasks}")
print(f"Tasks in fMRIPrep: {preproc_tasks}\n")

data = {
    "Subjects": Subjects,
    "Sessions": Sessions if len(Sessions) > 1 else [],
    "Tasks": {}
}

for task_name in Tasks:
    task_metadata = get_session_metadata(task_name, bids_layout, Sessions=Sessions, preproc_layout=preproc_layout)
    if task_metadata is None:
        continue

    task_event_files = task_metadata["task_event_files"]
    task_bold_files = task_metadata["task_bold_files"]
    num_volumes = task_metadata["num_volumes"]
    subject_data_by_session = task_metadata["subject_data_by_session"]

    task_runs = bids_layout.get_runs(task=task_name)
    task_sessions = bids_layout.get_sessions(task=task_name)

    if not task_event_files:
        print(f"\033[91mNo event files found for task: {task_name}\033[0m")
        continue

    # extract trial/event info
    group_df = pd.concat([pd.read_csv(f.path, sep='\t') for f in task_event_files], ignore_index=True)
    column_names = list(group_df.columns)
    column_data_types = {col: str(dtype) for col, dtype in zip(group_df.columns, group_df.dtypes)}
    trial_type_values = group_df['trial_type'].unique().tolist() if 'trial_type' in group_df.columns else []

    # save task metadata
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
        "trial_type_values": trial_type_values
    }

    print(f"\033[92mTask: {task_name}\033[0m")
    print(f"BOLD Volumes: {num_volumes}")
    print(f"Number of event files: {len(task_event_files)}")
    print(f"Column names: {column_names}")
    print(f"Column data types: {column_data_types}")
    print(f"Unique 'trial_type' values: {trial_type_values}")

    # Save subject-session summary CSV
    basics_out_dir = spec_path / 'basics_out'
    basics_out_dir.mkdir(parents=True, exist_ok=True)

    combined_df = pd.concat(
        [
            df if 'Session' in df.columns else df.assign(Session='ses-all')
            for df in subject_data_by_session.values()
        ],
        ignore_index=True
    )
    combined_df.to_csv(basics_out_dir / f'{task_name}_subject_session_run_summary.csv', index=False)

    # Generate plots
    create_task_plots(taskname=task_name, subj_data=subject_data_by_session, sess_list=Sessions, output_dir=basics_out_dir)

    # Summary printout
    total_subjects = sum(len(df) for df in subject_data_by_session.values())
    print(f"Total subjects: {total_subjects}")
    if Sessions and len(Sessions) > 1:
        for session, df in subject_data_by_session.items():
            print(f"  Session {session}: {len(df)} subjects")
        total_runs = sum(df['num_runs'].sum() for df in subject_data_by_session.values() if not df.empty)
        print(f"Summary for {task_name}:\n  - Total subjects across all sessions: {total_subjects}\n  - Total runs: {total_runs}")
    else:
        df = list(subject_data_by_session.values())[0]
        print(f"Summary for {task_name}:\n  - Total subjects: {len(df)}\n  - Total runs: {df['num_runs'].sum()}")


    subjects_file = spec_path / f'{study_id}-{task_name}_subjects.json'
    contrasts_file = spec_path / f'{study_id}-{task_name}_contrasts.json'

    if not subjects_file.exists():
        create_subjects_json(subj_list=Subjects, studyid=study_id, taskname=task_name, specpath=spec_path)
    else:
        print(f"Subjects file already exists: {subjects_file}")

    if not contrasts_file.exists():
        create_gencontrast_json(studyid=study_id, taskname=task_name, specpath=spec_path)
    else:
        print(f"Contrasts file already exists: {contrasts_file}")

# Save study and task details
detail_json = spec_path / f'{study_id}_basic-details.json'
if not detail_json.exists():
    with open(detail_json, 'w') as f:
        json.dump(data, f, indent=4)
else:
    print(f"Basic details file already exists: {detail_json}")

# Generate README
generate_studysummary(spec_path, study_id, data)
