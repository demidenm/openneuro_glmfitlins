"""Event fixes for ds003858."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds003858")
def ds003858(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds003858 baed on timings in 10.1016/j.neuroimage.2021.118617 as events files insufficient for model of MID
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    

    if task in ["MID"]:
        eventsdat = events_df.copy()

        #  if columns not present
        if not eventsdat['trial_type'].isin(['cue_neutral', 'probe', 'fix_neutral']).any():

            def get_condition_type(trial_type):
                """
                Convert trial_type to condition category
                """
                if trial_type in ['+$5', '$5']:
                    return 'largewin'
                elif trial_type in ['+$1', '$1']:
                    return 'smallwin'
                elif trial_type in ['+$0', '$0', '-$0']:
                    return 'neutral'
                elif trial_type in ['-$1', '($1)']:
                    return 'smallloss'
                elif trial_type in ['-$5', '($5)']:
                    return 'largeloss'


            def get_feedback_type(trial_type, hit):
                """
                Create feedback condition based on trial type and hit/miss
                """
                condition = get_condition_type(trial_type)
                hit_miss = 'hit' if hit == 1 else 'miss'
                return f"fb_{condition}{hit_miss}"

            # use functions to iterate and create events df
            components = []

            for idx, row in eventsdat.iterrows():
                trial_onset = row['onset']
                trial_num = row['trial']
                trial_type = row['trial_type']
                iti_duration = row['iti']
                hit_status = row['hit']
                
                # Get condition type for cue and fixation
                condition = get_condition_type(trial_type)
                
                # Get feedback type based on hit/miss
                feedback_condition = get_feedback_type(trial_type, hit_status)
                
                # Cue presentation (0-2 seconds)
                components.append({
                    'trial': trial_num,
                    'trial_type': f'cue_{condition}',
                    'component': 'cue',
                    'onset': trial_onset,
                    'duration': 2.0,
                    'end_time': trial_onset + 2.0
                })
                
                # Anticipatory fixation (2-4 seconds)
                components.append({
                    'trial': trial_num,
                    'trial_type': f'fix_{condition}',
                    'component': 'fixation',
                    'onset': trial_onset + 2.0,
                    'duration': 2.0,
                    'end_time': trial_onset + 4.0
                })
                
                # Target/probe (4-4.5 seconds)
                components.append({
                    'trial': trial_num,
                    'trial_type': 'probe',
                    'component': 'probe',
                    'onset': trial_onset + 4.0,
                    'duration': 0.5,
                    'end_time': trial_onset + 4.5,
                    'target_time': row['target_s'],  # actual target appearance within window
                    'response_time': row['response_time'],
                    'hit': row['hit']
                })
                
                # feedback presentation (6-8 seconds)
                components.append({
                    'trial': trial_num,
                    'trial_type': feedback_condition,
                    'component': 'feedback',
                    'onset': trial_onset + 6.0,
                    'duration': 2.0,
                    'end_time': trial_onset + 8.0,
                    'total_gain': row['total_gain']
                })
                
                # Inter-trial interval (ITI dur)
                components.append({
                    'trial': trial_num,
                    'trial_type': 'iti',
                    'component': 'iti',
                    'onset': trial_onset + 8.0,
                    'duration': iti_duration,
                    'end_time': trial_onset + 8.0 + iti_duration
                })

            eventsdat_rev = pd.DataFrame(components)
            print("Colnames:", eventsdat_rev.columns)

            return eventsdat_rev
        else:
            print("Columns present. Skipping modification.")
            return None
