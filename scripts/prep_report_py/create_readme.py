import os 
from pathlib import Path
import json
import glob

def generate_studysummary(spec_path, study_id, data, repo_url="https://github.com/demidenm/openneuro_glmfitlins/blob/main"):
    """
    Generates a README.md file summarizing study details and links to MRIQC summary HTML files.

    Parameters:
    - spec_path: Path where the README.md should be saved.
    - study_id: Study identifier.
    - data: Dictionary containing study details (subjects, tasks, trial types).
    - repo_url: Base GitHub repository URL for generating HTML preview links using https://htmlpreview.github.io/
    """
    readme_content = ""  # Initialize readme_content

    readme_content += (
        f"[![OpenNeuro ID](https://img.shields.io/badge/OpenNeuro_Dataset-{study_id}-blue?style=for-the-badge)]"
        f"(https://openneuro.org/datasets/{study_id})\n\n"
    )
    
    readme_content += f"# Dataset Details: {study_id}\n\n"
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
        # iteratre and add per task compiled descrptives
        image_pattern = os.path.join(spec_path, "basics_out", f"{task_name}*.png")
        image_files = glob.glob(image_pattern)
        
        if image_files:
            readme_content += "**Count Summaries**:\n"
            for image_file in sorted(image_files):
                # filename for cleaner display
                image_path = Path(image_file)
                image_name = image_path.name
                # Create relative path from spec_path
                relative_image_path = image_path.relative_to(Path(spec_path))
                readme_content += f"\n![{task_name} {image_name}]({relative_image_path})\n"
    
    readme_content += "\n"

    # Scan for HTML files in spec_path/mriqc_summary
    mriqc_dir = spec_path / "mriqc_summary"
    if mriqc_dir.exists():
        html_files = [f.name for f in mriqc_dir.iterdir() if f.suffix == ".html"]

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


