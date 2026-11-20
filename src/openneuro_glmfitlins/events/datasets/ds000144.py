"""Event fixes for ds000144."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000144")
def ds000144(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000114 by modifying trial types if applicable. 
    Create a distinct trial type (trial_type)
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): Task name for dataset 
    
    Returns:
    pd.DataFrame or None
        Modified events DataFrame, or None if no updates were applied.
    """

    eventsdat = events_df.copy()

    if task.lower() == "emotionalfaces":
        # Only apply modifications if not already present
        if not {"trail_type"}.issubset(eventsdat.columns):
            
            # create trial_type
            eventsdat["trial_type"] = eventsdat["stim_emotion"]


            print(f"Created trial_type for task {task}")
            return eventsdat
        else:
            print("Columns already modified, skipping")
            return None
    else:
        print(f"Task {task} not recognized for dataset, skipping modifications")
        return None
