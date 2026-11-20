"""Event fixes for ds002006."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds002006")
def ds002006(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds002006 by modifying trial types if applicable. 
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

    if task.lower() == "colordots":
        if not {"trial_type"}.issubset(eventsdat.columns):
            
            
            eventsdat["trial_type"] = eventsdat["TRIALTYPE"]
            eventsdat["response_time"] = eventsdat["RESPONSE_TIME"].fillna(0)

            eventsdat["trial_type"] = eventsdat["trial_type"].str.lower()
            print(f"renamed TRIALTYPE to trial_type, replace RT n/a w/0 and made trial_type lowercase for {task}")
            return eventsdat
        else:
            print("Columns already modified, skipping")
            return None

    elif task.lower() == "foodchoice":
        if not {"trial_type"}.issubset(eventsdat.columns):
            
            
            eventsdat["trial_type"] = eventsdat["TRIALTYPE"]
            eventsdat["response_time"] = eventsdat["RESPONSE_TIME"].fillna(0)

            eventsdat["trial_type"] = eventsdat["trial_type"].str.lower()
            print(f"renamed TRIALTYPE to trial_type, replace RT n/a w/0 and made trial_type lowercase for {task}")
            return eventsdat
        else:
            print("Columns already modified, skipping")
            return None
    
    elif task.lower() == "memory":
        if not {"trial_type"}.issubset(eventsdat.columns):
            
            eventsdat["trial_type"] = eventsdat["TRIALTYPE"]
            eventsdat["response_time"] = eventsdat["RESPONSE_TIME"].fillna(0)
            eventsdat["trial_type"] = eventsdat["trial_type"].str.lower()
            
            # Demean LIKING_RATING, demeaned from all non-NAN vales paper: 
            # "liking rating for the object demeaned across these trials within each run for each participant"
            eventsdat["LIKING_RATING_num"] = pd.to_numeric(eventsdat["LIKING_RATING"], errors='coerce')
            mean_rating = eventsdat["LIKING_RATING_num"].mean()
            eventsdat["liking_demeaned"] = eventsdat["LIKING_RATING_num"] - mean_rating
            
            print(f"renamed TRIALTYPE to trial_type, replace RT n/a w/0, made trial_type lowercase, and demeaned LIKING_RATING for {task}")
            return eventsdat

    else:
        print(f"Task {task} not recognized, skipping modifications")
        return None
