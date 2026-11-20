"""Event fixes for ds000120."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000120")
def ds000120(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000120 by modifying trial types if applicable. 
    Create a distinct trial type (trial_type + trial_phase).
    Use score_txt to create 1/0 regressors for incorrect and drop trials.
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): Task name for dataset 
    
    Returns:
    pd.DataFrame or None
        Modified events DataFrame, or None if no updates were applied.
    """

    eventsdat = events_df.copy()

    if task.lower() == "antisaccadetaskwithfixedorder":
        # Only apply modifications if not already present
        if not {"incorrect", "drop"}.issubset(eventsdat.columns):
            
            # combined trial_type
            eventsdat["trial_type"] = (
                eventsdat["trial_type"].str.strip().str.lower()
                + "_" +
                eventsdat["trial_phase"].str.strip().str.lower()
            )

            # incorrect & drop regressors (1/0), score_txt to lowercase
            score_lower = eventsdat["score_txt"].str.strip().str.lower()
            eventsdat["incorrect"] = (score_lower == "incorrect").astype(int)
            eventsdat["drop"] = (score_lower == "drop").astype(int)

            print(f"Modified trial_type and created incorrect/drop columns for task {task}")
            return eventsdat
        else:
            print("Columns already modified, skipping")
            return None
    else:
        print(f"Task {task} not recognized for dataset, skipping modifications")
        return None
