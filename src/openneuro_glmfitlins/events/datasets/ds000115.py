"""Event fixes for ds000115."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000115")
def ds000115(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000115 by modifying trial types if applicable. 
    Modifying to not use '-' in python column names. Do not use '_' to replace as that is a parsing value in PyBIDS
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["letter0backtask", "letter1backtask", "letter2backtask"]:
        eventsdat = events_df.copy()

        # Check if there are hyphens or whitespace in 'trial_type'
        if eventsdat['trial_type'].astype(str).str.contains(r'[-\s]', na=False).any():
            print("Cleaning 'trial_type' values: removing hyphens and spaces")
            # remove hyphens and whitespace from 'trial_type'
            eventsdat.loc[:, 'trial_type'] = eventsdat['trial_type'].str.replace(r'[-\s]', '', regex=True)
            return eventsdat

        else:
            print("No spaces or hyphens found in the specified columns. Skipping modification.")
            return None
