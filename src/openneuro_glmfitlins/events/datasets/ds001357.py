"""Event fixes for ds001357."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds001357")
def ds001357(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds001357 by correcting column names,
    normalizing trial_type values, and cleaning onset/duration.

    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): Task name for dataset ("familiarity" or "viewing")
    
    Returns:
    pd.DataFrame or None
        Modified events DataFrame, or None if no updates were applied.
    """
    eventsdat = events_df.copy()

    if task.lower() in ["familiarity", "viewing"]:
        # Clean column names - remove spaces
        eventsdat.columns = eventsdat.columns.str.strip()
        
        # Copy "events" column to "trial_type", get either "events" or " events" as there may be leading space
        events_col = None
        for col in eventsdat.columns:
            if col.strip() == "events":
                events_col = col
                break
        
        if events_col:
            eventsdat["trial_type"] = eventsdat[events_col]
        
        # fix spaces in trial_type values
        if "trial_type" in eventsdat.columns:
            eventsdat["trial_type"] = eventsdat["trial_type"].astype(str).str.replace(" ", "", regex=False)
        
        # onset and duration to numeric (removing any spaces first)
        for col in ["onset", "duration"]:
            if col in eventsdat.columns:
                eventsdat[col] = eventsdat[col].astype(str).str.replace(" ", "", regex=False)
                eventsdat[col] = pd.to_numeric(eventsdat[col], errors="coerce").fillna(0)

        print(f"Cleaned onset/duration and normalized trial_type for task {task}")
        return eventsdat
    else:
        print(f"Task {task} not recognized for ds001357, skipping modifications")
        return None
