"""Event fixes for ds001734."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds001734")
def ds001734(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for NARPS ds001734 by modifying trial types if applicable. 
    PyBIDS Replace() transformation fails for 'NoResp" in participant_response column. Renaming to noresp

    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["MGT"]:
        eventsdat = events_df.copy()

        # Check if there are hyphens or whitespace in 'trial_type'
        if "NoResp" in eventsdat['participant_response'].values:
            print("Replace NoResp with noresp in 'participant_response'")
            eventsdat.loc[eventsdat['participant_response'] == 'NoResp', 'participant_response'] = 'noresp'
 
            return eventsdat

        else:
            print(" NoResp not found in the specified columns. Skipping modification.")
            return None
