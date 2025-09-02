import argparse
import os
import sys
import inspect
import shutil
import json
import importlib
import modify_events
import pandas as pd
import numpy as np
from pathlib import Path
from utils import get_numvolumes, trim_derivatives, trim_calibration_volumes, trim_confounds, eval_missing_events
from bids.layout import BIDSLayout


## Set up argument parsing
parser = argparse.ArgumentParser(description="Setup OpenNeuro study variables")
parser.add_argument("--openneuro_study", type=str, required=True, help="OpenNeuro study ID")
parser.add_argument("--task", type=str, required=True, help="Task label")
parser.add_argument("--deriv_dir", type=str, required=True, help="fMRIprep Derivatives Folder")
parser.add_argument("--bids_dir", type=str, required=True, help="BIDS Directory Containing Events .tsv files")
parser.add_argument("--specs_dir", type=str, required=True, help="stat model specs containing study details")
args = parser.parse_args()

study_id = args.openneuro_study
taskname = args.task
fmriprep_path = args.deriv_dir
eventspath = args.bids_dir
spec_path = args.specs_dir

# grab task specific specs
with open(f'{spec_path}/{study_id}_basic-details.json', 'r') as file:
    specdata = json.load(file)

taskspecs = specdata.get('Tasks').get(taskname)
dummyvolumes = taskspecs.get('dummy_volumes')
dummyvolumes = int(dummyvolumes) if dummyvolumes is not None else 0  # Default to 0 if None
preproc_events = taskspecs.get('preproc_events')

if dummyvolumes > 0:
    print(f"\tGenerating Layout of Derivatives {fmriprep_path}/../")
    try:
        preproc_layout = BIDSLayout(f"{fmriprep_path}/..", derivatives=True)
    except FileNotFoundError:
        sys.exit(f" Path '{fmriprep_path}/..' not found or missing dataset_description.json. "
                "Please check that the directory exists and is a valid BIDS derivatives folder.")
    except Exception as e:
        sys.exit(f" Failed to initialize BIDSLayout for '{fmriprep_path}/..'. Error: {e}")    
    
    task_bold_files = preproc_layout.get(task=taskname, suffix="bold", extension=".nii.gz")
    task_conf_files = preproc_layout.get(task=taskname, suffix="timeseries", extension=".tsv")

    if not task_bold_files or not task_conf_files:
        ValueError(f"No files found for task: {taskname}")

    # iterate over bold files
    for bold_file in task_bold_files:
        bold_volcheck = get_numvolumes(bold_file.path)
        
        print(f"\tBOLD volumes: {bold_volcheck} | Adjusting by: {dummyvolumes}.")
        
        try:
            trimmed_nifti = trim_calibration_volumes(
                bold_path=bold_file.path, 
                num_voltotrim=dummyvolumes
            )
            og_path = Path(bold_file.path)
            new_path = Path(str(og_path).replace("derivatives", "derivatives_alt"))
            new_path.parent.mkdir(parents=True, exist_ok=True) 
            trimmed_nifti.to_filename(new_path)
            print(f"Trimmed BOLD file overwritten for {new_path.name}")

            # cp associated .json file to new derivatives folder
            json_file = Path(str(og_path).replace(".nii.gz", ".json")) 
            if json_file.exists():
                new_json_path = new_path.parent / json_file.name 
                shutil.copy(json_file, new_json_path)  # Copy the JSON file
                print(f"Copied associated JSON file to {new_json_path.name}")
            else:
                print(f"No associated JSON file found for {bold_file.filename}")

        except Exception as e:

            print(f"Error processing BOLD file {bold_file.filename}: {e}")

    # iterate over confound files -- trim confounds .tsv files to match BOLD length
    for conf_file in task_conf_files:
        conf_df = pd.read_csv(conf_file.path, sep='\t')
        conf_volcheck = len(conf_df) 
        
        print(f"\tConfounds rows: {conf_volcheck} | Adjusting by: {dummyvolumes}.")
        
        try:
            trimmed_confounds = trim_confounds(
                confounds_path=conf_file.path, 
                num_rowstotrim=dummyvolumes
            )
            ogcf_path = Path(conf_file.path)
            newcf_path = Path(str(ogcf_path).replace("derivatives", "derivatives_alt"))
            newcf_path.parent.mkdir(parents=True, exist_ok=True) 
            trimmed_confounds.to_csv(newcf_path, sep='\t', index=False)
            print(f"Trimmed confounds file {newcf_path.name}")
        except Exception as e:
            print(f"Error processing confounds file {conf_file.filename}: {e}")

else:
    print(f"Dummy volumes of {dummyvolumes}. Not modifying BOLD or confounds.tsv files.\n")


if preproc_events:
    print(f"\tGenerating Layout of BIDS Directory: {eventspath}/")
    try:
        bids_layout = BIDSLayout(eventspath, derivatives=False)
    except FileNotFoundError:
        sys.exit(f" Path '{eventspath}/..' not found or missing dataset_description.json. "
                "Please check that the directory exists and is a valid BIDS derivatives folder.")
    except Exception as e:
        sys.exit(f" Failed to initialize BIDSLayout for '{eventspath}/..'. Error: {e}")    


    task_event_files = bids_layout.get(task=taskname, suffix="events", extension=".tsv")

    if hasattr(modify_events, study_id):
        # grab function specific to study
        refactor_events = getattr(modify_events, study_id)  
    else:
        raise ValueError(f"Function {study_id} not found in mod_events.py. Cannot modify events data for {taskname}")

    for eventtsv_path in task_event_files:
        try:
            # if refactor_events accepts bids_layout (helpful in messy cases to recreate events in fly)
            sig = inspect.signature(refactor_events)
            if 'bids_layout' in sig.parameters:
                events_data = refactor_events(eventspath=eventtsv_path.path, task=taskname, bids_layout=bids_layout)
            else:
                events_data = refactor_events(eventspath=eventtsv_path.path, task=taskname)     


            if events_data is not None:           
                # save the modified events file to the *resolved* path
                events_data.to_csv(eventtsv_path.path, sep='\t', index=False)
                print(f"Modified events file for {os.path.basename(eventtsv_path.path)}")
            else:
                print(f"No changes made to {os.path.basename(eventtsv_path.path)}")

        except Exception as e:
            print(f"Error processing events file {eventtsv_path.filename}: {e}")
else:
    print(f"Preprocessing events files is {preproc_events}. Not modifying *_events.tsv files.\n")



# check subjects events files
print("\n\nChecking missing events files across subjects, runs and/or sessions. This will take a moment.")
inpdir_layout = BIDSLayout(eventspath, derivatives=False)

_ = eval_missing_events(dir_layout=inpdir_layout, taskname=taskname)
print()
