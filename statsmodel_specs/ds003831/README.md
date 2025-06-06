[![OpenNeuro ID](https://img.shields.io/badge/OpenNeuro_Dataset-ds003831-blue?style=for-the-badge)](https://openneuro.org/datasets/ds003831)

# Dataset Details: ds003831

## Number of Subjects
- BIDS Input: 74

## Tasks and Trial Types
### Task: identify1
- **Column Names**: onset, duration, dsgn_onset, dsgn_duration, trial_type, database, identifier, valence, arousal
- **Data Types**: onset (float64), duration (float64), dsgn_onset (float64), dsgn_duration (float64), trial_type (object), database (object), identifier (float64), valence (float64), arousal (float64)
- **BOLD Volumes**: 282
- **Unique 'trial_type' Values**: ex_stim, in_stim, in_prep, in_feel

### Task: identify2
- **Column Names**: onset, duration, dsgn_onset, dsgn_duration, trial_type, database, identifier, valence, arousal
- **Data Types**: onset (float64), duration (float64), dsgn_onset (float64), dsgn_duration (float64), trial_type (object), database (object), identifier (float64), valence (float64), arousal (float64)
- **BOLD Volumes**: 282
- **Unique 'trial_type' Values**: in_stim, in_prep, in_feel, ex_stim

### Task: modulate1
- **Column Names**: onset, duration, trial_type, fb_valence, fb_arousal
- **Data Types**: onset (float64), duration (float64), trial_type (object), fb_valence (float64), fb_arousal (float64)
- **BOLD Volumes**: 310
- **Unique 'trial_type' Values**: rest, fb_v_pos, feel, fb_a_pos, fb_v_neg, fb_a_neg, finish

### Task: modulate2
- **Column Names**: onset, duration, trial_type, fb_valence, fb_arousal
- **Data Types**: onset (float64), duration (float64), trial_type (object), fb_valence (float64), fb_arousal (float64)
- **BOLD Volumes**: 310
- **Unique 'trial_type' Values**: rest, fb_a_neg, feel, fb_v_pos, fb_a_pos, fb_v_neg, finish

## MRIQC Summary Reports
- [group_T1w.html](https://htmlpreview.github.io/?https://github.com/demidenm/openneuro_glmfitlins/blob/main/statsmodel_specs/ds003831/mriqc_summary/group_T1w.html)
- [group_bold.html](https://htmlpreview.github.io/?https://github.com/demidenm/openneuro_glmfitlins/blob/main/statsmodel_specs/ds003831/mriqc_summary/group_bold.html)


>Note: Error running `modulate2` task, given below fitlins error despite presence of files when piloting transformation history in notebook. Needs review.

```bash
"*/bids/variables/collections.py", line 263, in __getitem__
    raise ValueError(
        ValueError: No variable named 'trial_type' found in this collection
```