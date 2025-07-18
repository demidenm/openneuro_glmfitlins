# ds000114: fingerfootlips Task Analysis Report

The size of the Fitlins Derivatives for ds000114 fingerfootlips is 5.2M with 1178 files.

Dataset- and task-relevant citations may be found in the papers: [Paper 1](https://doi.org/10.1186/2047-217X-2-6).

## 1. Statistical Analysis [Boilerplate]

The below is an automatically generated report for the statistical analyses performed on this task and dataset. Some reporting standards from the 'Statistical Modeling & Inference' section of the COBIDAS checklist ([Nichols et al., 2017](https://www.nature.com/articles/nn.4500)) are adopted here.

### 1.1. First-level Analysis
For the 10 subjects, whole-brain, mass univariate analyses were performed using a general linear model (GLM). The 3 regressors of interest (out of 4 total regressors) were convolved with a spm hemodynamic response function (see Section 2.3 for list). The design matrix (see example in Section 4.1) included both the convolved regressors of interest and 30 nuisance regressors to account for physiological noise and motion-related artifacts (see Section 2.4 for full list).

**Motion Regressors**: Motion parameters included the six rigid-body parameters estimated during motion correction (three translations, three rotations), their temporal derivatives, and the squares of both the parameters and their derivatives, resulting in 24 motion-related regressors.
**Drift Regressors**: Cosine basis functions implemented a high-pass temporal filter with a cutoff of 128 seconds to remove low-frequency drift in the BOLD signal.

**Model Implementation**: All regressors were included in the subject-level first-level General Linear Model (GLM) using FitLins with the Nilearn estimator. The preprocessed (fMRIPrep) BOLD time series were pre-whitened using an autoregressive AR(1) model to correct for temporal autocorrelation. Spatial smoothing was applied with a 5 mm full-width at half maximum (FWHM) Gaussian kernel (isotropic additive smoothing). Each voxel's timeseries was mean-scaled by the voxel's mean signal value following Nilearn's *FirstLevelModel* default procedure.

Each voxel's timeseries (Y) was regressed onto the resulting design matrix (Xβ), which included the regressors and an intercept term . As illustrated in Section 3, 8 linear contrasts were computed

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
trial_type.Finger, trial_type.Foot, trial_type.Lips, intercept

### 2.3 Convolved Regressors
trial_type.Finger, trial_type.Foot, trial_type.Lips

### 2.4 Parametrically Modulated Regressors*
None identified


> **Note:** Parametric regressors are auto-identified by excluding: intercept, constant, trial_type.* and duration-assigned variables from non-nuisance regressors.

### 2.5 Nuisance Regressors
trans_x, trans_x_derivative1, trans_x_derivative1_power2, trans_x_power2, trans_y, trans_y_derivative1, trans_y_derivative1_power2, trans_y_power2, trans_z, trans_z_derivative1, trans_z_derivative1_power2, trans_z_power2, rot_x, rot_x_derivative1, rot_x_derivative1_power2, rot_x_power2, rot_y, rot_y_derivative1, rot_y_derivative1_power2, rot_y_power2, rot_z, rot_z_derivative1, rot_z_derivative1_power2, rot_z_power2, cosine00, cosine01, cosine02, cosine03, cosine04, cosine05

## 3 Contrasts of Interest
- **finger**: 1*`trial_type.Finger`

- **foot**: 1*`trial_type.Foot`

- **lips**: 1*`trial_type.Lips`

- **fingervfoot**: 1*`trial_type.Finger` - 1*`trial_type.Foot`

- **fingervlips**: 1*`trial_type.Finger` - 1*`trial_type.Lips`

- **footvlips**: 1*`trial_type.Foot` - 1*`trial_type.Lips`

- **footlipsvfinger**: 0.5*`trial_type.Foot` + 0.5*`trial_type.Lips` - 1*`trial_type.Finger`

- **fingerlipsvfoot**: 0.5*`trial_type.Finger` + 0.5*`trial_type.Lips` - 1*`trial_type.Foot`


# 4 Figures

## 4.1 Design Matrix
![Design Matrix](./files/ds000114_task-fingerfootlips_design-matrix.svg)

The example design matrix illustrates the model used in the statistical analyses for this task (Note: if motion outliers are included, the number of these will vary between subjects). Each column represents a regressor (of interest or not of interest, based on the above), and each row represents a time point in the BOLD timeseries. The colored patterns show how different experimental conditions are modeled across the scan duration (HRF model).

## 4.2 Contrast Weights
![Contrast Weight](./files/ds000114_task-fingerfootlips_contrast-matrix.svg)

The contrast maps represent the weights used to model brain activity.

## 4.3 Variance Inflation Factor (VIF)
![VIF Distribution](./files/ds000114_task-fingerfootlips_vif-boxplot.png)

The above includes 1) regressor and 2) contrast VIF estimates. The VIF boxplot quantifies multicollinearity between model regressors and how they impact contrasts (for more on contrasts VIFs, see [Dr. Mumford's repo](https://github.com/jmumford/vif_contrasts)).High VIF (e.g., >5 or >10) indicates that collinearity is inflating the variance at a potentially concerning level, which may lead to outliers.  Data should be queried to assess for outliers (e.g. [fmri-outlier-detector](https://github.com/jmumford/fmri-outlier-detector)). VIFs were estimated using the first-level model design matrices -- nusiance regressors are excluded here for brevity.

## 4.4 Voxelwise Model Variance Explained (r-squared)
Voxelwise R-squared values represent the proportion of variance explained by the model at each voxel in the brain. The R-squared images shown here are calculated across runs, subjects and/or sessions (dependent on data BIDS Stats Model nodes) for the study and task.

### 4.4.1 Voxelwise Average (Mean)
The **mean** R-squared image reflect the average of the R-squared values across all subjects and runs.In other words, the fluctuation in how much variability in the BOLD signal the model explains at a given voxel.
![R Square](./files/ds000114_task-fingerfootlips_rsquare-mean.png)

### 4.4.2 Voxelwise Variance (Standard Deviation)
The **standard deviation** (or variance) image provides insights into the variability of model performance.In otherwords, across subjects, runs and/or sessions, how much variability there is in the models ability to explain the BOLD at a given voxel.

#### 4.4.3 Flagged Subjects
The quality assessment pipeline evaluates volumetric data across multiple dimensions to identify problematic datasets. Subjects are flagged using: 

  - Dice Estimate: Similarity coefficient between subject r-squared maps and Target Space MNI152 mask falls below .80 (captures dropout and excess non-brain voxels) 
  - Voxels Outside of Mask: Percentage of voxels outside of the target brain mask is greater than the .10% (liberal threshold due to liberal brain masks in fMRIPrep BOLD, captures mostly non-brain voxels) 

The subjects flagged for fingerfootlips are:
sub-01_ses-retest, sub-01_ses-test, sub-02_ses-retest, sub-02_ses-test, sub-03_ses-retest, sub-03_ses-test, sub-04_ses-retest, sub-04_ses-test, sub-05_ses-retest, sub-05_ses-test, sub-06_ses-retest, sub-06_ses-test, sub-07_ses-retest, sub-07_ses-test, sub-08_ses-retest, sub-08_ses-test, sub-09_ses-retest, sub-09_ses-test, sub-10_ses-retest

The distribution for subjects and runs in fingerfootlips are below. 

![Dice](./files/ds000114_task-fingerfootlips_hist-dicesimilarity.png)
![Voxels Out](./files/ds000114_task-fingerfootlips_hist-voxoutmask.png)

## 5 Statistical Maps

### finger

#### ses-test
![finger ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-finger_map.png)

#### ses-retest
![finger ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-finger_map.png)

### foot

#### ses-test
![foot ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-foot_map.png)

#### ses-retest
![foot ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-foot_map.png)

### lips

#### ses-test
![lips ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-lips_map.png)

#### ses-retest
![lips ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-lips_map.png)

### fingervfoot

#### ses-test
![fingervfoot ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-fingervfoot_map.png)

#### ses-retest
![fingervfoot ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-fingervfoot_map.png)

### fingervlips

#### ses-test
![fingervlips ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-fingervlips_map.png)

#### ses-retest
![fingervlips ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-fingervlips_map.png)

### footvlips

#### ses-test
![footvlips ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-footvlips_map.png)

#### ses-retest
![footvlips ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-footvlips_map.png)

### footlipsvfinger

#### ses-test
![footlipsvfinger ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-footlipsvfinger_map.png)

#### ses-retest
![footlipsvfinger ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-footlipsvfinger_map.png)

### fingerlipsvfoot

#### ses-test
![fingerlipsvfoot ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-fingerlipsvfoot_map.png)

#### ses-retest
![fingerlipsvfoot ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-fingerlipsvfoot_map.png)
