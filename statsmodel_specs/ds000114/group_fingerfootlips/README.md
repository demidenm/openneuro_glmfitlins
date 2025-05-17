# ds000114: fingerfootlips Task Analysis Report

The size of the Fitlins Derivatives for ds000114 fingerfootlips is 1.7G with 1178 files.

## Statistical Analysis Boilerplate

### First-level Analysis
FitLins was employed to estimate task-related BOLD activity in the fingerfootlips task for 10 subjects. In this instance, FitLins used the Nilearn estimator in its statistical modeling of the BOLD data. For each participant, 3 regressors of interest (out of total 4 regressors; see list below) were convolved with a spm hemodynamic response function in Nilearn. The design matrix incorporated both regressors of interest and 30 additional components, including a drift cosine basis set and nuisance regressors to account for sources of noise in the BOLD signal. Following Nilearn's *FirstLevelModel* default procedure, each voxel's timeseries was mean-scaled by each voxel's mean of the timeseries. Data were smoothed at each run using a 5mm full-width at half maximum smoothing kernal (default: isotropic additive smoothing). From the resulting model, 8 distinct contrast estimates were computed (see list below).

### Model Outputs
For each participant's run, outputs include but are not limited to:
- A complete design matrix visualization
- Model fit statistics (R-squared and log-likelihood maps)
- For each contrast: effect size maps (beta values), t-statistic maps, z-statistic maps and variance maps

An example design matrix and contrast weight specifications are provided below.

### Group-level Analysis
Subject-level statistical maps were entered directly into a group-level analysis using a two-sided one-sample t-test to to estimate average univariate activation patterns.

## Additional Analysis Details 
### Regressors of Interest
trial_type.Finger, trial_type.Foot, trial_type.Lips, intercept
#### Convolved Regressors
trial_type.Finger, trial_type.Foot, trial_type.Lips
### Nuisance Regressors
trans_x, trans_x_derivative1, trans_x_derivative1_power2, trans_x_power2, trans_y, trans_y_derivative1, trans_y_derivative1_power2, trans_y_power2, trans_z, trans_z_derivative1, trans_z_derivative1_power2, trans_z_power2, rot_x, rot_x_derivative1, rot_x_derivative1_power2, rot_x_power2, rot_y, rot_y_derivative1, rot_y_derivative1_power2, rot_y_power2, rot_z, rot_z_derivative1, rot_z_derivative1_power2, rot_z_power2, cosine00, cosine01, cosine02, cosine03, cosine04, cosine05
## Model Structure
- Run-level models: Yes
- Subject-level models: No

## Contrasts of Interest
- **finger**: 1*`trial_type.Finger`
- **foot**: 1*`trial_type.Foot`
- **lips**: 1*`trial_type.Lips`
- **fingervfoot**: 1*`trial_type.Finger` - 1*`trial_type.Foot`
- **fingervlips**: 1*`trial_type.Finger` - 1*`trial_type.Lips`
- **footvlips**: 1*`trial_type.Foot` - 1*`trial_type.Lips`
- **footlipsvfinger**: 0.5*`trial_type.Foot` + 0.5*`trial_type.Lips` - 1*`trial_type.Finger`
- **fingerlipsvfoot**: 0.5*`trial_type.Finger` + 0.5*`trial_type.Lips` - 1*`trial_type.Foot`

## Figures

### Contrast Weights
![Contrast Weight](./files/ds000114_task-fingerfootlips_contrast-matrix.svg)

The contrast maps represents the weights used to model brain activity.

### Design Matrix
![Design Matrix](./files/ds000114_task-fingerfootlips_design-matrix.svg)

The example design matrix illustrates the model used in the statistical analyses for this task (Note: if motion outliers are included, the number of these will vary between subjects). Each column represents a regressor (of interest or not of interest, based on the above), and each row represents a time point in the BOLD timeseries. The colored patterns show how different experimental conditions are modeled across the scan duration (HRF model).

### Variance Inflation Factor (VIF)
![VIF Distribution](./files/ds000114_task-fingerfootlips_vif-boxplot.png)

