# ds003545: prodL1 Task Analysis Report

The size of the Fitlins Derivatives for ds003545 prodL1 is 8.9G with 6434 files.

Dataset- and task-relevant citations may be found in the papers: [Paper 1](https://doi.org/10.1523/JNEUROSCI.0851-20.2020).

## 1. Statistical Analysis [Boilerplate]

The below is an automatically generated report for the statistical analyses performed on this task and dataset. Some reporting standards from the 'Statistical Modeling & Inference' section of the COBIDAS checklist ([Nichols et al., 2017](https://www.nature.com/articles/nn.4500)) are adopted here.

### 1.1. First-level Analysis
For the 23 subjects, whole-brain, mass univariate analyses were performed using a general linear model (GLM). The 5 regressors of interest (out of 6 total regressors) were convolved with a spm hemodynamic response function (see Section 2.3 for list). The design matrix (see example in Section 4.1) included both the convolved regressors of interest and 34 nuisance regressors to account for physiological noise and motion-related artifacts (see Section 2.4 for full list).

**Motion Regressors**: Motion parameters included the six rigid-body parameters estimated during motion correction (three translations, three rotations), their temporal derivatives, and the squares of both the parameters and their derivatives, resulting in 24 motion-related regressors.
**Drift Regressors**: Cosine basis functions implemented a high-pass temporal filter with a cutoff of 128 seconds to remove low-frequency drift in the BOLD signal.

**Model Implementation**: All regressors were included in the subject-level first-level General Linear Model (GLM) using FitLins with the Nilearn estimator. The preprocessed (fMRIPrep) BOLD time series were pre-whitened using an autoregressive AR(1) model to correct for temporal autocorrelation. Spatial smoothing was applied with a 5 mm full-width at half maximum (FWHM) Gaussian kernel (isotropic additive smoothing). Each voxel's timeseries was mean-scaled by the voxel's mean signal value following Nilearn's *FirstLevelModel* default procedure.

Each voxel's timeseries (Y) was regressed onto the resulting design matrix (Xβ), which included the regressors and an intercept term . As illustrated in Section 3, 7 linear contrasts were computed

### 1.2. Model Outputs
For each run and subject, outputs include but are not limited to:
- A complete design matrix for visualization
- Model fit statistics (R-squared and log-likelihood maps)
- For each contrast: effect size maps (beta values), t-statistic maps, z-statistic maps and variance maps

### 1.3. Subject- and Group-level Analyses
**Within-subject combination**: After the GLM was computed for each subjects' run, multiple runs per subject were combined using Nilearn's *compute_fixed_effects* function with precision weighting disabled (`precision_weighted=False`), implementing a fixed-effects model across runs within each subject. **Group-level model**: The resulting subject-level average statistical maps were entered into a random-effects group analysis using a two-sided one-sample t-test against zero to estimate population-level activation patterns. This approach treats subjects as a random effect, allowing inferences to generalize to the broader population. Resulting group maps were not cluster corrected but thresholded at z > 2.3 for display purposes (see section 5). More details and images are provided below. 

## 2. Additional Analytic Details 


### 2.1 BIDS Stats Model Structure
- Run-level models: Yes
- Subject-level models: Yes
- Dataset-level models: Yes 

### 2.2 Regressors of Interest
trial_type.control_cond, trial_type.end_fixation, trial_type.fixation, trial_type.irrelevant_cond, trial_type.semantic_cond, intercept

### 2.3 Convolved Regressors
trial_type.control_cond, trial_type.end_fixation, trial_type.fixation, trial_type.irrelevant_cond, trial_type.semantic_cond

### 2.4 Parametrically Modulated Regressors*
None identified


> **Note:** Parametric regressors are auto-identified by excluding: intercept, constant, trial_type.* and duration-assigned variables from non-nuisance regressors.

### 2.5 Nuisance Regressors
trans_x, trans_x_derivative1, trans_x_derivative1_power2, trans_x_power2, trans_y, trans_y_derivative1, trans_y_derivative1_power2, trans_y_power2, trans_z, trans_z_derivative1, trans_z_derivative1_power2, trans_z_power2, rot_x, rot_x_derivative1, rot_x_derivative1_power2, rot_x_power2, rot_y, rot_y_derivative1, rot_y_derivative1_power2, rot_y_power2, rot_z, rot_z_derivative1, rot_z_derivative1_power2, rot_z_power2, cosine00, cosine01, cosine02, cosine03, cosine04, cosine05, cosine06, cosine07, cosine08, cosine09

## 3 Contrasts of Interest
- **semanticvcontrol**: 1*`trial_type.semantic_cond` - 1*`trial_type.control_cond`

- **semanticvirrelevant**: 1*`trial_type.semantic_cond` - 1*`trial_type.irrelevant_cond`

- **controlvirrelevant**: 1*`trial_type.control_cond` - 1*`trial_type.irrelevant_cond`

- **taskvfixation**: 1*`trial_type.semantic_cond` + 1*`trial_type.control_cond` + 1*`trial_type.irrelevant_cond` - 3*`trial_type.fixation`

- **semanticvfixation**: 1*`trial_type.semantic_cond` - 1*`trial_type.fixation`

- **controlvfixation**: 1*`trial_type.control_cond` - 1*`trial_type.fixation`

- **irrelevantvfixation**: 1*`trial_type.irrelevant_cond` - 1*`trial_type.fixation`


# 4 Figures

## 4.1 Design Matrix
![Design Matrix](./files/ds003545_task-prodL1_design-matrix.svg)

The example design matrix illustrates the model used in the statistical analyses for this task (Note: if motion outliers are included, the number of these will vary between subjects). Each column represents a regressor (of interest or not of interest, based on the above), and each row represents a time point in the BOLD timeseries. The colored patterns show how different experimental conditions are modeled across the scan duration (HRF model).

## 4.2 Contrast Weights
![Contrast Weight](./files/ds003545_task-prodL1_contrast-matrix.svg)

The contrast maps represent the weights used to model brain activity.

## 4.3 Variance Inflation Factor (VIF)
![VIF Distribution](./files/ds003545_task-prodL1_vif-boxplot.png)

The above includes 1) regressor and 2) contrast VIF estimates. The VIF boxplot quantifies multicollinearity between model regressors and how they impact contrasts (for more on contrasts VIFs, see [Dr. Mumford's repo](https://github.com/jmumford/vif_contrasts)).High VIF (e.g., >5 or >10) indicates that collinearity is inflating the variance at a potentially concerning level, which may lead to outliers.  Data should be queried to assess for outliers (e.g. [fmri-outlier-detector](https://github.com/jmumford/fmri-outlier-detector)). VIFs were estimated using the first-level model design matrices -- nusiance regressors are excluded here for brevity.

## 4.4 Voxelwise Model Variance Explained (r-squared)
Voxelwise R-squared values represent the proportion of variance explained by the model at each voxel in the brain. The R-squared images shown here are calculated across runs, subjects and/or sessions (dependent on data BIDS Stats Model nodes) for the study and task.

### 4.4.1 Voxelwise Average (Mean)
The **mean** R-squared image reflect the average of the R-squared values across all subjects and runs.In other words, the fluctuation in how much variability in the BOLD signal the model explains at a given voxel.
![R Square](files/ds003545_task-prodL1_rsquare-mean.png)

### 4.4.2 Voxelwise Variance (Standard Deviation)
The **standard deviation** (or variance) image provides insights into the variability of model performance.In otherwords, across subjects, runs and/or sessions, how much variability there is in the models ability to explain the BOLD at a given voxel.

#### 4.4.3 Flagged Subjects
The quality assessment pipeline evaluates volumetric data across multiple dimensions to identify problematic datasets. Subjects are flagged using: 

  - Dice Estimate: Similarity coefficient between subject r-squared maps and Target Space MNI152 mask falls below .85 (captures dropout and excess non-brain voxels) 
  - Voxels Outside of Mask: Percentage of voxels outside of the target brain mask is greater than the .10% (liberal threshold due to liberal brain masks in fMRIPrep BOLD, captures mostly non-brain voxels) 

The subjects flagged for prodL1 are:
sub-13_ses-02_run-2, sub-15_ses-01_run-1, sub-15_ses-02_run-1, sub-15_ses-02_run-2, sub-16_ses-01_run-2, sub-16_ses-02_run-1, sub-16_ses-02_run-2, sub-17_ses-02_run-2, sub-19_ses-01_run-1, sub-20_ses-01_run-2, sub-21_ses-01_run-1, sub-21_ses-01_run-2, sub-21_ses-02_run-1, sub-21_ses-02_run-2, sub-22_ses-01_run-1, sub-22_ses-01_run-2, sub-22_ses-02_run-1, sub-22_ses-02_run-2

The distribution for subjects and runs in prodL1 are below. 

![Dice](files/ds003545_task-prodL1_hist-dicesimilarity.png)
![Voxels Out](files/ds003545_task-prodL1_hist-voxoutmask.png)

## 5 Statistical Maps

### semanticvcontrol

#### ses-02
![semanticvcontrol ses-02 Map](files/ds003545_task-prodL1_ses-02_contrast-semanticvcontrol_map.png)

#### ses-01
![semanticvcontrol ses-01 Map](files/ds003545_task-prodL1_ses-01_contrast-semanticvcontrol_map.png)

### semanticvirrelevant

#### ses-02
![semanticvirrelevant ses-02 Map](files/ds003545_task-prodL1_ses-02_contrast-semanticvirrelevant_map.png)

#### ses-01
![semanticvirrelevant ses-01 Map](files/ds003545_task-prodL1_ses-01_contrast-semanticvirrelevant_map.png)

### controlvirrelevant

#### ses-02
![controlvirrelevant ses-02 Map](files/ds003545_task-prodL1_ses-02_contrast-controlvirrelevant_map.png)

#### ses-01
![controlvirrelevant ses-01 Map](files/ds003545_task-prodL1_ses-01_contrast-controlvirrelevant_map.png)

### taskvfixation

#### ses-02
![taskvfixation ses-02 Map](files/ds003545_task-prodL1_ses-02_contrast-taskvfixation_map.png)

#### ses-01
![taskvfixation ses-01 Map](files/ds003545_task-prodL1_ses-01_contrast-taskvfixation_map.png)

### semanticvfixation

#### ses-02
![semanticvfixation ses-02 Map](files/ds003545_task-prodL1_ses-02_contrast-semanticvfixation_map.png)

#### ses-01
![semanticvfixation ses-01 Map](files/ds003545_task-prodL1_ses-01_contrast-semanticvfixation_map.png)

### controlvfixation

#### ses-02
![controlvfixation ses-02 Map](files/ds003545_task-prodL1_ses-02_contrast-controlvfixation_map.png)

#### ses-01
![controlvfixation ses-01 Map](files/ds003545_task-prodL1_ses-01_contrast-controlvfixation_map.png)

### irrelevantvfixation

#### ses-02
![irrelevantvfixation ses-02 Map](files/ds003545_task-prodL1_ses-02_contrast-irrelevantvfixation_map.png)

#### ses-01
![irrelevantvfixation ses-01 Map](files/ds003545_task-prodL1_ses-01_contrast-irrelevantvfixation_map.png)
