import argparse
import os
import json
import numpy as np
from utils import pull_contrast_conditions_spec, get_bidstats_events
import warnings
warnings.filterwarnings("ignore")

## Set up argument parsing
parser = argparse.ArgumentParser(description="Setup OpenNeuro study variables")
parser.add_argument("--openneuro_study", type=str, required=True, help="OpenNeuro study ID")
parser.add_argument("--task", type=str, required=True, help="Task label")
parser.add_argument("--script_dir", type=str, required=True, help="Base directory for scripts")
parser.add_argument("--input_dir", type=str, required=True, help="Directory for BIDS/Events files")

args = parser.parse_args()

# Assign arguments to variables
study_id = args.openneuro_study
task = args.task
scripts = os.path.abspath(args.script_dir)
bids_dir = os.path.abspath(args.input_dir)

# Load the model JSON
sample_specs = os.path.join(scripts, "prep_report_py", "example_mod-specs.json")
spec_out_file = os.path.join(scripts, "..", "statsmodel_specs", study_id, f"{study_id}-{task}_specs.json")
if os.path.exists(spec_out_file):
    with open(spec_out_file, 'r') as specdf:
        model_data = json.load(specdf)

# grab task specific details
with open(os.path.join(scripts, "..", "statsmodel_specs", study_id, f'{study_id}_basic-details.json'), 'r') as file:
    basicdetails_json = json.load(file)

taskspecs = basicdetails_json.get('Tasks').get(task)
brainvols = int(taskspecs.get('bold_volumes'))
gen_tr = 2 # using a generic tr for simple, preliminary check of spec

if not os.path.exists(spec_out_file):
    if os.path.exists(sample_specs):
        print("working on file", sample_specs)
        with open(sample_specs, "r") as file:
            model_data = json.load(file)
    else:
        print("Error: The model JSON file does not exist.", sample_specs)
        exit(1)

    # Load the basic details JSON
    basics_json = os.path.join(scripts, "..", "statsmodel_specs", study_id, f"{study_id}_basic-details.json")
    if os.path.exists(basics_json):
        print("working on file", basics_json)    
        with open(basics_json, "r") as file:
            basics_data = json.load(file)
    else:
        print("Error: The basic details JSON file does not exist.", basics_json)
        exit(1)

    # Load the subjects JSON
    subjects_json = os.path.join(scripts, "..", "statsmodel_specs", study_id, f"{study_id}-{task}_subjects.json")
    if os.path.exists(subjects_json):
        print("working on file", subjects_json)    
        with open(subjects_json, "r") as file:
            subjects_data = json.load(file)
    else:
        print("Error: The subjects JSON file does not exist.", subjects_json)
        exit(1)

    # Load the contrasts JSON
    contrast_json = os.path.join(scripts, "..", "statsmodel_specs", study_id, f"{study_id}-{task}_contrasts.json")
    if os.path.exists(contrast_json):
        print("working on file", contrast_json)
        with open(contrast_json, "r") as file:
            contrast_data = json.load(file)
    else:
        print("Error: The contrasts JSON file does not exist.", contrast_json)
        exit(1)


    # Update the Study Name
    if "Name" in model_data:
        model_data["Name"] = f"{study_id}"

    # Update the Task Values
    if "Input" in model_data:
        model_data["Input"]["task"] = [task]

    # Update the subjects in the model
    if "Input" in model_data:
        model_data["Input"]["subject"] = subjects_data["Subjects"]

    # task runs and sessions
    taskrun_lst = basics_data["Tasks"][task]["task_runs"]
    tasksess_lst = basics_data["Tasks"][task]["task_sessions"]

    # add runs and sessions if greater than 1
    if len(taskrun_lst) > 1:
        model_data["Input"]["run"] = taskrun_lst

    if len(tasksess_lst) > 0:
        model_data["Input"]["session"] = tasksess_lst

    # update the contrasts in the model (for the "Run" level node)
    for node in model_data["Nodes"]:
        if node["Level"] == "Run":
            node["Contrasts"] = contrast_data["Contrasts"]
            break  # Exit loop after updating

    # drop Subject node if runs is less than 2, nothing to average
    # note, since the nodes here are structured in the same way using our sample, to simplify using pop to remove 2nd 'subject' node
    if len(taskrun_lst) < 2:
        print("Subject node is removed as the number of runs is less than 2 (no runs to average). Confirm spec to ensure this behavior is correct")
        model_data['Nodes'].pop(1)


    # append session to GroupBy array instead of replacing it
    if len(tasksess_lst) > 0:
        for node in model_data["Nodes"]:
            if "GroupBy" in node:
                if isinstance(node["GroupBy"], list):
                    if "session" not in node["GroupBy"]:
                        node["GroupBy"].append("session")
                else:
                    print("Session already in node {node}")


    # Save the updated model JSON
    with open(os.path.join(scripts, "..", "statsmodel_specs", study_id, f"{study_id}-{task}_specs.json"), "w") as file:
        json.dump(model_data, file, indent=2)

    print("SUCCESS: Model specs created, updated study name, task, subjects and contrasts.")

else:
    print("Spec file exists, not overwriting. Delete spec file to recreate.\n")


print()
print("Confirming contrast conditions map to available design matrix columns.")
try:
    _, root_mod, _ = get_bidstats_events(bids_dir, model_data, scan_length=brainvols*gen_tr, ignored=[r"sub-.*_physio\.(json|tsv\.gz)"], return_events_num=0)
    outputs = root_mod.run(
        group_by=root_mod.group_by, force_dense=False, transformation_history=True
    )
except TypeError as e:
    if "'<' not supported between instances of 'str' and 'float'" in str(e):
        print("ERROR: Mixed data types found in 'amplitude' column. This suggests that columns being Factored and convolved have a combination of numeric and string.")
        print("Typical cause is are NA values in the columns being factored/convolved, check first.")
    else:
        raise

unique_conditions = pull_contrast_conditions_spec(model_data)

# grab all unique dataframe columns across outputs using specs
unique_conditions = pull_contrast_conditions_spec(model_data)

# each model unique columns
per_model_columns = []
for outmod in outputs:
    df_columns = set(outmod.X.columns)
    per_model_columns.append(df_columns)

# all unique columns across all outputs
all_columns = set().union(*per_model_columns)

#  missing conditions (not present in any models)
missing_conditions = [cond for cond in unique_conditions if cond not in all_columns]
missing_str = ", ".join(missing_conditions) if missing_conditions else "None identified"

# conditions only in a subset of models
subset_conditions = []
for cond in unique_conditions:
    present_in_models = [cond in cols for cols in per_model_columns]
    if any(present_in_models) and not all(present_in_models):
        subset_conditions.append(cond)
subset_str = ", ".join(subset_conditions) if subset_conditions else "None identified"

if missing_conditions:
    print(f"{missing_str} values used in contrast are NOT available in ANY design matrices. Review and update contrasts.\n")
    print(f"All available columns across design matrices:\n{sorted(all_columns)}\n")
else:
    print("** All contrast conditions are present in at least one design matrix. ** \n")

if subset_conditions:
    print(f"{subset_str} conditions does not appear in all subjects' design matrices.\n")
    print(f"Contrasts with these values will be missing for subjects and cannot be estimated\n")

else:
    print("Conditions used in contrasts specification exist in all design matrices.\n")
