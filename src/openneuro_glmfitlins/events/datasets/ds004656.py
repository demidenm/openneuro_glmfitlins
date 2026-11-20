"""Event fixes for ds004656."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds004656")
def ds004656(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds004656 by modifying trial types if applicable. 
    Create a trial_type column which is copy of condition. Simple standardization
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    pd.DataFrame or str
        Modified events DataFrame, or a message that no updates were necessary.
    """

    if task == "FoodStimHiLo":
        eventsdat = events_df.copy()
        if 'trial_type' not in eventsdat.columns:
            eventsdat["trial_type"] = eventsdat["condition"]
            print("Copied condition to trial_type")

            return eventsdat
        else:
            print("No updates necessary, 'trial_type' already present")
            return None