def generate_groupmodsummary(study_id, task, num_subjects, hrf_model_type, signal_regressors, noise_regressors, convolved_regressors, paramod_regressors,
    has_run, has_subject, contrast_dict, contrast_image, design_image, spec_imgs_dir, sub_flag, r2_quality_ran, sessions=None, 
    deriv_size=None, task_cites=None):
    # Add title and description
    readme_content = f"# {study_id}: {task} Task Analysis Report\n"
    if deriv_size:
        readme_content += f"\n{deriv_size}\n\n"
    
    if task_cites:
        cite_str = ', '.join(f"[Paper {i+1}]({link})" for i, link in enumerate(task_cites))
        readme_content += f"Dataset- and task-relevant citations may be found in the papers: {cite_str}.\n\n"

    readme_content += "## 1. Statistical Analysis [Boilerplate]\n\n"
    readme_content += "The below is an automatically generated report for the statistical analyses performed on this task and dataset. Some reporting standards from the 'Statistical Modeling & Inference' section of "    
    readme_content += "the COBIDAS checklist ([Nichols et al., 2017](https://www.nature.com/articles/nn.4500)) are adopted here.\n\n"

    readme_content += f"### 1.1. First-level Analysis\n"
    readme_content += f"For the {num_subjects} subjects, whole-brain, mass univariate analyses were performed using a general linear model (GLM). "
    readme_content += f"The {len(convolved_regressors)} regressors of interest (out of {len(signal_regressors)} total regressors) were convolved with a {hrf_model_type} hemodynamic response function (see Section 2.3 for list). "

    if paramod_regressors:
        readme_content += f"Of the convolved regressors, {len(paramod_regressors)} were parametrically modulated regressors in the model (see Section 2.4 for list). "
        readme_content += f"The design matrix (see example in Section 4.1) included both the convolved and parametrically modulated regressors of interest and {len(noise_regressors)} nuisance regressors to account for physiological noise and motion-related artifacts (see Section 2.4 for full list).\n\n"

    else:
        readme_content += f"The design matrix (see example in Section 4.1) included both the convolved regressors of interest and {len(noise_regressors)} nuisance regressors to account for physiological noise and motion-related artifacts (see Section 2.4 for full list).\n\n"

    readme_content += "**Motion Regressors**: Motion parameters included the six rigid-body parameters estimated during motion correction (three translations, three rotations), their temporal derivatives, and the squares of both the parameters and their derivatives, resulting in 24 motion-related regressors.\n"
    readme_content += "**Drift Regressors**: Cosine basis functions implemented a high-pass temporal filter with a cutoff of 128 seconds to remove low-frequency drift in the BOLD signal.\n\n"

    readme_content += f"**Model Implementation**: All regressors were included in the subject-level first-level General Linear Model (GLM) using FitLins with the Nilearn estimator. "
    readme_content += "The preprocessed (fMRIPrep) BOLD time series were pre-whitened using an autoregressive AR(1) model to correct for temporal autocorrelation. "
    readme_content += "Spatial smoothing was applied with a 5 mm full-width at half maximum (FWHM) Gaussian kernel (isotropic additive smoothing). "
    readme_content += f"Each voxel's timeseries was mean-scaled by the voxel's mean signal value following Nilearn's *FirstLevelModel* default procedure.\n\n"
    readme_content += f"Each voxel's timeseries (Y) was regressed onto the resulting design matrix (Xβ), which included the regressors and an intercept term . As illustrated in Section 3, {len(contrast_dict.items())} linear contrasts were computed\n\n"


    readme_content += f"### 1.2. Model Outputs\n"
    readme_content += f"For each run and subject, outputs include but are not limited to:\n"
    readme_content += f"- A complete design matrix for visualization\n"
    readme_content += f"- Model fit statistics (R-squared and log-likelihood maps)\n"
    readme_content += f"- For each contrast: effect size maps (beta values), t-statistic maps, z-statistic maps and variance maps\n\n"
        
    readme_content += f"### 1.3. Subject- and Group-level Analyses\n"
    if has_subject:
        readme_content += f"**Within-subject combination**: After the GLM was computed for each subjects' run, multiple runs per subject were combined using Nilearn's *compute_fixed_effects* function with precision weighting disabled (`precision_weighted=False`), implementing a fixed-effects model across runs within each subject. "
        readme_content += f"**Group-level model**: The resulting subject-level average statistical maps were entered into a random-effects group analysis using a two-sided one-sample t-test against zero to estimate population-level activation patterns. "
        readme_content += f"This approach treats subjects as a random effect, allowing inferences to generalize to the broader population. Resulting group maps were not cluster corrected but thresholded at z > 2.3 for display purposes (see section 5). More details and images are provided below. \n\n"
    else:
        readme_content += f"**Group-level model**: Subject-level statistical maps (single run per subject) were entered directly into a random-effects group analysis using a two-sided one-sample t-test against zero to estimate population-level activation patterns. "
        readme_content += f"This approach treats subjects as a random effect, allowing inferences to generalize to the broader population. Resulting group maps were not cluster corrected but thresholded at z > 2.3 for display purposes (see section 5). More details and images are provided below. \n\n"

    readme_content += "## 2. Additional Analytic Details \n\n"
    readme_content += "\n### 2.1 BIDS Stats Model Structure\n"
    readme_content += f"- Run-level models: {'Yes' if has_run else 'No'}\n"
    readme_content += f"- Subject-level models: {'Yes' if has_subject else 'No'}\n"
    readme_content += f"- Dataset-level models: Yes \n\n"

    readme_content += "### 2.2 Regressors of Interest\n"
    readme_content += ", ".join(signal_regressors) if signal_regressors else "None identified\n"
    readme_content += "\n\n### 2.3 Convolved Regressors\n"
    readme_content += ", ".join(convolved_regressors) if convolved_regressors else "None identified\n"
    readme_content += "\n\n### 2.4 Parametrically Modulated Regressors*\n"
    readme_content += ", ".join(paramod_regressors) if paramod_regressors else "None identified\n"
    readme_content += "\n\n> **Note:** Parametric regressors are auto-identified by excluding: intercept, constant, trial_type.* and duration-assigned variables from non-nuisance regressors."

    readme_content += "\n\n### 2.5 Nuisance Regressors\n"
    readme_content += ", ".join(noise_regressors) if noise_regressors else "None identified"


    readme_content += "\n\n## 3 Contrasts of Interest\n"
    for name, expr in contrast_dict.items():
        readme_content += f"- **{name}**: {expr}\n\n"
    
    readme_content += "\n# 4 Figures\n"
    readme_content += f"\n## 4.1 Design Matrix\n![Design Matrix]({f"./files/{design_image}"})\n"
    readme_content += f"\nThe example design matrix illustrates the model used in the statistical analyses for this task (Note: if motion outliers are included, the number of these will vary between subjects). Each column represents a regressor (of interest or not of interest, based on the above), and each row represents a time point in the BOLD timeseries. The colored patterns show how different experimental conditions are modeled across the scan duration (HRF model).\n"
    readme_content += f"\n## 4.2 Contrast Weights\n![Contrast Weight]({f"./files/{contrast_image}"})\n"
    readme_content += f"\nThe contrast maps represent the weights used to model brain activity.\n"
    readme_content += f"\n## 4.3 Variance Inflation Factor (VIF)\n![VIF Distribution]({f"./files/{study_id}_task-{task}_vif-boxplot.png"})\n"
    readme_content += f"\nThe above includes 1) regressor and 2) contrast VIF estimates. The VIF boxplot quantifies multicollinearity between model regressors and how they impact contrasts (for more on contrasts VIFs, see [Dr. Mumford's repo](https://github.com/jmumford/vif_contrasts))."
    readme_content += f"High VIF (e.g., >5 or >10) indicates that collinearity is inflating the variance at a potentially concerning level, which may lead to outliers.  Data should be queried to assess for outliers (e.g. [fmri-outlier-detector](https://github.com/jmumford/fmri-outlier-detector)). VIFs were estimated using the first-level model design matrices -- nusiance regressors are excluded here for brevity.\n"
    readme_content += f"\n## 4.4 Voxelwise Model Variance Explained (r-squared)\n"
    readme_content += (
    f"Voxelwise R-squared values represent the proportion of variance explained by the "
    f"model at each voxel in the brain. The R-squared images shown here are calculated across runs, subjects and/or sessions (dependent on data BIDS Stats Model nodes) for the study and task.\n\n"
    
    f"### 4.4.1 Voxelwise Average (Mean)\n"
    f"The **mean** R-squared image reflect the average of the R-squared values across all subjects and runs."
    f"In other words, the fluctuation in how much variability in the BOLD signal the model explains at a given voxel.\n"

    f"![R Square]({f'files/{study_id}_task-{task}_rsquare-mean.png'})\n\n"
    
    f"### 4.4.2 Voxelwise Variance (Standard Deviation)\n"
    f"The **standard deviation** (or variance) image provides insights into the variability of model performance."
    f"In otherwords, across subjects, runs and/or sessions, how much variability there is in the models ability to explain the BOLD at a given voxel.\n"
    )

    if r2_quality_ran:
        readme_content += (
            f"\n#### 4.4.3 Flagged Subjects\n"
            f"The quality assessment pipeline evaluates volumetric data across multiple dimensions to identify problematic datasets. Subjects are flagged using: \n\n"
            f"  - Dice Estimate: Similarity coefficient between subject r-squared maps and Target Space MNI152 mask falls below .80 (captures dropout and excess non-brain voxels) \n"
            f"  - Voxels Outside of Mask: Percentage of voxels outside of the target brain mask is greater than the .10% (liberal threshold due to liberal brain masks in fMRIPrep BOLD, captures mostly non-brain voxels) \n\n"
            f"The subjects flagged for {task} are:\n"

            f"{', '.join(sub_flag) if sub_flag else 'None Subjects Flagged'}\n\n"

            f"The distribution for subjects and runs in {task} are below. \n\n"

            f"![Dice](files/{study_id}_task-{task}_hist-dicesimilarity.png)\n"
            f"![Voxels Out](files/{study_id}_task-{task}_hist-voxoutmask.png)\n"
        )

 
    # Add contrast maps
    readme_content += "\n## 5 Statistical Maps\n"
    for con_name in contrast_dict.keys():
        if sessions is None:
            # no sessions specified, look for the non-session contrast map
            map_path = f"files/{study_id}_task-{task}_contrast-{con_name}_map.png"
            map_file_path = Path(spec_imgs_dir) / f"{study_id}_task-{task}_contrast-{con_name}_map.png"
            if map_file_path.exists():
                readme_content += f"\n### {con_name}\n![{con_name} Map]({map_path})\n"
        else:
            # for each session, add its contrast map if it exists
            readme_content += f"\n### {con_name}\n"
            session_maps_found = False
            
            for session in sessions:
                session_map_path = f"files/{study_id}_task-{task}_{session}_contrast-{con_name}_map.png"
                session_map_file = spec_imgs_dir / f"{study_id}_task-{task}_{session}_contrast-{con_name}_map.png"
                if session_map_file.exists():
                    readme_content += f"\n#### {session}\n![{con_name} {session} Map]({session_map_path})\n"
                    session_maps_found = True
            
            # If no session maps were found, check if there's a non-session map available
            if not session_maps_found:
                map_path = f"files/{study_id}_task-{task}_contrast-{con_name}_map.png"
                map_file = spec_imgs_dir / f"{study_id}_task-{task}_contrast-{con_name}_map.png"
                if map_file.exists():
                    readme_content += f"![{con_name} Map]({map_path})\n"
                else:
                    readme_content += f"*No statistical maps available for contrast {con_name}*\n"
    
    return readme_content
