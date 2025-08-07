# ds003858: MID Task Analysis Report
<p style="color: red; font-style: italic;">
  NOTE: The run-level data are associated with different acquisitions types (single slice, multi-band 4, multi-band 8). This group report is based on run-4, or the Multi-band 4-slice acquisition.
</p>

The size of the Fitlins Derivatives for ds003858 MID is 2.2G with 1400 files.

Dataset- and task-relevant citations may be found in the papers: [Paper 1](https://www.doi.org10.1016/j.neuroimage.2021.118617).

## 1. Statistical Analysis [Boilerplate]

The below is an automatically generated report for the statistical analyses performed on this task and dataset. Some reporting standards from the 'Statistical Modeling & Inference' section of the COBIDAS checklist ([Nichols et al., 2017](https://www.nature.com/articles/nn.4500)) are adopted here.

### 1.1. First-level Analysis
For the 12 subjects, whole-brain, mass univariate analyses were performed using a general linear model (GLM). The 21 regressors of interest (out of 22 total regressors) were convolved with a spm hemodynamic response function (see Section 2.3 for list). The design matrix (see example in Section 4.1) included both the convolved regressors of interest and 36 nuisance regressors to account for physiological noise and motion-related artifacts (see Section 2.4 for full list).

**Motion Regressors**: Motion parameters included the six rigid-body parameters estimated during motion correction (three translations, three rotations), their temporal derivatives, and the squares of both the parameters and their derivatives, resulting in 24 motion-related regressors.
**Drift Regressors**: Cosine basis functions implemented a high-pass temporal filter with a cutoff of 128 seconds to remove low-frequency drift in the BOLD signal.

**Model Implementation**: All regressors were included in the subject-level first-level General Linear Model (GLM) using FitLins with the Nilearn estimator. The preprocessed (fMRIPrep) BOLD time series were pre-whitened using an autoregressive AR(1) model to correct for temporal autocorrelation. Spatial smoothing was applied with a 5 mm full-width at half maximum (FWHM) Gaussian kernel (isotropic additive smoothing). Each voxel's timeseries was mean-scaled by the voxel's mean signal value following Nilearn's *FirstLevelModel* default procedure.

Each voxel's timeseries (Y) was regressed onto the resulting design matrix (Xβ), which included the regressors and an intercept term . As illustrated in Section 3, 17 linear contrasts were computed

### 1.2. Model Outputs
For each run and subject, outputs include but are not limited to:
- A complete design matrix for visualization
- Model fit statistics (R-squared and log-likelihood maps)
- For each contrast: effect size maps (beta values), t-statistic maps, z-statistic maps and variance maps

### 1.3. Subject- and Group-level Analyses
**Group-level model**: Subject-level statistical maps (single run per subject) were entered directly into a random-effects group analysis using a two-sided one-sample t-test against zero to estimate population-level activation patterns. This approach treats subjects as a random effect, allowing inferences to generalize to the broader population. Resulting group maps were not cluster corrected but thresholded at z > 2.3 for display purposes (see section 5). More details and images are provided below. 

## 2. Additional Analytic Details 


### 2.1 BIDS Stats Model Structure
- Run-level models: Yes
- Subject-level models: No
- Dataset-level models: Yes 

### 2.2 Regressors of Interest
trial_type.cue_largeloss, trial_type.cue_largewin, trial_type.cue_neutral, trial_type.cue_smallloss, trial_type.cue_smallwin, trial_type.fix_largeloss, trial_type.fix_largewin, trial_type.fix_neutral, trial_type.fix_smallloss, trial_type.fix_smallwin, trial_type.probe, trial_type.fb_largelosshit, trial_type.fb_largelossmiss, trial_type.fb_largewinhit, trial_type.fb_largewinmiss, trial_type.fb_neutralhit, trial_type.fb_neutralmiss, trial_type.fb_smalllosshit, trial_type.fb_smalllossmiss, trial_type.fb_smallwinhit, trial_type.fb_smallwinmiss, intercept

### 2.3 Convolved Regressors
trial_type.cue_largeloss, trial_type.cue_largewin, trial_type.cue_neutral, trial_type.cue_smallloss, trial_type.cue_smallwin, trial_type.fix_largeloss, trial_type.fix_largewin, trial_type.fix_neutral, trial_type.fix_smallloss, trial_type.fix_smallwin, trial_type.probe, trial_type.fb_largelosshit, trial_type.fb_largelossmiss, trial_type.fb_largewinhit, trial_type.fb_largewinmiss, trial_type.fb_neutralhit, trial_type.fb_neutralmiss, trial_type.fb_smalllosshit, trial_type.fb_smalllossmiss, trial_type.fb_smallwinhit, trial_type.fb_smallwinmiss

### 2.4 Parametrically Modulated Regressors*
None identified


> **Note:** Parametric regressors are auto-identified by excluding: intercept, constant, trial_type.* and duration-assigned variables from non-nuisance regressors.

### 2.5 Nuisance Regressors
trans_x, trans_x_derivative1, trans_x_derivative1_power2, trans_x_power2, trans_y, trans_y_derivative1, trans_y_derivative1_power2, trans_y_power2, trans_z, trans_z_derivative1, trans_z_derivative1_power2, trans_z_power2, rot_x, rot_x_derivative1, rot_x_derivative1_power2, rot_x_power2, rot_y, rot_y_derivative1, rot_y_derivative1_power2, rot_y_power2, rot_z, rot_z_derivative1, rot_z_derivative1_power2, rot_z_power2, cosine00, cosine01, cosine02, cosine03, cosine04, cosine05, cosine06, cosine07, cosine08, cosine09, cosine10, cosine11

## 3 Contrasts of Interest
- **cueLWvNeut**: 1*`trial_type.cue_largewin` - 1*`trial_type.cue_neutral`

- **cueWvNeut**: 0.5*`trial_type.cue_largewin` + 0.5*`trial_type.cue_smallwin` - 1*`trial_type.cue_neutral`

- **cueLLvNeut**: 1*`trial_type.cue_largeloss` - 1*`trial_type.cue_neutral`

- **cue_LvNeut**: 0.5*`trial_type.cue_largeloss` + 0.5*`trial_type.cue_smallloss` - 1*`trial_type.cue_neutral`

- **cueLWvBase**: 1*`trial_type.cue_largewin`

- **fixLWvNeut**: 1*`trial_type.fix_largewin` - 1*`trial_type.fix_neutral`

- **fixWvNeut**: 0.5*`trial_type.fix_largewin` + 0.5*`trial_type.fix_smallwin` - 1*`trial_type.fix_neutral`

- **fixLLvNeut**: 1*`trial_type.fix_largeloss` - 1*`trial_type.fix_neutral`

- **fixLvNeut**: 0.5*`trial_type.fix_largeloss` + 0.5*`trial_type.fix_smallloss` - 1*`trial_type.fix_neutral`

- **fixLWvBase**: 1*`trial_type.fix_largewin`

- **probe**: 1*`trial_type.probe`

- **fbWHitvWMiss**: 0.5*`trial_type.fb_largewinhit` + 0.5*`trial_type.fb_smallwinhit` - 0.5*`trial_type.fb_largewinmiss` - 0.5*`trial_type.fb_smallwinmiss`

- **fbLWHitvLWMiss**: 1*`trial_type.fb_largewinhit` - 1*`trial_type.fb_largewinmiss`

- **fbLHitvLMiss**: 0.5*`trial_type.fb_largelosshit` + 0.5*`trial_type.fb_smalllosshit` - 0.5*`trial_type.fb_largelossmiss` - 0.5*`trial_type.fb_smalllossmiss`

- **fbLLHitvLLMiss**: 1*`trial_type.fb_largelosshit` - 1*`trial_type.fb_largelossmiss`

- **fbLWHitvNeutHit**: 1*`trial_type.fb_largewinhit` - 1*`trial_type.fb_neutralhit`

- **fbLWHitvBase**: 1*`trial_type.fb_largewinhit`


# 4 Figures

## 4.1 Design Matrix
![Design Matrix](./files/ds003858_task-MID_design-matrix.svg)

The example design matrix illustrates the model used in the statistical analyses for this task (Note: if motion outliers are included, the number of these will vary between subjects). Each column represents a regressor (of interest or not of interest, based on the above), and each row represents a time point in the BOLD timeseries. The colored patterns show how different experimental conditions are modeled across the scan duration (HRF model).

## 4.2 Contrast Weights
![Contrast Weight](./files/ds003858_task-MID_contrast-matrix.svg)

The contrast maps represent the weights used to model brain activity.

## 4.3 Variance Inflation Factor (VIF)
![VIF Distribution](./files/ds003858_task-MID_vif-boxplot.png)

The above includes 1) regressor and 2) contrast VIF estimates. The VIF boxplot quantifies multicollinearity between model regressors and how they impact contrasts (for more on contrasts VIFs, see [Dr. Mumford's repo](https://github.com/jmumford/vif_contrasts)).High VIF (e.g., >5 or >10) indicates that collinearity is inflating the variance at a potentially concerning level, which may lead to outliers.  Data should be queried to assess for outliers (e.g. [fmri-outlier-detector](https://github.com/jmumford/fmri-outlier-detector)). VIFs were estimated using the first-level model design matrices -- nusiance regressors are excluded here for brevity.

## 4.4 Voxelwise Model Variance Explained (r-squared)
Voxelwise R-squared values represent the proportion of variance explained by the model at each voxel in the brain. The R-squared images shown here are calculated across runs, subjects and/or sessions (dependent on data BIDS Stats Model nodes) for the study and task.

### 4.4.1 Voxelwise Average (Mean)
The **mean** R-squared image reflect the average of the R-squared values across all subjects and runs.In other words, the fluctuation in how much variability in the BOLD signal the model explains at a given voxel.
![R Square](files/ds003858_task-MID_rsquare-mean.png)

### 4.4.2 Voxelwise Variance (Standard Deviation)
The **standard deviation** (or variance) image provides insights into the variability of model performance.In otherwords, across subjects, runs and/or sessions, how much variability there is in the models ability to explain the BOLD at a given voxel.

#### 4.4.3 Flagged Subjects
The quality assessment pipeline evaluates volumetric data across multiple dimensions to identify problematic datasets. Subjects are flagged using: 

  - Dice Estimate: Similarity coefficient between subject r-squared maps and Target Space MNI152 mask falls below .80 (captures dropout and excess non-brain voxels) 
  - Voxels Outside of Mask: Percentage of voxels outside of the target brain mask is greater than the .10% (liberal threshold due to liberal brain masks in fMRIPrep BOLD, captures mostly non-brain voxels) 

The subjects flagged for MID are:
sub-01_run-4, sub-02_run-4, sub-03_run-4, sub-04_run-4, sub-05_run-4, sub-06_run-4, sub-07_run-4, sub-08_run-4, sub-09_run-4, sub-10_run-4, sub-11_run-4, sub-12_run-4

The distribution for subjects and runs in MID are below. 

![Dice](files/ds003858_task-MID_hist-dicesimilarity.png)
![Voxels Out](files/ds003858_task-MID_hist-voxoutmask.png)

## 5 Statistical Maps

### cueLWvNeut
![cueLWvNeut Map](files/ds003858_task-MID_contrast-cueLWvNeut_map.png)

### cueWvNeut
![cueWvNeut Map](files/ds003858_task-MID_contrast-cueWvNeut_map.png)

### cueLLvNeut
![cueLLvNeut Map](files/ds003858_task-MID_contrast-cueLLvNeut_map.png)

### cue_LvNeut
*No statistical maps available for contrast cue_LvNeut*

### cueLWvBase
![cueLWvBase Map](files/ds003858_task-MID_contrast-cueLWvBase_map.png)

### fixLWvNeut
![fixLWvNeut Map](files/ds003858_task-MID_contrast-fixLWvNeut_map.png)

### fixWvNeut
![fixWvNeut Map](files/ds003858_task-MID_contrast-fixWvNeut_map.png)

### fixLLvNeut
![fixLLvNeut Map](files/ds003858_task-MID_contrast-fixLLvNeut_map.png)

### fixLvNeut
![fixLvNeut Map](files/ds003858_task-MID_contrast-fixLvNeut_map.png)

### fixLWvBase
![fixLWvBase Map](files/ds003858_task-MID_contrast-fixLWvBase_map.png)

### probe
![probe Map](files/ds003858_task-MID_contrast-probe_map.png)

### fbWHitvWMiss
![fbWHitvWMiss Map](files/ds003858_task-MID_contrast-fbWHitvWMiss_map.png)

### fbLWHitvLWMiss
![fbLWHitvLWMiss Map](files/ds003858_task-MID_contrast-fbLWHitvLWMiss_map.png)

### fbLHitvLMiss
![fbLHitvLMiss Map](files/ds003858_task-MID_contrast-fbLHitvLMiss_map.png)

### fbLLHitvLLMiss
![fbLLHitvLLMiss Map](files/ds003858_task-MID_contrast-fbLLHitvLLMiss_map.png)

### fbLWHitvNeutHit
![fbLWHitvNeutHit Map](files/ds003858_task-MID_contrast-fbLWHitvNeutHit_map.png)

### fbLWHitvBase
![fbLWHitvBase Map](files/ds003858_task-MID_contrast-fbLWHitvBase_map.png)
