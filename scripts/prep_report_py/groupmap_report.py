import json
import os
import shutil
import argparse
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

args = parser.parse_args()

# Set variables from arguments
study_id = args.openneuro_study
analysis_dir = args.analysis_dir
scratch_dir = args.scratch_dir
spec_path = args.spec_dir
task = args.taskname

# Define nuisance regressor patterns
noise_reg = [
    "motion_", "c_comp_", "a_comp_", "w_comp_", "t_comp_",
    "global_signal", "csf", "white_matter",
    "rot_", "trans_", "cosine", "drift_"
]

# Create output directory for images
spec_imgs_dir = Path(f"{spec_path}/{study_id}/group_{task}/imgs")
spec_imgs_dir.mkdir(parents=True, exist_ok=True)

# Get plotting coordinates from study details
study_details = f"{spec_path}/{study_id}/{study_id}_basic-details.json"
with open(study_details, 'r') as file:
    study_info = json.load(file)
    plt_coords = tuple(study_info.get("Tasks", {}).get(task, {}).get("plot_coords"))

# Load model specifications & study details
try:
    spec_file = f"{spec_path}/{study_id}/{study_id}-{task}_specs.json"
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
contrast_images = list(Path(analysis_dir).rglob(f"*_task-{task}_*contrasts.svg"))
if contrast_images:
    print(f"Found example contrasts image: {contrast_images[0].name}")
    con_matrix_copy = Path(spec_imgs_dir) / f"{study_id}_task-{task}_contrast-matrix.svg"
    shutil.copy(contrast_images[0], con_matrix_copy)

design_images = list(Path(analysis_dir).rglob(f"*_task-{task}_*design.svg"))
if design_images:
    print(f"Found example design mat image: {design_images[0].name}")
    design_matrix_copy = Path(spec_imgs_dir) / f"{study_id}_task-{task}_design-matrix.svg"
    shutil.copy(design_images[0], design_matrix_copy)

# Find design matrices
design_matrices = list(Path(analysis_dir).rglob(f"*_task-{task}_*design.tsv"))
if design_matrices:
    print(f"Found design matrix TSV file: {design_matrices[0].name}")
    design_tsv_copy = Path(spec_imgs_dir) / f"{study_id}_task-{task}_design-matrix.tsv"
    shutil.copy(design_matrices[0], design_tsv_copy)

# VIF ESTIMATION
# Get contrast spec from notes for VIF est
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
    plt.savefig(f"{spec_imgs_dir}/{study_id}_task-{task}_vif-boxplot.png", dpi=300)
    plt.close()
else:
    print("No VIF data available for visualization")

# R-SQUARED MAPS
# Estimate average and variance of r-square maps
rquare_statmaps = list(Path(analysis_dir).rglob(f"*_task-{task}*_stat-rSquare_statmap.nii.gz"))
r2mean, r2std = calc_niftis_meanstd(path_imgs=rquare_statmaps)

# Plot r-square mean and std maps if available
if r2mean:
    r2mean_path = f"{spec_imgs_dir}/{study_id}_task-{task}_rsquare-mean.png"
    plot_stat_map(
        stat_map_img=r2mean,
        cut_coords=plt_coords, 
        cmap="Reds",
        vmin=0,
        vmax=1,
        display_mode='ortho', 
        colorbar=True,  
        output_file=r2mean_path,
        title=f"R2 mean across {len(rquare_statmaps)} Subject/Run Imgs"
    )
if r2std:
    r2std_path = f"{spec_imgs_dir}/{study_id}_task-{task}_rsquare-std.png"
    plot_stat_map(
        stat_map_img=r2std,
        cut_coords=plt_coords, 
        cmap="Reds",
        vmin=0,
        vmax=1,
        display_mode='ortho', 
        colorbar=True, 
        output_file=r2std_path,
        title=f"R2 stdev across {len(rquare_statmaps)} Subject/Run Imgs"
    )

# Prepare r-squared maps for similarity analysis
tmp_r2_dir = Path(f"{scratch_dir}/{study_id}_task-{task}/r2tmp")
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
            basename = os.path.basename(file)
            squeezed_path = os.path.join(tmp_r2_dir, basename)
            img1_squeezed.to_filename(squeezed_path)
except Exception as e:
    print(f"Error during squeeze and save: {e}")

# Get or create MNI template mask
mni_mask_dir = Path(f"{tmp_r2_dir}/mask")
mni_mask_dir.mkdir(parents=True, exist_ok=True)
mni_tmp_img = f"{mni_mask_dir}/MNI152NLin2009cAsym_desc-brain_mask.nii.gz"

