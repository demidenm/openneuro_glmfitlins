import json
import shutil
import fnmatch 
import argparse
import subprocess
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from bids.layout import BIDSLayout
from create_readme import generate_groupmodsummary
from utils import get_numvolumes, extract_model_info, gen_vifdf, calc_niftis_meanstd, similarity_boldstand_metrics, get_low_quality_subs
from nilearn.plotting import plot_stat_map
from nilearn.image import load_img, concat_imgs, mean_img, new_img_like
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from templateflow import api


# Turn off back end display to create plots
plt.switch_backend('Agg')

# Set up argument parsing
parser = argparse.ArgumentParser(description="Provide OpenNeuro study variables")
parser.add_argument("--openneuro_study", type=str, help="OpenNeuro study ID", required=True)
parser.add_argument("--taskname", type=str, help="Task name using in analyses", required=True)
parser.add_argument("--spec_dir", type=str, help="Directory where model specs are", required=True)
parser.add_argument("--analysis_dir", type=str, help="Root directory for fitlins output", required=True)
parser.add_argument("--scratch_dir", type=str, help="Scratch directory for intermediate outputs", required=True)
parser.add_argument('--tasksuffix', default=None, help='Optional suffix for group report output')

args = parser.parse_args()

# Set variables from arguments - convert to Path objects
study_id = args.openneuro_study
analysis_dir = Path(args.analysis_dir)
scratch_dir = Path(args.scratch_dir)
spec_path = Path(args.spec_dir)
task = args.taskname
tasksuffix = args.tasksuffix  

# Define nuisance regressor patterns
noise_reg = [
    "motion_", "c_comp_", "a_comp_", "w_comp_", "t_comp_",
    "global_signal", "csf", "white_matter",
    "rot_", "trans_", "cosine", "drift_"
]

# maps z threshold
zstat_thresh = 2.3

# Create output directory for images
if tasksuffix:
    spec_imgs_dir = spec_path / study_id / f"group_{task}{tasksuffix}" / "files"
    spec_imgs_dir.mkdir(parents=True, exist_ok=True)
else:
    spec_imgs_dir = spec_path / study_id / f"group_{task}" / "files"
    spec_imgs_dir.mkdir(parents=True, exist_ok=True)

# Get plotting coordinates from study details
study_details = spec_path / study_id / f"{study_id}_basic-details.json"
with open(study_details, 'r') as file:
    study_info = json.load(file)
    plt_coords = tuple(study_info.get("Tasks", {}).get(task, {}).get("plot_coords"))
    cite_list = tuple(study_info.get("Tasks", {}).get(task, {}).get("cite_links"))

# Load model specifications & study details
try:
    spec_file = spec_path / study_id / f"{study_id}-{task}_specs.json"
    with open(spec_file, 'r') as file:
        spec_data = json.load(file)
    
    spec_results = extract_model_info(model_spec=spec_data)
except Exception as e:
    print(f"Failed to load or process spec file: {e}")
    exit(1)

# Check whether run and subject nodes exist 
# (determines if subject-level and fixed effect models are computed)
has_run = False
has_subject = False
for node in spec_results['nodes']:
    if node['level'] == 'Run':
        has_run = True
    elif node['level'] == 'Subject':
        has_subject = True

# Extract study information
num_subjects = len(spec_results['subjects'])
hrf_model_type = spec_results['nodes'][0]['convolve_model']
derivative_added = spec_results['nodes'][0]['if_derivative_hrf']
dispersion_added = spec_results['nodes'][0]['if_dispersion_hrf']
convolved_inputs = spec_results['nodes'][0]['convolve_inputs']
target_vars = spec_results['nodes'][0]['target_var']

# HRF model description based on convolution, derivative and dispersion terms
hrf_components = []
if derivative_added:
    hrf_components.append("derivatives")
if dispersion_added:
    hrf_components.append("dispersion")

if hrf_components:
    hrf_model = f"{hrf_model_type} w/ {' & '.join(hrf_components)}"
else:
    hrf_model = hrf_model_type

