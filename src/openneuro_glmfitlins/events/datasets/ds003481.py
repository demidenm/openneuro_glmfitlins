"""Event fixes for ds003481."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds003481")
def ds003481(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds003481 by modifying trial types if applicable. 
    Simple standardization (lowercase values)
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    pd.DataFrame or str
        Modified events DataFrame, or a message that no updates were necessary.
    """
    eventsdat = events_df.copy()


    # For tasks sar or sae, convert trial_type to lowercase
    if task.lower() in ["sar"]:
        eventsdat["trial_type"] = eventsdat["trial_type"].str.lower()
        print(f"Converted trial_type values to lowercase for task {task}")

        return eventsdat
    
    if task.lower() in ["verbs"]:
        eventsdat["trial_type"] = eventsdat["trial_type"].str.strip()
        print(f"Stripped whitespace from trial_type for task {task}")

        return eventsdat
    else:
        print("Task provided is not 'sar' or 'verbs', skipping modifications")
        return None