if not os.path.exists(mni_tmp_img):
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
    tmp_r2_paths = list(Path(tmp_r2_dir).rglob(f"*_task-{task}*_stat-rSquare_statmap.nii.gz"))
    num_cpus = os.cpu_count()
    use_workers = max(1, num_cpus - 2)  # Use all but 2 cores

    partial_func = partial(similarity_boldstand_metrics, brainmask_path=mni_tmp_img)
    with ProcessPoolExecutor(max_workers=use_workers) as executor:
        ratio_results = list(executor.map(partial_func, tmp_r2_paths))

    ratio_df = pd.DataFrame(ratio_results)
    low_quality = get_low_quality_subs(ratio_df=ratio_df, dice_thresh=0.85, voxout_thresh=0.10)
    r2_success = True

except Exception as e:
    print(f"R-square similarity calculation error: {e}")

# Generate similarity plots if successful
if r2_success:
    # Save similarity results
    ratio_df.to_csv(os.path.join(spec_imgs_dir, f"{study_id}_task-{task}_hist-dicesimilarity.tsv"), sep='\t', index=False)

    # Plot 1: Dice similarity
    plt.figure(figsize=(8, 5))
    plt.hist(ratio_df['dice'], bins=20, edgecolor='black', alpha=0.7)
    plt.title("Dice Similarity (R2 map ~ MNI)")
    plt.xlabel("Dice Est")
    plt.ylabel("Freq")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(spec_imgs_dir, f"{study_id}_task-{task}_hist-dicesimilarity.png"))
    plt.close()

    # Plot 2: Voxels Outside of MNI Mask
    plt.figure(figsize=(8, 5))
    plt.hist(ratio_df['voxoutmask'], bins=20, edgecolor='black', alpha=0.7)
    plt.title("Proportion of Voxels Outside of MNI Mask")
    plt.xlabel("Percentage Out")
    plt.ylabel("Freq")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(spec_imgs_dir, f"{study_id}_task-{task}_hist-voxoutmask.png"))
    plt.close()

# GROUP MAP PLOTS
# Plot group maps if they exist
grp_map_path = f"{analysis_dir}/node-dataLevel"
sessionlabs = None
if os.path.exists(grp_map_path):

    # Create group maps and save them for each contrast
    for con_name in contrast_dict.keys():
        # First, try to find maps directly in the node-dataLevel folder
        direct_zstat_paths = list(Path(grp_map_path).glob(f"*contrast-{con_name}_stat-z_statmap.nii.gz"))
        
        if direct_zstat_paths:
            # Handle maps found directly in node-dataLevel
            output_img_path = f"{spec_imgs_dir}/{study_id}_task-{task}_contrast-{con_name}_map.png"
            plot_stat_map(
                stat_map_img=direct_zstat_paths[0],
                cut_coords=plt_coords, 
                display_mode='ortho', 
                colorbar=True, 
                threshold=1.5, 
                output_file=output_img_path,
                title=f"{con_name}: z-stat map"
            )
        else:
            # Look for session folders (ses-*)
            session_folders = [f for f in os.listdir(grp_map_path) if f.startswith('ses-') and os.path.isdir(os.path.join(grp_map_path, f))]
            sessionlabs = [session for session in session_folders]

            # For each session folder, find and plot maps
            for session in session_folders:
                
                session_path = os.path.join(grp_map_path, session)
                # Search for contrast maps in each session folder
                session_maps = list(Path(session_path).glob(f"*contrast-{con_name}_stat-z_statmap.nii.gz"))
                
                if session_maps:
                    # Include session in filename and title
                    output_img_path = f"{spec_imgs_dir}/{study_id}_task-{task}_{session}_contrast-{con_name}_map.png"
                    plot_stat_map(
                        stat_map_img=session_maps[0],
                        cut_coords=plt_coords, 
                        display_mode='ortho', 
                        colorbar=True, 
                        threshold=1.5, 
                        output_file=output_img_path,
                        title=f"{session}, {con_name}: z-stat map"
                    )
            
            # if no maps found
            if not direct_zstat_paths and not any(list(Path(os.path.join(grp_map_path, s)).glob(f"*contrast-{con_name}_stat-z_statmap.nii.gz")) for s in session_folders):
                print(f"No z-stat map found for contrast: {con_name}")
else:
    print("Group map path not found.")

# GENERATE AND SAVE README
contrast_image = contrast_images[0] if contrast_images else None
grp_readme = generate_groupmodsummary(
    study_id=study_id, 
    task=task, 
    num_subjects=num_subjects, 
    hrf_model_type=hrf_model, 
    signal_regressors=signal_regressors, 
    noise_regressors=noise_regressors, 
    has_run=has_run, 
    has_subject=has_subject, 
    contrast_dict=contrast_dict, 
    contrast_image=Path(con_matrix_copy).name if contrast_image else None, 
    design_image=Path(design_matrix_copy).name if design_images else None, 
    spec_imgs_dir=spec_imgs_dir,
    r2_quality_ran=r2_success,
    sub_flag=low_quality,
    sessions=sessionlabs
)

readme_path = os.path.join(f"{spec_path}/{study_id}/group_{task}", "README.md")
with open(readme_path, "w") as f:
    f.write(grp_readme)