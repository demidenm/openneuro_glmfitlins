"""Event fixes for ds003345."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds003345")
def ds003345(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds003345 by modifying trial types if applicable. 
    Create a distinct trial type (trial_type + stim_info)

    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): Task name for dataset 
    
    Returns:
    pd.DataFrame or None
        Modified events DataFrame, or None if no updates were applied.
    """

    eventsdat = events_df.copy()

    if task.lower() == "penaltykik":
        # Only apply modifications if not already present
        if not {"trialtype_old"}.issubset(eventsdat.columns):
            eventsdat["trialtype_old"] = eventsdat["trial_type"]
            
            # combined trial_type
            eventsdat["trial_type"] = (
                eventsdat["trial_type"].str.strip().str.lower()
                + "_" +
                eventsdat["stim_info"].str.strip().str.lower()
            )
            print(f"Modified trial_type {task}. Trial types:", eventsdat["trial_type"].unique())
            return eventsdat
        else:
            print("Columns already modified, skipping")
            return None
    else:
        print(f"Task {task} not recognized for dataset, skipping modifications")
        return None
