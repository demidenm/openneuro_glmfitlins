[![OpenNeuro ID](https://img.shields.io/badge/OpenNeuro_Dataset-ds000009-blue?style=for-the-badge)](https://openneuro.org/datasets/ds000009)

# Dataset Details: ds000009

## Number of Subjects
- BIDS Input: 24

## Tasks and Trial Types
### Task: balloonanalogrisktask
- **Column Names**: onset, duration, reaction_time, trial_number, trial_type, button_pressed, action, explode_trial, trial_value, trial_cumulative_value, payoff_level, onset_orig, duration_orig, trial_type_orig
- **Data Types**: onset (float64), duration (int64), reaction_time (float64), trial_number (int64), trial_type (object), button_pressed (object), action (object), explode_trial (int64), trial_value (float64), trial_cumulative_value (float64), payoff_level (float64), onset_orig (float64), duration_orig (float64), trial_type_orig (object)
- **BOLD Volumes**: 245
- **Unique 'trial_type' Values**: BALOON

### Task: discounting
- **Column Names**: onset, duration, reaction_time, percent_off_trial, trial_type, immediate_amount, delayed_amount, delay_time_words, delay_time_days, k_this_trial, response_button, response_binarized, onset.plus.rt, onset.plus.stimdur, absolute_time, trialnum, onset_orig, duration_orig, trial_type_orig, easy_par_orig, hard_par_orig
- **Data Types**: onset (float64), duration (float64), reaction_time (float64), percent_off_trial (float64), trial_type (object), immediate_amount (int64), delayed_amount (float64), delay_time_words (object), delay_time_days (int64), k_this_trial (float64), response_button (object), response_binarized (int64), onset.plus.rt (float64), onset.plus.stimdur (float64), absolute_time (float64), trialnum (int64), onset_orig (float64), duration_orig (float64), trial_type_orig (object), easy_par_orig (float64), hard_par_orig (float64)
- **BOLD Volumes**: 293
- **Unique 'trial_type' Values**: easy_par, hard_par

### Task: emotionalregulation
- **Column Names**: onset, duration, trial_type, image_type, image_num, response, reaction_time, trial_num, onset_orig, duration_orig, trial_type_orig, rating_par_orig
- **Data Types**: onset (float64), duration (int64), trial_type (object), image_type (object), image_num (float64), response (float64), reaction_time (float64), trial_num (int64), onset_orig (float64), duration_orig (float64), trial_type_orig (object), rating_par_orig (float64)
- **BOLD Volumes**: 200
- **Unique 'trial_type' Values**: attend, rate, suppress

### Task: stopsignal
- **Column Names**: onset, duration, trial_type, PresentedStimulusArrowDirection, ReactionTime, SubjectResponseButton, SubjectResponseButtonCode, SubjectResponseCorrectness, TrialOutcome, StopSignalDelay, LadderNumber, LadderTime, LadderMovement, TimeCourse, onset_orig, duration_orig, trial_type_orig
- **Data Types**: onset (float64), duration (float64), trial_type (object), PresentedStimulusArrowDirection (object), ReactionTime (float64), SubjectResponseButton (object), SubjectResponseButtonCode (int64), SubjectResponseCorrectness (object), TrialOutcome (object), StopSignalDelay (float64), LadderNumber (int64), LadderTime (int64), LadderMovement (int64), TimeCourse (float64), onset_orig (float64), duration_orig (float64), trial_type_orig (object)
- **BOLD Volumes**: 184
- **Unique 'trial_type' Values**: STOP, GO

## MRIQC Summary Reports
- [group_T1w.html](https://htmlpreview.github.io/?https://github.com/demidenm/openneuro_glmfitlins/blob/main/statsmodel_specs/ds000009/mriqc_summary/group_T1w.html)
- [group_bold.html](https://htmlpreview.github.io/?https://github.com/demidenm/openneuro_glmfitlins/blob/main/statsmodel_specs/ds000009/mriqc_summary/group_bold.html)
