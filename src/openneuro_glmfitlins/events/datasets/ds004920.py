"""Event fixes for ds004920."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds004920")
def ds004920(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds004920 by modifying trial types if applicable. 
    social doors have N/A in trial_type which is not allowed in BIDS-SM, drop NA values
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    pd.DataFrame or str
        Modified events DataFrame, or a message that no updates were necessary.
    """

    if task == "socialdoors":
        eventsdat = events_df.copy()

        # if no NaNs left, return message
        if not eventsdat['trial_type'].isna().any():
            print("No updates necessary, no NaNs in trial_type")
            return None
        
        eventsdat_cleaned = eventsdat.dropna(subset=['onset', 'duration', 'trial_type'])
        return eventsdat_cleaned

    elif task == "sharedreward":
        df = events_df.copy()
        df.columns = df.columns.str.strip()

        # already processed?
        if "trial_type_old" in df.columns:
            print("No updates necessary, 'trial_type_old' already present")
            return None

        if df['trial_type'].str.contains("_decision").any():
            print("No updates necessary, decision-phase trial_types already present")
            return None

        events = df[
            df['trial_type'].str.startswith('event_') | 
            (df['trial_type'] == 'missed_trial')
        ].copy()
        
        new_events = []
        for _, trial in events.iterrows():
            if trial['trial_type'] == 'missed_trial':
                missed_event = {
                    'onset': trial['onset'],
                    'duration': trial['duration'],
                    'trial_type': 'missed_trial',
                    'trial_type_old': trial['trial_type'],
                    'response_time': trial['response_time']
                }
                new_events.append(missed_event)
                continue

            parts = trial['trial_type'].split('_')
            partner = parts[1]
            outcome = parts[2]
            outcome_map = {'reward': 'win', 'punish': 'lose', 'neutral': 'neutral'}
            mapped_outcome = outcome_map[outcome]
            
            decision_event = {
                'onset': trial['onset'],
                'duration': 2.5,
                'trial_type': f'{partner}_decision',
                'trial_type_old': trial['trial_type'],
                'response_time': trial['response_time']
            }
            new_events.append(decision_event)
            
            feedback_event = {
                'onset': trial['onset'] + 2.5,
                'duration': 1.0,
                'trial_type': f'{partner}_{mapped_outcome}',
                'trial_type_old': trial['trial_type'],
                'response_time': 'n/a'
            }
            new_events.append(feedback_event)
        
        result_df = pd.DataFrame(new_events).sort_values('onset').reset_index(drop=True)
        return result_df

    elif task == "mid":
        df = events_df.copy()

        # already decomposed?
        if df['trial_type'].str.contains("cue_|fix_|probe_|feedback_").any():
            print("No updates necessary, trial_types already decomposed into cue/fix/probe/feedback")
            return None

        df = df.sort_values(by="onset").reset_index(drop=True)
        new_rows = []
        last_trial_type = None  

        for _, row in df.iterrows():
            onset = row["onset"]
            duration = row["duration"]
            trial_type = row["trial_type"]

            if trial_type in ["ConHit", "ConMiss"]:
                if last_trial_type is None:
                    raise ValueError(f"Feedback at onset {onset} has no preceding cue trial.")
                feedback_label = "feedback_Hit" if trial_type == "ConHit" else "feedback_Miss"
                new_rows.append({
                    "onset": onset,
                    "duration": duration,
                    "trial_type": f"{feedback_label}_{last_trial_type}"
                })
                last_trial_type = None
                continue

            cue_onset = onset
            cue_duration = 1.0
            fix_onset = cue_onset + cue_duration
            fix_duration = duration - 1.0
            probe_onset = fix_onset + fix_duration
            probe_duration = 1.0

            trial_clean = trial_type.strip().replace(" ", "").replace("-", "").replace("_", "")
            last_trial_type = trial_clean

            new_rows.append({
                "onset": cue_onset,
                "duration": cue_duration,
                "trial_type": f"cue_{trial_clean}"
            })
            new_rows.append({
                "onset": fix_onset,
                "duration": fix_duration,
                "trial_type": f"fix_{trial_clean}"
            })
            new_rows.append({
                "onset": probe_onset,
                "duration": probe_duration,
                "trial_type": f"probe"
            })

        result_df = pd.DataFrame(new_rows)
        return result_df
