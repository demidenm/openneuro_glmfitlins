# ds000108: Emotionregulation Task Analysis Report
## Analysis Overview
Subject-level models were fit for 30 subjects performing the Emotionregulation task.
HRF model type: spm
### Regressors of Interest
trial_type.Look_Neg_Ant, trial_type.Look_Neg_Cue, trial_type.Look_Neg_Rating, trial_type.Look_Neg_Stim, trial_type.Look_Neutral_Ant, trial_type.Look_Neutral_Cue, trial_type.Look_Neutral_Rating, trial_type.Look_Neutral_Stim, trial_type.Reapp_Neg_Ant, trial_type.Reapp_Neg_Cue, trial_type.Reapp_Neg_Rating, trial_type.Reapp_Neg_Stim, intercept
### Nuisance Regressors
trans_x, trans_x_derivative1, trans_x_derivative1_power2, trans_x_power2, trans_y, trans_y_derivative1, trans_y_derivative1_power2, trans_y_power2, trans_z, trans_z_derivative1, trans_z_derivative1_power2, trans_z_power2, rot_x, rot_x_derivative1, rot_x_derivative1_power2, rot_x_power2, rot_y, rot_y_derivative1, rot_y_derivative1_power2, rot_y_power2, rot_z, rot_z_derivative1, rot_z_derivative1_power2, rot_z_power2, cosine00, cosine01, cosine02, cosine03, cosine04
## Model Structure
- Run-level models: Yes
- Subject-level models: Yes

The run-wise contrast estimates for each subject are averaged using a fixed-effects model.
## Contrasts of Interest
- **StimReappNegvLookNeg**: ['1 * `trial_type.Reapp_Neg_Stim` - 1 * `trial_type.Look_Neg_Stim`']
- **StimLookNegvNeutral**: ['1 * `trial_type.Look_Neg_Stim` - 1 * `trial_type.Look_Neutral_Stim`']
- **StimReappvLookNegNeut**: ['1 * `trial_type.Reapp_Neg_Stim` - 0.5 * `trial_type.Look_Neg_Stim` - 0.5 * `trial_type.Look_Neutral_Stim`']
- **StimReappNeg**: ['1 * `trial_type.Reapp_Neg_Stim`']
- **StimLookNeg**: ['1 * `trial_type.Look_Neg_Stim`']
- **StimLookNeutral**: ['1 * `trial_type.Look_Neutral_Stim`']
- **StimPhase**: ['0.33 * `trial_type.Look_Neg_Stim` + 0.33 * `trial_type.Reapp_Neg_Stim` + 0.33 * `trial_type.Look_Neutral_Stim`']
- **AntPhase**: ['0.33 * `trial_type.Look_Neg_Ant` + 0.33 * `trial_type.Reapp_Neg_Ant` + 0.33 * `trial_type.Look_Neutral_Ant`']
- **RatePhase**: ['0.33 * `trial_type.Look_Neg_Rating` + 0.33 * `trial_type.Reapp_Neg_Rating` + 0.33 * `trial_type.Look_Neutral_Rating`']

## Figures

### Contrast Weights
![Contrast Weight](./imgs/ds000108_task-Emotionregulation_contrast-matrix.svg)
The contrast maps represents the weights used to model brain activity.

### Design Matrixs
![Design Matrix](./imgs/ds000108_task-Emotionregulation_design-matrix.svg)
The example design matrix illustrate the model used in the statistical analyses for this task (Note: if motion outliers are included, the number of these will vary between subjects). Each column represents a regressor (of interest or not of interested, based on the above), and each row represents a time point in the BOLD timeseries. The colored patterns show how different experimental conditions are modeled across the scan duration (HRF model).

### Variance Inflation Factor (VIF)
![VIF Distribution](./imgs/ds000108_task-Emotionregulation_vif-boxplot.png)
The Variance Inflation Factor (VIF) boxplot quantifies multicollinearity between model regressors. Lower VIF values indicate more statistically independent regressors, which is desirable for reliable parameter estimation. VIFs were estimated using the design matrices -- nusiance regressors are excluded here for brevity.

### Voxelwise Model Variance Explained (r-squared)
Voxelwise R-squared values represent the proportion of variance explained by the model at each voxel in the brain. The R-squared images shown here are calculated across runs, subjects and/or sessions (dependent on data Fitlins nodes) for the study and task.

#### Voxelwise Average (Mean)
The **mean** R-squared image reflect the average of the R-squared values across all subjects and runs.In other words, the fluctuation in how much variability in the BOLD signal the model explains at a given voxel.
![R Square](./imgs/ds000108_task-Emotionregulation_rsquare-mean.png)

#### Voxelwise Variance (Standard Deviation)
The **standard deviation** (or variance) image provides insights into the variability of model performance.In otherwords, across subjects, runs and/or sessions, how much variability there is in the models ability to explain the BOLD at a given voxel.
![R Square](./imgs/ds000108_task-Emotionregulation_rsquare-std.png)

### Statistical Maps

#### StimReappNegvLookNeg
![StimReappNegvLookNeg Map](./imgs/ds000108_task-Emotionregulation_contrast-StimReappNegvLookNeg_map.png)

#### StimLookNegvNeutral
![StimLookNegvNeutral Map](./imgs/ds000108_task-Emotionregulation_contrast-StimLookNegvNeutral_map.png)

#### StimReappvLookNegNeut
![StimReappvLookNegNeut Map](./imgs/ds000108_task-Emotionregulation_contrast-StimReappvLookNegNeut_map.png)

#### StimReappNeg
![StimReappNeg Map](./imgs/ds000108_task-Emotionregulation_contrast-StimReappNeg_map.png)

#### StimLookNeg
![StimLookNeg Map](./imgs/ds000108_task-Emotionregulation_contrast-StimLookNeg_map.png)

#### StimLookNeutral
![StimLookNeutral Map](./imgs/ds000108_task-Emotionregulation_contrast-StimLookNeutral_map.png)

#### StimPhase
![StimPhase Map](./imgs/ds000108_task-Emotionregulation_contrast-StimPhase_map.png)

#### AntPhase
![AntPhase Map](./imgs/ds000108_task-Emotionregulation_contrast-AntPhase_map.png)

#### RatePhase
![RatePhase Map](./imgs/ds000108_task-Emotionregulation_contrast-RatePhase_map.png)
