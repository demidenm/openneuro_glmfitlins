import json
import os
import argparse
import pandas as pd
import numpy as np
from bids.layout import BIDSLayout
from create_readme import generate_studysummary
from utils import get_numvolumes, create_subjects_json, create_gencontrast_json


# Set up argument parsing
parser = argparse.ArgumentParser(description="Setup OpenNeuro study variables")
parser.add_argument("--openneuro_study", type=str, help="OpenNeuro study ID", required=True)
parser.add_argument("--bids_dir", type=str, help="Base BIDS Directory", required=True)
parser.add_argument("--fmriprep_dir", type=str, help="Base fMRIPrep derivatives directory if different from bids_dir", required=False)
parser.add_argument("--spec_dir", type=str, help="Directory where model specs are", required=True)
parser.add_argument("--minimal_fp", type=str, help="Are outputs minimal yes/no", required=True)


args = parser.parse_args()

# set variables
study_id = args.openneuro_study
bids_path = args.bids_dir
fmriprep_path = args.fmriprep_dir
spec_path = args.spec_dir
minimal_deriv = args.minimal_fp


# get layouts
bids_layout = BIDSLayout(bids_path)
if minimal_deriv == "yes":
    preproc_layout = BIDSLayout(fmriprep_path, derivatives=False)
else:
    preproc_layout = BIDSLayout(fmriprep_path, derivatives=True)

# BIDS input basics
bids_sub_n = bids_layout.get_subjects()
bids_run_n = bids_layout.get_runs()
bids_tasks = bids_layout.get_tasks()
bids_runs_array = [run for run in bids_run_n]

# Check for sessions
bids_sessions = bids_layout.get_sessions()

# fmriprep basics
preproc_sub_n = preproc_layout.get_subjects()
preproc_run_n = preproc_layout.get_runs()
preproc_tasks = preproc_layout.get_tasks()
preproc_runs_array = [run for run in preproc_run_n]

Subjects = bids_sub_n
Tasks = bids_tasks
Sessions = bids_sessions

# print to terminal subject details
print()
print(f"{study_id} Details for BIDS Input versus fMRIPrep")
print("============ Subjects ============")
print(f"Number of Subjects in BIDS Input: {len(bids_sub_n)}")
print(f"Number of Subjects in fMRIPrep: {len(preproc_sub_n)}")
print()

# Print sessions if more than one
if len(Sessions) > 1:
    print("============ Sessions ============")
    print(f"Sessions in BIDS Input: {Sessions}")
    print()

print("============ Tasks ============")
print(f"Tasks in BIDS Input: {bids_tasks}")
print(f"Tasks in fMRIPrep: {preproc_tasks}")
print()

# create dictionary to store study and task details
data = {
    "Subjects": Subjects,
    "Sessions": Sessions if len(Sessions) > 1 else [],
    "Tasks": {}
}

# get column names, data types, and trial_type values for each task
for task_name in Tasks:
    if task_name in ['rest', 'resting', 'REST', 'RESTING']:
        print(f"* Task name {task_name} is resting state sequence, not true task. Skipping. *")
        continue

    task_runs = bids_layout.get_runs(task=task_name)
    task_sessions = bids_layout.get_sessions(task=task_name)
    # Handle sessions if present    
    if Sessions and len(Sessions) > 1:
        task_event_files = []
        task_bold_files = []
        
        for session in Sessions:
            # pull event files that match the task and session
            session_event_files = bids_layout.get(task=task_name, session=session, suffix="events", extension=".tsv")
            task_event_files.extend(session_event_files)
            
            # pull bold files that match the task and session
            session_bold_files = bids_layout.get(task=task_name, session=session, suffix="bold", extension=".nii.gz")
            task_bold_files.extend(session_bold_files)

        # If no event files found in session-specific locations, look at the root
        if not task_event_files:
            root_event_files = bids_layout.get(task=task_name, suffix="events", extension=".tsv", session=None)
            task_event_files.extend(root_event_files)
            
    else:
        # If no sessions or only one session
        task_event_files = bids_layout.get(task=task_name, suffix="events", extension=".tsv")
        task_bold_files = bids_layout.get(task=task_name, suffix="bold", extension=".nii.gz")

    # Get number of volumes for the first bold file
    num_volumes = get_numvolumes(task_bold_files[0].path) if task_bold_files else None

    # if BIDS Input is cloned, no BOLD information. Try fMRIPrep'd BOLD to obtain volumes.
    if num_volumes is None:
        deriv_bold_files = preproc_layout.get(task=task_name, suffix="bold", extension=".nii.gz")
        num_volumes = get_numvolumes(deriv_bold_files[0].path) if deriv_bold_files else None

    if not task_event_files:
        print()
        print(f"\033[91mNo event files found for task: {task_name}\033[0m")

    else:
        # Concatenate ALL event files from ALL runs & sessions
        group_df = pd.concat([pd.read_csv(file, sep='\t') for file in task_event_files], ignore_index=True)

        # Obtain column names and data types, get unique values for trial_type (not important across all runs, as some tasks have behavioral diff modify trial_type)
        column_names = list(group_df.columns)
        column_data_types = {col: str(dtype) for col, dtype in zip(group_df.columns, group_df.dtypes)}
        trial_type_values = group_df['trial_type'].unique().tolist() if 'trial_type' in group_df.columns else []

        # Task-specific data dictionary update
        data["Tasks"][task_name] = {
            "plot_coords": [0,0,0],
            "bold_volumes": num_volumes,
            "dummy_volumes": None,
            "preproc_events": False,
            "task_runs": task_runs,
            "task_sessions": task_sessions,
            "column_names": column_names,
            "column_data_types": column_data_types,
            "trial_type_values": trial_type_values
        }

        # Print results
        print(f"\033[92mTask: {task_name}\033[0m")
        print(f"BOLD Volumes: {num_volumes}")
        print(f"Number of event files: {len(task_event_files)}")
        print(f"Column names: {column_names}")
        print(f"Column data types: {column_data_types}")
        print(f"Unique 'trial_type' values: {trial_type_values}")
        print()

        subjects_file = os.path.join(spec_path, f'{study_id}-{task_name}_subjects.json')
        contrasts_file = os.path.join(spec_path, f'{study_id}-{task_name}_contrasts.json')
        
        if not os.path.exists(subjects_file):
            create_subjects_json(subj_list=Subjects, studyid=study_id, taskname=task_name, specpath=spec_path)
        else:
            print(f"Subjects file already exist: {subjects_file}. Delete and rerun to recreate.")

        # Create contrasts file if it doesn't exist
        if not os.path.exists(contrasts_file):
            create_gencontrast_json(studyid=study_id, taskname=task_name, specpath=spec_path)
        else:
            print(f"Contrasts file already exist: {contrasts_file}. Delete and rerun to recreate./n")


# save study and task details to json
detail_json = os.path.join(spec_path, f'{study_id}_basic-details.json')
if not os.path.exists(detail_json):
    with open(detail_json, 'w') as f:
        json.dump(data, f, indent=4)
else:
    print(f"Basic details file already exist: {contrasts_file}. Delete and rerun to recreate./n")


# generate README.md file
generate_studysummary(spec_path, study_id, data)
