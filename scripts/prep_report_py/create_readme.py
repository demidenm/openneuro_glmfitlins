import os 
import json

def generate_studysummary(spec_path, study_id, data, repo_url="https://github.com/demidenm/openneuro_glmfitlins/blob/main"):
    """
    Generates a README.md file summarizing study details and links to MRIQC summary HTML files.

    Parameters:
    - spec_path: Path where the README.md should be saved.
    - study_id: Study identifier.
    - data: Dictionary containing study details (subjects, tasks, trial types).
    - repo_url: Base GitHub repository URL for generating HTML preview links using https://htmlpreview.github.io/
    """

    readme_content = f"# Study Details: {study_id}\n\n"
    readme_content += f"## Number of Subjects\n- BIDS Input: {len(data['Subjects'])}\n\n"

    # Add sessions information if multiple sessions exist
    if data.get('Sessions') and len(data['Sessions']) > 1:
        readme_content += "## Sessions\n"
        readme_content += f"- Sessions: {', '.join(data['Sessions'])}\n\n"

    readme_content += "## Tasks and Trial Types\n"

    for task_name, task_info in data["Tasks"].items():
        readme_content += f"### Task: {task_name}\n"
        readme_content += f"- **Column Names**: {', '.join(task_info['column_names'])}\n"
        readme_content += f"- **Data Types**: {', '.join([f'{col} ({dtype})' for col, dtype in task_info['column_data_types'].items()])}\n"
        if task_info['bold_volumes']:
            readme_content += f"- **BOLD Volumes**: {task_info['bold_volumes']}\n"
        else:
            readme_content += "- **BOLD Volumes**: None\n"
        if task_info['trial_type_values']:
            readme_content += f"- **Unique 'trial_type' Values**: {', '.join(map(str, task_info['trial_type_values']))}\n"
        else:
            readme_content += "- **Unique 'trial_type' Values**: None\n"
        readme_content += "\n"

    # Scan for HTML files in spec_path/mriqc_summary
    mriqc_dir = os.path.join(spec_path, "mriqc_summary")
    if os.path.exists(mriqc_dir):
        html_files = [f for f in os.listdir(mriqc_dir) if f.endswith(".html")]

        if html_files:
            readme_content += "## MRIQC Summary Reports\n"
            for html_file in sorted(html_files):
                file_url = f"https://htmlpreview.github.io/?{repo_url}/statsmodel_specs/{study_id}/mriqc_summary/{html_file}"
                readme_content += f"- [{html_file}]({file_url})\n"

    # Save the README.md file
    readme_path = os.path.join(spec_path, "README.md")
    with open(readme_path, "w") as f:
        f.write(readme_content)

    print(f"README.md file created at {readme_path}")
    print("\tReview output and update calibration and events preproc values, as needed\n")


