"""Event fixes for ds002872."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds002872")
def ds002872(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds002827 by modifying trial types if applicable. 
    Modify onset and duration, some include '.' (seconds) others ',' (suggest ms). Occurrs in error
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["illusion"]:
        eventsdat = events_df.copy()

        orig_to_new = {
            "T1": "t_low",
            "T2": "t_hi",
            "P1": "p_hi",
            "P2": "p_low"
        }

        #  if there trial_type values in current matrix
        if not eventsdat['trial_type'].isin(['t_hi', 't_low', 'p_hi', 'p_low']).any():
            print("Cleaning 'trial_type' values by remapping and remiving commas in onset/duration to decimal")
            #  comma decimal separator in numeric columns
            eventsdat.loc[:, 'onset'] = eventsdat['onset'].astype(str).str.replace(',', '.').astype(float)
            eventsdat.loc[:, 'duration'] = eventsdat['duration'].astype(str).str.replace(',', '.').astype(float)
            
            
            # remap cols
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(orig_to_new)

            print("Unique trial types:",  eventsdat['trial_type'].unique())

            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None
