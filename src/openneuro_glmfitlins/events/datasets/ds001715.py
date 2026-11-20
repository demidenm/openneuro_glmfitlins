"""Event fixes for ds001715."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds001715")
def ds001715(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds001715 by modifying trial types if applicable. 
    Modifying to not use the repeating and space values
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task == "dts":
        orig_to_new = {
            "SignedMotionCohRight": "signedmotion_cohright",
            "SignedColorCohRight": "signedcolor_cohright",
            "RT": "response_time",
            "isMissedTrial": "missed_trial"
        }
        eventsdat = events_df.copy()


        # if all new columns already exist
        if not all(col in eventsdat.columns for col in orig_to_new.values()):
            print("Creating new columns in snake_case and filling RT NAs with zero.")

            for orig_col, new_col in orig_to_new.items():
                if orig_col in eventsdat.columns:
                    eventsdat[new_col] = eventsdat[orig_col]
            
            eventsdat["response_time"] = eventsdat["response_time"].fillna(0)
            eventsdat["signedmotion_abs"] = abs(eventsdat["signedmotion_cohright"])
            eventsdat["signedcolor_abs"] = abs(eventsdat["signedcolor_cohright"])

            return eventsdat

        else:
            print("New columns already exist. Skipping creation.")
            return None
