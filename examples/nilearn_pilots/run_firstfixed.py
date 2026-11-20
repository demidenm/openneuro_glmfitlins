import sys
import os
import json
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from model_utils import fixed_effect, group_onesample
import matplotlib.pyplot as plt
from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix
from nilearn.plotting import plot_design_matrix


plt.switch_backend('Agg') # turn off back end display to create plots
parser = argparse.ArgumentParser(description="Process fMRI data using Nilearn")
parser.add_argument("--study", help="openneuro id, e.g ds003425")
parser.add_argument("--sub", help="subject name, sub-XX, include entirety with 'sub-' prefix")
parser.add_argument("--task", help="task type -- e.g., mid, reward, etc")
parser.add_argument("--ses", help="session, include the session type without prefix, e.g., 1, 01, baselinearm1")
parser.add_argument("--smooth", help="fwhm smoothing kernal size (e.g. 5)")
parser.add_argument("--beh_path", help="Path to the behavioral (.tsv) directory/files for the task")
parser.add_argument("--fmriprep_path", help="Path to the output directory for the fmriprep output")
parser.add_argument("--mask", help="path the to a binarized brain mask (e.g., MNI152 or "
                                   "constrained mask in MNI space, spec-network",
                    default=None)
parser.add_argument("--mask_label", help="label for mask, e.g. mni152, yeo-network, etc",
                    default=None)
parser.add_argument("--output", help="output folder where to write out and save information")
args = parser.parse_args()

# Now you can access the arguments as attributes of the 'args' object.
study_id = args.study
subj = args.sub
task = args.task
ses = args.ses
beh_path = args.beh_path
fmriprep_path = args.fmriprep_path
brainmask = args.mask
mask_label = args.mask_label
scratch_out = args.output
fwhm= int(args.smooth)


# Define the path to the JSON file
json_file = Path(__file__).parent / "study_req.json"

# Load JSON data
with open(json_file, "r") as f:
    json_data = json.load(f)

# relevant values based on the task type
study_data = json_data[study_id][task]
con_labs = study_data["con_labs"]
contrasts = set(study_data["contrasts"])  # list to set
trial_type_map = (
    {int(k): v for k, v in study_data["trial_type_map"].items()} 
    if study_data.get("trial_type_map") else None
)

# volume, TR, and runs
numvols = int(study_data["volume"]) # grab numvols
boldtr = float(study_data["tr"]) # grab tr value
runs = study_data["runs"]  # grab run list
slice_time_correct = study_data["slice_time_correct_true"]  # grab slice time correction flag

# first level
firstlvl_out = Path(scratch_out) / subj / f'ses-{ses}'

if not os.path.exists(firstlvl_out):  
    os.makedirs(firstlvl_out)


for run in runs:
    print(f'\tStarting {subj} {run}.')
    # import behavior events .tsv from data path, fix issue with RT column & duration onsettoonset issues
    eventsdat = pd.read_csv(
        Path(beh_path) / subj / f"ses-{ses}" / "func" / f"{subj}_ses-{ses}_task-{task}_run-{run}_events.tsv",
        sep='\t'
        )

    # custom for task 
    subset_df = eventsdat[eventsdat['trial_type'].isin([4, 5])]
    first_last_df = subset_df.iloc[[0, -1]].copy()
    first_last_df['trial_type'] = 6
    events_cpy = pd.concat([eventsdat, first_last_df], ignore_index=True)

    # remap trial_type values if remappping exists
    if trial_type_map:
        events_cpy["trial_type"] = events_cpy["trial_type"].map(trial_type_map)

    # get path to confounds from fmriprep, func data + mask, set image path
    conf_path = Path(fmriprep_path) / subj / f"ses-{ses}" / "func" / f"{subj}_ses-{ses}_task-{task}_run-{run}_desc-confounds_timeseries.tsv"

    conf_df = pd.read_csv(conf_path, sep='\t')
    
    nii_path = next(Path(fmriprep_path).glob(
        f"{subj}/ses-{ses}/func/{subj}_ses-{ses}_task-{task}_run-{run}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    ), None)

    print(f"Nifti image", nii_path)
    print('\t\t 1/3 Create Regressors & Design Matrix for GLM')
    
    # design matrix
    design_events = pd.DataFrame({'trial_type': events_cpy['trial_type'],
                                    'onset': events_cpy['onset'],
                                    'duration': events_cpy['duration']})


    frame_times = np.arange(numvols) * boldtr
    if slice_time_correct:
        frame_times += boldtr / 2

    design_matrix = make_first_level_design_matrix(
            frame_times= frame_times,
            events=design_events,
            hrf_model='spm + derivative',
            drift_model=None,
            add_regs=conf_df.filter(regex="^(cosine|trans|rot)").fillna(0) # first volumes have nans, so need to make them zero to avoid error
            )

    plot_design_matrix(design_matrix)
    plt.savefig(Path(firstlvl_out) / f"{subj}_ses-{ses}_task-{task}_run-{run}_design-mat.png")

    print('\t\t 2/3 Mask Image, Fit GLM model ar1 autocorrelation')
    # using ar1 autocorrelation (FSL prewhitening), drift model
    fmri_glm = FirstLevelModel(subject_label=subj, mask_img=brainmask,
                                t_r=boldtr, smoothing_fwhm=fwhm,
                                standardize=False, noise_model='ar1', drift_model=None, high_pass=None
                                )
    # Run GLM model using set paths and calculate design matrix
    run_fmri_glm = fmri_glm.fit(nii_path, design_matrices=design_matrix)


    for con_name, con in con_labs.items():
        print(f"Working on contrast {con_name} with weight {con}")
        try:
            # Construct file paths using pathlib
            beta_name = Path(firstlvl_out) / f"{subj}_ses-{ses}_task-{task}_run-{run}_contrast-{con_name}_stat-beta.nii.gz"
            beta_est = run_fmri_glm.compute_contrast(con, output_type="effect_size")
            beta_est.to_filename(beta_name)

            # Compute variance
            var_name = Path(firstlvl_out) / f"{subj}_ses-{ses}_task-{task}_run-{run}_contrast-{con_name}_stat-var.nii.gz"
            var_est = run_fmri_glm.compute_contrast(con, output_type="effect_variance")
            var_est.to_filename(var_name)
        except Exception as e:
            print(f"Error processing beta: {e} for {subj} and {con_name}")


print("Running Fixed effect model -- precision weight of runs for each contrast")

fixed_effect(subject=subj, session=ses, task_type=task,
            contrast_list=contrasts, firstlvl_indir=firstlvl_out, fixedeffect_outdir=firstlvl_out,
            save_beta=True, save_var=True, save_tstat=True)