# COPY CONTRAST AND DESIGN 
# Find and copy example contrast image & design matrix
contrast_images = list(analysis_dir.rglob(f"*_task-{task}_*contrasts.svg"))
if contrast_images:
    print(f"Found example contrasts image: {contrast_images[0].name}")
    con_matrix_copy = spec_imgs_dir / f"{study_id}_task-{task}_contrast-matrix.svg"
    shutil.copy(contrast_images[0], con_matrix_copy)

design_images = list(analysis_dir.rglob(f"*_task-{task}_*design.svg"))
if design_images:
    print(f"Found example design mat image: {design_images[0].name}")
    design_matrix_copy = spec_imgs_dir / f"{study_id}_task-{task}_design-matrix.svg"
    shutil.copy(design_images[0], design_matrix_copy)

# Find design matrices
design_matrices = list(analysis_dir.rglob(f"*_task-{task}_*design.tsv"))
if design_matrices:
    print(f"Found design matrix TSV file: {design_matrices[0].name}")
    design_tsv_copy = spec_imgs_dir / f"{study_id}_task-{task}_design-matrix.tsv"
    shutil.copy(design_matrices[0], design_tsv_copy)

# VIF ESTIMATION
# Get contrast spec from nodes for VIF est
contrast_dict = {}
for node in spec_results['nodes']:
    if 'contrasts' in node:
        for contrast in node['contrasts']:
            name = contrast['name']
            conditions = contrast['conditions']
            weights = contrast['weights']
            
            # weights and conditions as expression
            weighted_conditions = [f"{weight}*`{condition}`" for weight, condition in zip(weights, conditions)]
            contrast_expr = " + ".join(weighted_conditions).replace(" + -", " - ")
            
            # as a string, not in a list
            contrast_dict[name] = contrast_expr

# Calculate VIF for each design matrix
all_vif_dfs = []
signal_regressors = []
noise_regressors = []

for design_mat_path in design_matrices:
    try:
        design_matrix = pd.read_csv(design_mat_path, sep='\t')
        noise_regressors = [col for col in design_matrix.columns if any(noise in col for noise in noise_reg)]
        signal_regressors = [col for col in design_matrix.columns if not any(noise in col for noise in noise_reg)]
        
        _,_, vif_df = gen_vifdf(
            designmat=design_matrix,
            contrastdict=contrast_dict,  
            nuisance_regressors=noise_regressors,
        )

        # Add source identifier
        vif_df["design_matrix"] = design_mat_path.name
        all_vif_dfs.append(vif_df)
    except Exception as e:
        print(f"Error processing {design_mat_path.name}: {e}")

# subset signal_regressors with those used in convolve as inputs & if not convolved/intercept, parametric modulators
parametricmodulator_names = []
convolved_names = []

for pattern in convolved_inputs:
    matches = fnmatch.filter(signal_regressors, pattern)
    convolved_names.extend(matches)

parametricmodulator_names = [
    name for name in signal_regressors 
    if name not in ("intercept", "constant") 
    and "trial_type" not in str(name).lower()
    and name not in target_vars
]

# Create VIF visualization if data is available
if all_vif_dfs:
    combined_vif_df = pd.concat(all_vif_dfs, ignore_index=True)
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="name", y="value", hue="type", data=combined_vif_df)
    plt.title("VIF for Regressors & Contrasts")
    plt.xlabel("Type")
    plt.ylabel("VIF")
    plt.xticks(rotation=90, ha="right")
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(spec_imgs_dir / f"{study_id}_task-{task}_vif-boxplot.png", dpi=300)
    plt.close()
else:
    print("No VIF data available for visualization")

# R-SQUARED MAPS
# Estimate average and variance of r-square maps
rquare_statmaps = list(analysis_dir.rglob(f"*_task-{task}*_stat-rSquare_statmap.nii.gz"))
r2mean, r2std = calc_niftis_meanstd(path_imgs=rquare_statmaps)

# Plot r-square mean and std maps if available
if r2mean:
    r2mean_path = spec_imgs_dir / f"{study_id}_task-{task}_rsquare-mean.png"
    plot_stat_map(
        stat_map_img=r2mean,
        cut_coords=plt_coords, 
        cmap="Reds",
        vmin=0,
        vmax=1,
        display_mode='ortho', 
        colorbar=True,  
        output_file=str(r2mean_path),
        title=f"R2 mean across {len(rquare_statmaps)} Subject/Run Imgs"
    )
