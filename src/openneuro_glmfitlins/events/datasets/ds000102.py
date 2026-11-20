"""Event fixes for ds000102."""

import pandas as pd

from ..common import EventsContext, add_reactiontime_regressor
from ..registry import register_events


@register_events("ds000102")
def ds000102(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000102: adding rt regressor. 

    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["flanker"]:
        eventsdat = events_df.copy()

        if "rt_reg" not in eventsdat['trial_type'].values:
            # create rt regressor

            # RT appears important, adding RT 'rt_reg' into trial_type column. Missed is included, set to 0 by func since NaN
            # include 'rt_reg' in spec file
            eventsdat_cpy = eventsdat.copy()
            cols_rt = ['congruent_correct', 'incongruent_incorrect', 'incongruent_correct', 'congruent_incorrect'] 
            eventsdat_cpy = add_reactiontime_regressor(eventsdf=eventsdat_cpy, trial_type_col='trial_type', resp_trialtype = cols_rt, 
            response_colname = 'response_time', rtreg_name ='rt_reg', resp_in_ms = False)
            
            # Sort by 'onset' column from low to high
            eventsdat_cpy = eventsdat_cpy.sort_values(by='onset', ascending=True)
            return eventsdat_cpy

        else:
            print(f"Trial type value 'missed' already contained in events file. Skipping modification for {ctx.path.name}")
            return None
