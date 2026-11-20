"""Event fixes for ds003789."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds003789")
def ds003789(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds003789 by modifying trial types if applicable. 
    Modifying to not use the repeating and space values
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    eventsdat = events_df.copy()

    if task in ["retrieval"]:
        # if trial_type contains updated values
        if not eventsdat['trial_type'].isin(['foil_new', 'lure_new', 'target_old', 'lure_old']).any():
            print("Modifying 'trial_type' with remapped values & dropping na")
            eventsdat['trial_type'] = eventsdat['trial_type'].replace({
                'foil new': 'foil_new',
                'lure new': 'lure_new',
                'target old': 'target_old',
                'lure old': 'lure_old'
            })
            eventsdatcpy = eventsdat.dropna(subset=['onset', 'duration', 'trial_type'])
            na_count = eventsdatcpy["response_time"].isna().sum()
            eventsdatcpy["response_time"] = eventsdatcpy["response_time"].fillna(0)

            print("Unique trial types:", eventsdatcpy['trial_type'].unique(), "Replace response NA rows:", na_count)
            return eventsdatcpy

        else:
            print("Modified 'trial_type' already exists . Skipping modification.")
            return None
        
    if task in ["encoding"]:
        #if trial_type contains updated values
        if not eventsdat['trial_type'].isin(['fixation', 'word_list1', 'word_list2', 'word_list3', 'rt_reg']).any():
            print("Modifying 'trial_type' with remapped values")
            eventsdat['trial_type'] = eventsdat['trial_type'].replace({
                '0.0': 'fixation',
                'rep1': 'word_list1',
                'rep2': 'word_list2',
                'rep3': 'word_list3'
            })
            eventsdatcpy = eventsdat.dropna(subset=['onset', 'duration', 'trial_type'])
            na_count = eventsdatcpy["response_time"].isna().sum()
            eventsdatcpy["response_time"] = eventsdatcpy["response_time"].fillna(0)
            
            print("Unique trial types:", eventsdatcpy['trial_type'].unique(), "Replace response NA rows:", na_count)
            return eventsdatcpy

        else:
            print("Modified 'trial_type' already exists . Skipping modification.")
            return None
