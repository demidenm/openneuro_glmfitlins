"""Event fixes for ds000109."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000109")
def ds000109(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000109 by modifying trial types if applicable. 
    Per DOI: 10.1523/JNEUROSCI.5511-11.2012, Dropping NaN in timing columns that are incorrect
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["theoryofmindwithmanualresponse"]:
        eventsdat = events_df.copy()

        # Check if there are any NAs in the specified columns or trial_type has spaces
        if eventsdat[['onset', 'duration', 'trial_type']].isna().any().any() or eventsdat['trial_type'].str.contains(r'\s', na=False).any():
            print("**NaN dropped and trial_type spaces removed**")
            # Only run this if there are NAs in those columns
            eventsdat_cpy = eventsdat.dropna(subset=['onset', 'duration', 'trial_type'])
            eventsdat_cpy.loc[:, 'trial_type'] = eventsdat_cpy['trial_type'].str.replace(' ', '')

            return eventsdat_cpy
        else:
            print("No NaNs or spaces found in the specified columns. Skipping modification.")
            return None
