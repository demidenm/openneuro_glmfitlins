"""Event fixes for ds001848."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds001848")
def ds001848(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds001848 by modifying trial types if applicable. 
    Modifying to not use the repeating and space values
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task == "ParallelAdaptation":
        eventsdat = events_df.copy()

        # trial_type exists or contains non-null values
        if 'trial_type' not in eventsdat.columns or eventsdat['trial_type'].isnull().all():
            print("Creating 'trial_type' with remapped values removing spaces and camelcase")

            remap_dict = {}
            for val in eventsdat['Condition Name'].dropna().unique():
                first = val.split()[0]
                snake = ''
                for i, char in enumerate(first):
                    if char.isupper() and i != 0 and not first[i-1].isupper():
                        snake += '_'
                    snake += char.lower()
                remap_dict[val] = snake

            eventsdat['trial_type'] = eventsdat['Condition Name'].map(remap_dict)

            print("Unique trial types:", eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("'trial_type' already exists or is partially filled. Skipping modification.")
            return None