def generate_groupmodsummary(study_id, task, num_subjects, hrf_model_type, signal_regressors, noise_regressors, convolved_regressors,
    has_run, has_subject, contrast_dict, contrast_image, design_image, spec_imgs_dir, sub_flag, r2_quality_ran, sessions=None, 
    deriv_size=None):
    # Add title and description
    readme_content = f"# {study_id}: {task} Task Analysis Report\n"
    if deriv_size:
        readme_content += f"\n{deriv_size}\n\n"
    
    readme_content += "## Statistical Analysis Boilerplate\n\n"
    readme_content += f"### First-level Analysis\n"
    readme_content += f"FitLins was employed to estimate task-related BOLD activity in the {task} task for {num_subjects} subjects. In this instance, FitLins used the Nilearn estimator in its statistical modeling of the BOLD data. "
    readme_content += f"For each participant, {len(convolved_regressors)} regressors of interest (out of total {len(signal_regressors)} regressors; see list below) were convolved with a {hrf_model_type} hemodynamic response function in Nilearn. "
    readme_content += f"The design matrix incorporated both regressors of interest and {len(noise_regressors)} additional components, including a drift cosine basis set and nuisance regressors to account for sources of noise in the BOLD signal. "
    readme_content += f"Following Nilearn's *FirstLevelModel* default procedure, each voxel's timeseries was mean-scaled by each voxel's mean of the timeseries. "
    readme_content += f"Data were smoothed at each run using a 5mm full-width at half maximum smoothing kernal (default: isotropic additive smoothing). "
    readme_content += f"From the resulting model, {len(contrast_dict)} distinct contrast estimates were computed (see list below).\n\n"
    
    readme_content += f"### Model Outputs\n"
    readme_content += f"For each participant's run, outputs include but are not limited to:\n"
    readme_content += f"- A complete design matrix visualization\n"
    readme_content += f"- Model fit statistics (R-squared and log-likelihood maps)\n"
    readme_content += f"- For each contrast: effect size maps (beta values), t-statistic maps, z-statistic maps and variance maps\n\n"
    
    readme_content += f"An example design matrix and contrast weight specifications are provided below.\n\n"
    
    readme_content += f"### Group-level Analysis\n"
    if has_subject:
        readme_content += f"Within-subject runs were combined using Nilearn's *compute_fixed_effects* function (without precision weighting; `precision_weighted=False`). "
        readme_content += f"These subject-level average statistical maps were then entered into a group-level analysis using a two-sided one-sample t-test to estimate average univariate activation patterns.\n\n"
    else:
        readme_content += f"Subject-level statistical maps were entered directly into a group-level analysis using a two-sided one-sample t-test to to estimate average univariate activation patterns.\n\n"

    readme_content += "## Additional Analysis Details \n"
    readme_content += "### Regressors of Interest\n"
    readme_content += ", ".join(signal_regressors) if signal_regressors else "None identified\n"
    readme_content += "\n#### Convolved Regressors\n"
    readme_content += ", ".join(convolved_regressors) if convolved_regressors else "None identified\n"
    
    readme_content += "\n### Nuisance Regressors\n"
    readme_content += ", ".join(noise_regressors) if noise_regressors else "None identified"
    
    readme_content += "\n## Model Structure\n"
    readme_content += f"- Run-level models: {'Yes' if has_run else 'No'}\n"
    readme_content += f"- Subject-level models: {'Yes' if has_subject else 'No'}\n"
    
    readme_content += "\n## Contrasts of Interest\n"
    for name, expr in contrast_dict.items():
        readme_content += f"- **{name}**: {expr}\n"
    
    readme_content += "\n## Figures\n"
    readme_content += f"\n### Contrast Weights\n![Contrast Weight]({f"./files/{contrast_image}"})\n"
    readme_content += f"\nThe contrast maps represents the weights used to model brain activity.\n"
    readme_content += f"\n### Design Matrix\n![Design Matrix]({f"./files/{design_image}"})\n"
    readme_content += f"\nThe example design matrix illustrates the model used in the statistical analyses for this task (Note: if motion outliers are included, the number of these will vary between subjects). Each column represents a regressor (of interest or not of interest, based on the above), and each row represents a time point in the BOLD timeseries. The colored patterns show how different experimental conditions are modeled across the scan duration (HRF model).\n"
    readme_content += f"\n### Variance Inflation Factor (VIF)\n![VIF Distribution]({f"./files/{study_id}_task-{task}_vif-boxplot.png"})\n"
    readme_content += f"\nThe above includes 1) regressor and 2) contrast VIF estimates. The VIF boxplot quantifies multicollinearity between model regressors and how they impact contrasts (for more on contrasts VIFs, see [Dr. Mumford's repo](https://github.com/jmumford/vif_contrasts)). Lower VIF values indicate more statistically independent regressors, which is desirable for reliable parameter estimation. VIFs were estimated using the first-level model design matrices -- nusiance regressors are excluded here for brevity.\n"
    readme_content += f"\n### Voxelwise Model Variance Explained (r-squared)\n"
    readme_content += (
    f"Voxelwise R-squared values represent the proportion of variance explained by the "
    f"model at each voxel in the brain. The R-squared images shown here are calculated across runs, subjects and/or sessions (dependent on data Fitlins nodes) for the study and task.\n\n"
    
    f"#### Voxelwise Average (Mean)\n"
    f"The **mean** R-squared image reflect the average of the R-squared values across all subjects and runs."
    f"In other words, the fluctuation in how much variability in the BOLD signal the model explains at a given voxel.\n"

    f"![R Square]({f'./files/{study_id}_task-{task}_rsquare-mean.png'})\n\n"
    
    f"#### Voxelwise Variance (Standard Deviation)\n"
    f"The **standard deviation** (or variance) image provides insights into the variability of model performance."
    f"In otherwords, across subjects, runs and/or sessions, how much variability there is in the models ability to explain the BOLD at a given voxel.\n"
    )

    if r2_quality_ran:
        readme_content += (
            f"\n#### Flagged Subjects\n"
            f"The quality assessment pipeline evaluates volumetric data across multiple dimensions to identify problematic datasets. Subjects are flagged using: \n\n"
            f"  - Dice Estimate: Similarity coefficient between subject r-squared maps and Target Space MNI152 mask falls below .80 (captures dropout and excess non-brain voxels) \n"
            f"  - Voxels Outside of Mask: Percentage of voxels outside of the target brain mask is greater than the .10% (liberal threshold due to liberal brain masks in fMRIPrep BOLD, captures mostly non-brain voxels) \n\n"
            f"The subjects flagged for {task} are:\n"

            f"{', '.join(sub_flag) if sub_flag else 'None Subjects Flagged'}\n\n"

            f"The distribution for subjects and runs in {task} are below. \n\n"

            f"![Dice](./files/{study_id}_task-{task}_hist-dicesimilarity.png)\n"
            f"![Voxels Out](./files/{study_id}_task-{task}_hist-voxoutmask.png)\n"
        )

 
    # Add contrast maps
    readme_content += "\n### Statistical Maps\n"
    for con_name in contrast_dict.keys():
        if sessions is None:
            # no sessions specified, look for the non-session contrast map
            map_path = f"./files/{study_id}_task-{task}_contrast-{con_name}_map.png"
            if os.path.exists(os.path.join(spec_imgs_dir, f"{study_id}_task-{task}_contrast-{con_name}_map.png")):
                readme_content += f"\n#### {con_name}\n![{con_name} Map]({map_path})\n"
        else:
            # for each session, add its contrast map if it exists
            readme_content += f"\n#### {con_name}\n"
            session_maps_found = False
            
            for session in sessions:
                session_map_path = f"./files/{study_id}_task-{task}_{session}_contrast-{con_name}_map.png"
                if os.path.exists(os.path.join(spec_imgs_dir, f"{study_id}_task-{task}_{session}_contrast-{con_name}_map.png")):
                    readme_content += f"\n##### {session}\n![{con_name} {session} Map]({session_map_path})\n"
                    session_maps_found = True
            
            # If no session maps were found, check if there's a non-session map available
            if not session_maps_found:
                map_path = f"./files/{study_id}_task-{task}_contrast-{con_name}_map.png"
                if os.path.exists(os.path.join(spec_imgs_dir, f"{study_id}_task-{task}_contrast-{con_name}_map.png")):
                    readme_content += f"![{con_name} Map]({map_path})\n"
                else:
                    readme_content += f"*No statistical maps available for contrast {con_name}*\n"
    
    return readme_content
