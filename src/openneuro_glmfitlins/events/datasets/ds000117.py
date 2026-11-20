"""Event fixes for ds000117."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000117")
def ds000117(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000117 by modifying trial types to make them easier to interpret
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    trial_type_mapping = {
        'IniFF': 'famous_initial',
        'ImmFF': 'famous_immediate',
        'DelFF': 'famous_delayed',
        'IniUF': 'unfamiliar_initial',
        'ImmUF': 'unfamiliar_immediate',
        'DelUF': 'unfamiliar_delayed',
        'IniSF': 'scrambled_initial',
        'ImmSF': 'scrambled_immediate',
        'DelSF': 'scrambled_delayed'
    }

    if task in ["facerecognition"]:
        eventsdat = events_df.copy()
        eventsdat['old_trial_type'] = eventsdat['trial_type']

        #  if there trial_type values in current matrix
        if not eventsdat['trial_type'].isin(['famous_immediate', 'famous_delayed', 'unfamiliar_initial', 'unfamiliar_initial']).any():
            print("Creating new 'trial_type' values with more descriptive names")            

            # use the mapping to replace the values in trial type
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(trial_type_mapping)
                # dropping unclear NaN values -- rest blocks?
            eventsdat = eventsdat.dropna(subset=['trial_type'])

            print("Unique trial types:",  eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None