if r2std:
    r2std_path = spec_imgs_dir / f"{study_id}_task-{task}_rsquare-std.png"
    plot_stat_map(
        stat_map_img=r2std,
        cut_coords=plt_coords, 
        cmap="Reds",
        vmin=0,
        vmax=1,
        display_mode='ortho', 
        colorbar=True, 
        output_file=str(r2std_path),
        title=f"R2 stdev across {len(rquare_statmaps)} Subject/Run Imgs"
    )

# Prepare r-squared maps for similarity analysis
tmp_r2_dir = scratch_dir / f"{study_id}_task-{task}" / "r2tmp"
tmp_r2_dir.mkdir(parents=True, exist_ok=True)

# Squeeze r-squared values to compute the similarity / vox out-in
try: 
    for file in rquare_statmaps:
        img1 = load_img(file)
        data1 = img1.get_fdata()

        if data1.ndim == 4 and data1.shape[3] == 1:
            # Squeeze the 4th dimension
            squeezed_data = data1.squeeze()
            img1_squeezed = new_img_like(img1, squeezed_data)

            # Save to tmp directory
            squeezed_path = tmp_r2_dir / file.name
            img1_squeezed.to_filename(str(squeezed_path))
except Exception as e:
    print(f"Error during squeeze and save: {e}")

# Get or create MNI template mask
mni_mask_dir = tmp_r2_dir / "mask"
mni_mask_dir.mkdir(parents=True, exist_ok=True)
mni_tmp_img = mni_mask_dir / "MNI152NLin2009cAsym_desc-brain_mask.nii.gz"

if not mni_tmp_img.exists():
    template_mni = api.get(
        'MNI152NLin2009cAsym',
        desc='brain',
        resolution=2,
        suffix='mask',
        extension='nii.gz'
    )
    shutil.copy(template_mni, mni_tmp_img)
    print(f"MNI Brain mask saved to: {mni_tmp_img}")
else:
    print("MNI brain mask already exists")

# Calculate similarity metrics
r2_success = False
low_quality = None
try:
    tmp_r2_paths = list(tmp_r2_dir.rglob(f"*_task-{task}*_stat-rSquare_statmap.nii.gz"))
    import os  # Keep for cpu_count
    num_cpus = os.cpu_count()
    use_workers = max(1, num_cpus - 2)  # Use all but 2 cores

    partial_func = partial(similarity_boldstand_metrics, brainmask_path=str(mni_tmp_img))
    with ProcessPoolExecutor(max_workers=use_workers) as executor:
        ratio_results = list(executor.map(partial_func, tmp_r2_paths))

    ratio_df = pd.DataFrame(ratio_results)
    low_quality = get_low_quality_subs(ratio_df=ratio_df, dice_thresh=0.80, voxout_thresh=0.10)
    r2_success = True

except Exception as e:
    print(f"R-square similarity calculation error: {e}")

# Generate similarity plots if successful
if r2_success:
    # Save similarity results
    ratio_df.to_csv(spec_imgs_dir / f"{study_id}_task-{task}_hist-dicesimilarity.tsv", sep='\t', index=False)

    # Plot 1: Dice similarity
    plt.figure(figsize=(8, 5))
    plt.hist(ratio_df['dice'], bins=20, edgecolor='black', alpha=0.7)
    plt.title("Dice Similarity (R2 map ~ MNI)")
    plt.xlabel("Dice Est")
    plt.ylabel("Freq")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(spec_imgs_dir / f"{study_id}_task-{task}_hist-dicesimilarity.png")
    plt.close()

    # Plot 2: Voxels Outside of MNI Mask
    plt.figure(figsize=(8, 5))
    plt.hist(ratio_df['voxoutmask'], bins=20, edgecolor='black', alpha=0.7)
    plt.title("Proportion of Voxels Outside of MNI Mask")
    plt.xlabel("Percentage Out")
    plt.ylabel("Freq")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(spec_imgs_dir / f"{study_id}_task-{task}_hist-voxoutmask.png")
    plt.close()

# GROUP MAP PLOTS
# Plot group maps if they exist; sometimes fitlins create dataLevel and other times datasetLevel
data_level_path = analysis_dir / "node-dataLevel"
dataset_level_path = analysis_dir / "node-datasetLevel"

