[![OpenNeuro ID](https://img.shields.io/badge/OpenNeuro_Dataset-ds000008-blue?style=for-the-badge)](https://openneuro.org/datasets/ds000008)

# Dataset Details: ds000008

## Number of Subjects
- BIDS Input: 14

## Tasks and Trial Types
### Task: conditionalstopsignal
- **Column Names**: onset, duration, trial_type, TrialType, Stimulus, SSD, Response, response_time, CorrectGo, SuccStop
- **Data Types**: onset (float64), duration (float64), trial_type (object), TrialType (int64), Stimulus (int64), SSD (float64), Response (int64), response_time (float64), CorrectGo (int64), SuccStop (int64)
- **BOLD Volumes**: 176
- **Unique 'trial_type' Values**: failed stop-critical, go-noncritical, go-critical, successful stop-critical, junk, failed stop-noncritical

### Task: stopsignal
- **Column Names**: onset, duration, trial_type, TrialType, Stimulus, SSD, Response, response_time, CorrectGo, SuccStop
- **Data Types**: onset (float64), duration (float64), trial_type (object), TrialType (float64), Stimulus (float64), SSD (float64), Response (float64), response_time (float64), CorrectGo (float64), SuccStop (float64)
- **BOLD Volumes**: 182
- **Unique 'trial_type' Values**: nan, go, failed stop, successful stop, junk

## MRIQC Summary Reports
- [group_T1w.html](https://htmlpreview.github.io/?https://github.com/demidenm/openneuro_glmfitlins/blob/main/statsmodel_specs/ds000008/mriqc_summary/group_T1w.html)
- [group_bold.html](https://htmlpreview.github.io/?https://github.com/demidenm/openneuro_glmfitlins/blob/main/statsmodel_specs/ds000008/mriqc_summary/group_bold.html)