The above includes 1) regressor and 2) contrast VIF estimates. The VIF boxplot quantifies multicollinearity between model regressors and how they impact contrasts (for more on contrasts VIFs, see [Dr. Mumford's repo](https://github.com/jmumford/vif_contrasts)). Lower VIF values indicate more statistically independent regressors, which is desirable for reliable parameter estimation. VIFs were estimated using the first-level model design matrices -- nusiance regressors are excluded here for brevity.

### Voxelwise Model Variance Explained (r-squared)
Voxelwise R-squared values represent the proportion of variance explained by the model at each voxel in the brain. The R-squared images shown here are calculated across runs, subjects and/or sessions (dependent on data Fitlins nodes) for the study and task.

#### Voxelwise Average (Mean)
The **mean** R-squared image reflect the average of the R-squared values across all subjects and runs.In other words, the fluctuation in how much variability in the BOLD signal the model explains at a given voxel.
![R Square](./files/ds000114_task-fingerfootlips_rsquare-mean.png)

#### Voxelwise Variance (Standard Deviation)
The **standard deviation** (or variance) image provides insights into the variability of model performance.In otherwords, across subjects, runs and/or sessions, how much variability there is in the models ability to explain the BOLD at a given voxel.

#### Flagged Subjects
The quality assessment pipeline evaluates volumetric data across multiple dimensions to identify problematic datasets. Subjects are flagged using: 

  - Dice Estimate: Similarity coefficient between subject r-squared maps and Target Space MNI152 mask falls below .80 (captures dropout and excess non-brain voxels) 
  - Voxels Outside of Mask: Percentage of voxels outside of the target brain mask is greater than the .10% (liberal threshold due to liberal brain masks in fMRIPrep BOLD, captures mostly non-brain voxels) 

The subjects flagged for fingerfootlips are:
sub-01_ses-retest, sub-01_ses-test, sub-02_ses-retest, sub-02_ses-test, sub-03_ses-retest, sub-03_ses-test, sub-04_ses-retest, sub-04_ses-test, sub-05_ses-retest, sub-05_ses-test, sub-06_ses-retest, sub-06_ses-test, sub-07_ses-retest, sub-07_ses-test, sub-08_ses-retest, sub-08_ses-test, sub-09_ses-retest, sub-09_ses-test, sub-10_ses-retest

The distribution for subjects and runs in fingerfootlips are below. 

![Dice](./files/ds000114_task-fingerfootlips_hist-dicesimilarity.png)
![Voxels Out](./files/ds000114_task-fingerfootlips_hist-voxoutmask.png)

### Statistical Maps

#### finger

##### ses-test
![finger ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-finger_map.png)

##### ses-retest
![finger ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-finger_map.png)

#### foot

##### ses-test
![foot ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-foot_map.png)

##### ses-retest
![foot ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-foot_map.png)

#### lips

##### ses-test
![lips ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-lips_map.png)

##### ses-retest
![lips ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-lips_map.png)

#### fingervfoot

##### ses-test
![fingervfoot ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-fingervfoot_map.png)

##### ses-retest
![fingervfoot ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-fingervfoot_map.png)

#### fingervlips

##### ses-test
![fingervlips ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-fingervlips_map.png)

##### ses-retest
![fingervlips ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-fingervlips_map.png)

#### footvlips

##### ses-test
![footvlips ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-footvlips_map.png)

##### ses-retest
![footvlips ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-footvlips_map.png)

#### footlipsvfinger

##### ses-test
![footlipsvfinger ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-footlipsvfinger_map.png)

##### ses-retest
![footlipsvfinger ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-footlipsvfinger_map.png)

#### fingerlipsvfoot

##### ses-test
![fingerlipsvfoot ses-test Map](./files/ds000114_task-fingerfootlips_ses-test_contrast-fingerlipsvfoot_map.png)

##### ses-retest
![fingerlipsvfoot ses-retest Map](./files/ds000114_task-fingerfootlips_ses-retest_contrast-fingerlipsvfoot_map.png)
