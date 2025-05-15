# ds004556: feedback Task Analysis Report

The size of the Fitlins Derivatives for ds004556 feedback is 4.5G with 2912 files.

## Statistical Analysis Boilerplate

### First-level Analysis
FitLins was employed to estimate task-related BOLD activity in the feedback task for 53 subjects. In this instance, FitLins used the Nilearn estimator in its statistical modeling of the BOLD data. For each participant, 6 regressors of interest (out of total 8 regressors; see list below) were convolved with a spm hemodynamic response function in Nilearn. The design matrix incorporated both regressors of interest and 32 additional components, including a drift cosine basis set and nuisance regressors to account for sources of noise in the BOLD signal. Following Nilearn's *FirstLevelModel* default procedure, each voxel's timeseries was mean-scaled by each voxel's mean of the timeseries. Data were smoothed at each run using a 5mm full-width at half maximum smoothing kernal (default: isotropic additive smoothing). From the resulting model, 8 distinct contrast estimates were computed (see list below).

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
trial_type.control_moving_bars, trial_type.fixation_cross, trial_type.instruction, trial_type.rating, trial_type.watch_moving_bars, trial_type.watch_static_bars, rating, intercept
#### Convolved Regressors
trial_type.control_moving_bars, trial_type.fixation_cross, trial_type.instruction, trial_type.rating, trial_type.watch_moving_bars, trial_type.watch_static_bars
### Nuisance Regressors
trans_x, trans_x_derivative1, trans_x_derivative1_power2, trans_x_power2, trans_y, trans_y_derivative1, trans_y_derivative1_power2, trans_y_power2, trans_z, trans_z_derivative1, trans_z_derivative1_power2, trans_z_power2, rot_x, rot_x_derivative1, rot_x_derivative1_power2, rot_x_power2, rot_y, rot_y_derivative1, rot_y_derivative1_power2, rot_y_power2, rot_z, rot_z_derivative1, rot_z_derivative1_power2, rot_z_power2, cosine00, cosine01, cosine02, cosine03, cosine04, cosine05, cosine06, cosine07
## Model Structure
- Run-level models: Yes
- Subject-level models: No

## Contrasts of Interest
- **barstaticvmoving**: 1*`trial_type.watch_static_bars` - 1*`trial_type.watch_moving_bars`
- **barcontrolvmoving**: 1*`trial_type.control_moving_bars` - 1*`trial_type.watch_moving_bars`
- **barcontrolvstatic**: 1*`trial_type.control_moving_bars` - 1*`trial_type.watch_static_bars`
- **barcontrolvstaticmoving**: 1*`trial_type.control_moving_bars` - 0.5*`trial_type.watch_static_bars` - 0.5*`trial_type.watch_moving_bars`
- **allbarsvfixation**: 0.333*`trial_type.control_moving_bars` + 0.333*`trial_type.watch_static_bars` + 0.333*`trial_type.watch_moving_bars` - 1*`trial_type.fixation_cross`
- **ratingvfixation**: 1*`trial_type.rating` - 1*`trial_type.fixation_cross`
- **instructionvfixation**: 1*`trial_type.instruction` - 1*`trial_type.fixation_cross`
- **rate**: 1*`rating`

## Figures

### Contrast Weights
![Contrast Weight](./files/ds004556_task-feedback_contrast-matrix.svg)

The contrast maps represents the weights used to model brain activity.

### Design Matrix
![Design Matrix](./files/ds004556_task-feedback_design-matrix.svg)

The example design matrix illustrates the model used in the statistical analyses for this task (Note: if motion outliers are included, the number of these will vary between subjects). Each column represents a regressor (of interest or not of interest, based on the above), and each row represents a time point in the BOLD timeseries. The colored patterns show how different experimental conditions are modeled across the scan duration (HRF model).

### Variance Inflation Factor (VIF)
![VIF Distribution](./files/ds004556_task-feedback_vif-boxplot.png)

The above includes 1) regressor and 2) contrast VIF estimates. The VIF boxplot quantifies multicollinearity between model regressors and how they impact contrasts (for more on contrasts VIFs, see [Dr. Mumford's repo](https://github.com/jmumford/vif_contrasts)). Lower VIF values indicate more statistically independent regressors, which is desirable for reliable parameter estimation. VIFs were estimated using the first-level model design matrices -- nusiance regressors are excluded here for brevity.

### Voxelwise Model Variance Explained (r-squared)
Voxelwise R-squared values represent the proportion of variance explained by the model at each voxel in the brain. The R-squared images shown here are calculated across runs, subjects and/or sessions (dependent on data Fitlins nodes) for the study and task.

#### Voxelwise Average (Mean)
The **mean** R-squared image reflect the average of the R-squared values across all subjects and runs.In other words, the fluctuation in how much variability in the BOLD signal the model explains at a given voxel.
![R Square](./files/ds004556_task-feedback_rsquare-mean.png)

#### Voxelwise Variance (Standard Deviation)
The **standard deviation** (or variance) image provides insights into the variability of model performance.In otherwords, across subjects, runs and/or sessions, how much variability there is in the models ability to explain the BOLD at a given voxel.

#### Flagged Subjects
The quality assessment pipeline evaluates volumetric data across multiple dimensions to identify problematic datasets. Subjects are flagged using: 

  - Dice Estimate: Similarity coefficient between subject r-squared maps and Target Space MNI152 mask falls below .80 (captures dropout and excess non-brain voxels) 
  - Voxels Outside of Mask: Percentage of voxels outside of the target brain mask is greater than the .10% (liberal threshold due to liberal brain masks in fMRIPrep BOLD, captures mostly non-brain voxels) 

The subjects flagged for feedback are:
None Subjects Flagged

The distribution for subjects and runs in feedback are below. 

![Dice](./files/ds004556_task-feedback_hist-dicesimilarity.png)
![Voxels Out](./files/ds004556_task-feedback_hist-voxoutmask.png)

### Statistical Maps

#### barstaticvmoving
![barstaticvmoving Map](./files/ds004556_task-feedback_contrast-barstaticvmoving_map.png)

#### barcontrolvmoving
![barcontrolvmoving Map](./files/ds004556_task-feedback_contrast-barcontrolvmoving_map.png)

#### barcontrolvstatic
![barcontrolvstatic Map](./files/ds004556_task-feedback_contrast-barcontrolvstatic_map.png)

#### barcontrolvstaticmoving
![barcontrolvstaticmoving Map](./files/ds004556_task-feedback_contrast-barcontrolvstaticmoving_map.png)

#### allbarsvfixation
![allbarsvfixation Map](./files/ds004556_task-feedback_contrast-allbarsvfixation_map.png)

#### ratingvfixation
![ratingvfixation Map](./files/ds004556_task-feedback_contrast-ratingvfixation_map.png)

#### instructionvfixation
![instructionvfixation Map](./files/ds004556_task-feedback_contrast-instructionvfixation_map.png)

#### rate
![rate Map](./files/ds004556_task-feedback_contrast-rate_map.png)
