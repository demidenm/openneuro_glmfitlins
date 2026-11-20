"""Event fixes for ds005012."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds005012")
def ds005012(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds005012 by reformating timing values into BIDS standard to run the models
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): Task name for dataset 
    
    Returns:
    pd.DataFrame or None
        Modified events DataFrame, or None if no updates were applied.
    """

    eventsdat = events_df.copy()
    eventsdat['trial'] = range(1, len(eventsdat) + 1)
    eventsdat['condition'] = eventsdat['TRIAL_TYPE']

    if task.lower() == "mid":
        # apply modifications if not already present
        if not {'trial_type', 'condition', 'trial', 'accuracy', 'response_time', 'result_words','result_reason'}.issubset(eventsdat.columns):
            
            bids_events = []

            # Fixed: Use eventsdat instead of df
            for idx, row in eventsdat.iterrows():
                # Handle missing trial column - use index if not present
                trial_num = row.get('trial', idx)  # Use index if 'trial' column doesn't exist
                
                # Extract condition from original data structure
                # You may need to adjust this based on your actual column names
                condition = row.get('TRIAL_TYPE', row.get('condition', 'unknown'))
                probe_hit = row.get('PROBE_HIT', 0)
                
                # Cue 
                cue_event = {
                    'onset': row['CUE_ONSET'],
                    'duration': row['CUE_DURATION'],
                    'trial_type': f'cue_{condition}',
                    'condition': condition,
                    'trial': trial_num
                }
                bids_events.append(cue_event)
                
                # Fixation 
                fixation_event = {
                    'onset': row['FIXATION_ONSET'],
                    'duration': row['FIXATION_DURATION'],
                    'trial_type': f'fix_{condition}',
                    'condition': condition,
                    'trial': trial_num
                }
                bids_events.append(fixation_event)
                
                # Probe 
                probe_event = {
                    'onset': row['PROBE_ONSET'],
                    'duration': row['PROBE_DURATION'],
                    'trial_type': 'probe',
                    'condition': condition,
                    'trial': trial_num,
                    'accuracy': probe_hit,
                    'response_time': row['PROBE_MRT'] if pd.notna(row['PROBE_MRT']) and row['PROBE_MRT'] > 0 else 'n/a'
                }
                bids_events.append(probe_event)
                
                # Feedback: hit vs miss
                feedback_type = f"fb_{'hit' if probe_hit == 1 else 'miss'}"
                feedback_event = {
                    'onset': row['FEEDBACK_ONSET'],
                    'duration': row['FEEDBACK_DURATION'],
                    'trial_type': f'{feedback_type}_{condition}',
                    'condition': condition,
                    'result_words': row.get('TRIAL_RESULT', ''),
                    'result_reason': row.get('RESULT_REASON', ''),
                    'trial': trial_num
                }
                bids_events.append(feedback_event)

            # by onset
            bids_df = pd.DataFrame(bids_events)
            bids_df = bids_df.sort_values('onset').reset_index(drop=True)

            # cols BIDS format
            column_order = ['onset', 'duration', 'trial_type', 'condition', 'trial', 'accuracy', 'response_time', 'result_words','result_reason']
            
            # grab only existing columns
            available_cols = [col for col in column_order if col in bids_df.columns]
            bids_df = bids_df[available_cols]

            return bids_df

        else:
            print("Columns already modified, skipping")
            return None
    else:
        print(f"Task {task} not recognized for dataset, skipping modifications")
        return None