if data_level_path.exists():
    grp_map_path = data_level_path
    print(f"Setting group map path to: {grp_map_path}")
elif dataset_level_path.exists():
    grp_map_path = dataset_level_path
    print(f"Setting group map path to: {grp_map_path}")
else:
    grp_map_path = None 
    
sessionlabs = None

if grp_map_path and grp_map_path.exists():
    # Create group maps and save them for each contrast
    for con_name in contrast_dict.keys():
        # First, try to find maps directly in the node-dataLevel folder
        direct_zstat_paths = list(grp_map_path.glob(f"*contrast-{con_name}_stat-z_statmap.nii.gz"))
        
        if direct_zstat_paths:
            print(f"No session folders, grabbing {con_name} group map from node-dataLevel directly.\n")
            # Handle maps found directly in node-dataLevel
            output_img_path = spec_imgs_dir / f"{study_id}_task-{task}_contrast-{con_name}_map.png"
            plot_stat_map(
                stat_map_img=direct_zstat_paths[0],
                cut_coords=plt_coords, 
                display_mode='ortho', 
                colorbar=True, 
                threshold=zstat_thresh, 
                output_file=str(output_img_path),
                title=f"{con_name}: z-stat map"
            )
        else:
            # Look for session folders (ses-*)
            session_folders = [f for f in grp_map_path.iterdir() 
                             if f.is_dir() and f.name.startswith('ses-')]
            sessionlabs = [session.name for session in session_folders]

            # For each session folder, find and plot maps
            for session_folder in session_folders:
                print(f"Session folders existing, grabbing {con_name} group map from node-dataLevel {session_folder.name} sub-directory.\n")
                
                # Search for contrast maps in each session folder
                session_maps = list(session_folder.glob(f"*contrast-{con_name}_stat-z_statmap.nii.gz"))
                
                if session_maps:
                    # Include session in filename and title
                    output_img_path = spec_imgs_dir / f"{study_id}_task-{task}_{session_folder.name}_contrast-{con_name}_map.png"
                    plot_stat_map(
                        stat_map_img=session_maps[0],
                        cut_coords=plt_coords, 
                        display_mode='ortho', 
                        colorbar=True, 
                        threshold=zstat_thresh, 
                        output_file=str(output_img_path),
                        title=f"{session_folder.name}, {con_name}: z-stat map"
                    )
            
            # if no maps found
            if not direct_zstat_paths and not any(list(session_folder.glob(f"*contrast-{con_name}_stat-z_statmap.nii.gz")) for session_folder in session_folders):
                print(f"No z-stat map found for contrast: {con_name}")
else:
    print("Group map path not found.")

# Get file count and folder size
gb_size = subprocess.check_output(['du', '-sh', str(analysis_dir)]).split()[0].decode()
file_count = subprocess.check_output(f"find {analysis_dir} -type f -o -type l | wc -l", shell=True).strip().decode()

fold_info = f"The size of the Fitlins Derivatives for {study_id} {task} is {gb_size} with {file_count} files."

# GENERATE AND SAVE README
contrast_image = contrast_images[0] if contrast_images else None
grp_readme = generate_groupmodsummary(
    study_id=study_id, 
    task=task, 
    deriv_size=fold_info,
    num_subjects=num_subjects, 
    hrf_model_type=hrf_model, 
    signal_regressors=signal_regressors, 
    noise_regressors=noise_regressors, 
    convolved_regressors=convolved_names,
    paramod_regressors=parametricmodulator_names,
    has_run=has_run, 
    has_subject=has_subject, 
    contrast_dict=contrast_dict, 
    contrast_image=con_matrix_copy.name if contrast_image else None, 
    design_image=design_matrix_copy.name if design_images else None, 
    spec_imgs_dir=spec_imgs_dir,
    r2_quality_ran=r2_success,
    sub_flag=low_quality,
    sessions=sessionlabs,
    task_cites=cite_list
)

if tasksuffix:
    readme_path = spec_path / study_id / f"group_{task}{tasksuffix}" / "README.md"
else:
    readme_path = spec_path / study_id / f"group_{task}" / "README.md"


with open(readme_path, "w") as f:
    f.write(grp_readme)