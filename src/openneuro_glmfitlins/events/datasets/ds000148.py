"""Event fixes for ds000148."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000148")
def ds000148(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000148 by modifying trial types if applicable. 
    Modifying to not use ' ' in python column names. 
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["figure2backwith1backlures"]:
        eventsdat = events_df.copy()

        # Check if there are hyphens or whitespace in 'trial_type'
        if eventsdat['trial_type'].astype(str).str.contains(r'\s', na=False).any():
            print("Cleaning 'trial_type' values: removing spaces")
            eventsdat.loc[:, 'trial_type'] = eventsdat['trial_type'].str.replace(r'\s', '', regex=True)
            return eventsdat

        else:
            print("No spaces found in the specified columns. Skipping modification.")
            return None
