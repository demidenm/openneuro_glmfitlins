"""Event fixes for ds001229."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds001229")
def ds001229(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds001229 by modifying trial types if applicable. 
    trial_type doesnt exist, create by combining category + type. Note, typo categor, categ, category in some task events
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    Returns:
    modified events files
    """

    if task in ["em","wm"]:
        eventsdat = events_df.copy()

        #  if there trial_type values in current matrix
        if 'trial_type' not in eventsdat.columns:
            print("Creating 'trial_type' values by combining categ / category / categor + type")            
            # create trial_type col
            if 'categor' in eventsdat.columns:
                eventsdat['trial_type'] = eventsdat['categor'] + '_' + eventsdat['type']
            elif 'categ' in eventsdat.columns:
                eventsdat['trial_type'] = eventsdat['categ'] + '_' + eventsdat['type']
            elif 'category' in eventsdat.columns:
                eventsdat['trial_type'] = eventsdat['category'] + '_' + eventsdat['type']
            else:
                raise KeyError("Neither 'categor' nor 'category' column found in events file.")
            
            print("Unique trial types:",  eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None
