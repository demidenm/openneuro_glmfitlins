"""Event fixes for ds000001."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000001")
def ds000001(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000001 by modifying NA values to 0. With N/As fitlins model spec issues -- convolution doesnt work
    Modifying to not use the repeating and space values
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task == "balloonanalogrisktask":
        check_col_nans = ['cash_demean', 'control_pumps_demean', 'explode_demean', 'pumps_demean','response_time']
        eventsdat = events_df.copy()

        if eventsdat[check_col_nans].isna().any().any():
            print("Modify events to replace NaN with zero for Fitlins Models")
            eventsdat[check_col_nans] = eventsdat[check_col_nans].fillna(0)
            
            return eventsdat

        else:
            print("Columns dont contain NaN. Skipping creation.")
            return None
