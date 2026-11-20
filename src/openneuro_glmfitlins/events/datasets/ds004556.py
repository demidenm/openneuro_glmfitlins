"""Event fixes for ds004556."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds004556")
def ds004556(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds004556 by modifying trial types to make them easier to interpret
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    

    if task in ["feedback"]:
        eventsdat = events_df.copy()
        eventsdat['old_rating'] = eventsdat['rating']

        #  if rating contains na
        if eventsdat['rating'].isna().any():
            print("replacing n/a in rating with '0' to make modulation compatible w/ fitlins")            

            eventsdat['rating'] = eventsdat["rating"].fillna(0)

            print("Unique values in rating:",  eventsdat['rating'].unique())
            return eventsdat

        else:
            print("No n/a in rating col. Skipping modification.")
            return None
