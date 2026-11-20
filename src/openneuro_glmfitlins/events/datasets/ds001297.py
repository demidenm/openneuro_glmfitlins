"""Event fixes for ds001297."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds001297")
def ds001297(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds001297 by modifying trial types if applicable. 
    refactoring to make friend, control easier to compare
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    remap_dict = {
                '+fill0': 'fill',
                '+fill1': 'fill',
                '+fill2': 'fill',
                '+fill3': 'fill',
                'friend1': 'friend',
                'friend2': 'friend',
                'friend3': 'friend',
                'friend4': 'friend',
                'control1': 'control',
                'control2': 'control',
                'control3': 'control',
                'control4': 'control',
                'oddball1': 'oddball',
                'oddball2': 'oddball',
                'oddball3': 'oddball',
                'oddball4': 'oddball',
                'blank': 'blank',
                'self': 'self',
                'motor': 'motor'
            }

    if task in ["faceidentityoddball"]:
        eventsdat = events_df.copy()
        eventsdat['old_trial_type'] = eventsdat['trial_type']

        #  if there trial_type values in current matrix
        if not eventsdat['trial_type'].isin(['friend', 'control', 'fill', 'oddball']).any():
            print("Creating new 'trial_type' values by friend*, control*, fill*, oddball*")            

            # use the mapping to replace the values in trial type
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(remap_dict)

            print("Unique trial types:",  eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None
