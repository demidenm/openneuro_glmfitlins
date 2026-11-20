"""Event fixes for ds000212."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000212")
def ds000212(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000212 by modifying trial types if applicable. 
    cleaning for bids standards
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): Task name for dataset 
    
    Returns:
    pd.DataFrame or None
        Modified events DataFrame, or None if no updates were applied.
    """

    eventsdat = events_df.copy()

    if task.lower() == "dis":
        if not {"trial_type"}.issubset(eventsdat.columns):
            
            
            eventsdat["trial_type"] = eventsdat["condition"]
            eventsdat["response_time"] = eventsdat["RT"].fillna(0)
            eventsdat["trial_type"] = eventsdat["trial_type"].str.lower()

            print(f"renamed condition to trial_type, replace RT n/a w/0 and made")
            return eventsdat
        else:
            print("Columns already modified, skipping")
            return None

    elif task.lower() == "fb":
        if not {"trial_type"}.issubset(eventsdat.columns):
            
            
            eventsdat["trial_type"] = eventsdat["condition"]
            eventsdat["response_time"] = eventsdat["RT"].fillna(0)
            eventsdat["trial_type"] = eventsdat["trial_type"].str.lower()

            # Until the design is clarified, keeping only first part of value name
            eventsdat["trial_type"] = eventsdat["trial_type"].str.split('_').str[0]

            print(f"renamed condition to trial_type, replace RT n/a w/0 and made")
            return eventsdat
        else:
            print("Columns already modified, skipping")
            return None

    else:
        print(f"Task {task} not recognized, skipping modifications")
        return None
