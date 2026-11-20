"""Event fixes for ds000002."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000002")
def ds000002(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000002 by modifying trial types if applicable. 
    Per DOI: 10.1016/j.neuroimage.2005.08.010, 'PCL trials alone were modeled ...  A nuisance regressor was added, 
    which consisted of trials on which no response was made.'
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["deterministicclassification", "mixedeventrelatedprobe", "probabilisticclassification"]:
        eventsdat = events_df.copy()

        if "missed" in eventsdat['trial_type'].values or eventsdat['trial_type'].isna().any():
            # dropping unclear NaN values -- rest blocks?
            eventsdat = eventsdat.dropna(subset=['duration', 'trial_type'])

            # A nuisance regressor was added, which consisted of trials on which no response was made 
            # setting as trial_type == 'missed'. Will convolve and include as nuisance
            eventsdat.loc[eventsdat['response_time'].isna(), 'trial_type'] = 'missed'
            return eventsdat

        else:
            print(f"Trial type value 'missed' already contained in events file. Skipping modification for {ctx.path.name}")
            return None
