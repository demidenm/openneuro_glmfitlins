[![OpenNeuro ID](https://img.shields.io/badge/OpenNeuro_Dataset-ds000002-blue?style=for-the-badge)](https://openneuro.org/datasets/ds000002)

# Dataset Details: ds000002

## Number of Subjects
- BIDS Input: 17

## Tasks and Trial Types
### Task: deterministicclassification
- **Column Names**: onset, duration, trial_type, feedback, TrialNum, StimCond, StimulusNum, Response, response_time, Correct, Feedback
- **Data Types**: onset (float64), duration (float64), trial_type (object), feedback (float64), TrialNum (float64), StimCond (float64), StimulusNum (float64), Response (object), response_time (float64), Correct (object), Feedback (object)
- **BOLD Volumes**: 180
- **Unique 'trial_type' Values**: feedback, nan

### Task: mixedeventrelatedprobe
- **Column Names**: onset, duration, trial_type, TrialNum, StimCond, StimulusNum, Response, response_time, Correct
- **Data Types**: onset (float64), duration (float64), trial_type (object), TrialNum (float64), StimCond (float64), StimulusNum (float64), Response (object), response_time (float64), Correct (float64)
- **BOLD Volumes**: 237
- **Unique 'trial_type' Values**: classification-probabilistic, classification-deterministic, nan

### Task: probabilisticclassification
- **Column Names**: onset, duration, trial_type, feedback, TrialNum, StimCond, StimulusNum, Response, response_time, Correct, Feedback
- **Data Types**: onset (float64), duration (float64), trial_type (object), feedback (float64), TrialNum (float64), StimCond (float64), StimulusNum (float64), Response (object), response_time (float64), Correct (object), Feedback (object)
- **BOLD Volumes**: 180
- **Unique 'trial_type' Values**: feedback, nan

## MRIQC Summary Reports
- [group_T1w.html](https://htmlpreview.github.io/?https://github.com/demidenm/openneuro_glmfitlins/blob/main/statsmodel_specs/ds000002/mriqc_summary/group_T1w.html)
- [group_bold.html](https://htmlpreview.github.io/?https://github.com/demidenm/openneuro_glmfitlins/blob/main/statsmodel_specs/ds000002/mriqc_summary/group_bold.html)
