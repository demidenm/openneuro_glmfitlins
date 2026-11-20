"""Event fixes for ds004144."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds004144")
def ds004144(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds004144 by modifying trial types if applicable. 
    epr task trial_type have spacing which can cause issues with BIDS-SM, cleaning to make it easier to work with
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    pd.DataFrame or str
        Modified events DataFrame, or a message that no updates were necessary.
    """

    if task == "epr":
        eventsdat = events_df.copy()

        def clean_trialtype(name):
            return name.replace(" ", "").replace("-", "_")

        # Apply function
        eventsdat["trial_type"] = eventsdat["trial_type"].apply(clean_trialtype)
        
        return eventsdat
