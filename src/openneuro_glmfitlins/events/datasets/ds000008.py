"""Event fixes for ds000008."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000008")
def ds000008(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000008 by modifying spaces/dashes in trialtype which are not compatible with PyBIDS transformations
    Modifying to not use the repeating and space values
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["conditionalstopsignal", "stopsignal"]:
        eventsdat = events_df.copy()

        # if trial_type column contains whitespace
        if eventsdat['trial_type'].astype(str).str.contains(r'\s', na=False).any():
            print("Modifying events to remove spaces in condition names and dropping rows with NA in onset/duration/trial_type")

            # removing spaces and dashes & drop onset/duration/trial_type that contain N/A
            eventsdat['trial_type'] = eventsdat['trial_type'].str.replace(r'[-\s]', '', regex=True)
            eventsdat = eventsdat.dropna(subset=['onset', 'duration', 'trial_type'])
            print("Unique trial types:",  eventsdat['trial_type'].unique())
            
            return eventsdat
        else:
            print("No whitespace found in trial_type. Skipping modification.")
            return None
