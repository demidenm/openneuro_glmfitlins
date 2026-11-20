"""Event fixes for ds001233."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds001233")
def ds001233(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds001233 by modifying trial types if applicable. 
    Modify onset and duration, Modifying numeric finger events to labels and make "trial_type". Remap 0 to incorr and 1 to corr for accuracy
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["cuedSFM"]:
        eventsdat = events_df.copy()

        orig_to_new = {
            2: "index",
            3: "middle",
            4: "ring",
            5: "pinky"
        }
        acc = {
            0: "incorrect",
            1: "correct"
        }

        #  if there trial_type values in current matrix
        if 'trial_type' not in eventsdat.columns or not eventsdat['trialType'].isin(['index', 'middle', 'ring', 'pinky']).any():
            print("Cleaning 'trial_type' values by remapping and update correct/incc")            
            # remap cols
            eventsdat['trial_type'] = eventsdat['trialType'].replace(orig_to_new)
            eventsdat['accuracy'] = eventsdat['correct'].replace(acc)

            print("Unique trial types:",  eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None
