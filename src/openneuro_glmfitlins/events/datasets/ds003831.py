"""Event fixes for ds003831."""

import numpy as np
import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds003831")
def ds003831(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds003831 created mean-cented arousal and valence cols
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """
    

    if task in ["identify1","identify2"]:
        eventsdat = events_df.copy()

        #  if columns not present
        if not eventsdat['trial_type'].isin(['exstim_valcent', 'exstim_arouscent', 'instim_valcent', 'instim_arouscent']).any():

            # grab ex_stim and in_stim trial_type rows
            ex_stim_mask = eventsdat['trial_type'] == 'ex_stim'
            in_stim_mask = eventsdat['trial_type'] == 'in_stim'

            # calc means & make mean centered cols
            mean_valence_ex = eventsdat.loc[ex_stim_mask, 'valence'].mean()
            mean_arousal_ex = eventsdat.loc[ex_stim_mask, 'arousal'].mean()
            mean_valence_in = eventsdat.loc[in_stim_mask, 'valence'].mean()
            mean_arousal_in = eventsdat.loc[in_stim_mask, 'arousal'].mean()

            # initialize with zero, as in_prep and in_feel have no corresponding arousal/valence, so no modulator hence always 0.
            eventsdat['exstim_valcent'] = 0.0
            eventsdat['exstim_arouscent'] = 0.0
            eventsdat['instim_valcent'] = 0.0
            eventsdat['instim_arouscent'] = 0.0

            # add mean-centered values for ex_stim & in_stim
            ex_stim_indices = eventsdat[ex_stim_mask].index
            eventsdat.loc[ex_stim_indices, 'exstim_valcent'] = (
                eventsdat.loc[ex_stim_indices, 'valence'] - mean_valence_ex
            )
            eventsdat.loc[ex_stim_indices, 'exstim_arouscent'] = (
                eventsdat.loc[ex_stim_indices, 'arousal'] - mean_arousal_ex
            )

            in_stim_indices = eventsdat[in_stim_mask].index
            eventsdat.loc[in_stim_indices, 'instim_valcent'] = (
                eventsdat.loc[in_stim_indices, 'valence'] - mean_valence_in
            )
            eventsdat.loc[in_stim_indices, 'instim_arouscent'] = (
                eventsdat.loc[in_stim_indices, 'arousal'] - mean_arousal_in
            )
            print("Colnames:", eventsdat.columns)

            return eventsdat

    if task in ["modulate1","modulate2"]:
        eventsdat = events_df.copy()

        #  if columns not present
        if 'reg_error' not in eventsdat.columns:
            # feel and rest have no corresponding arousal/valence, so no modulator and thus 0.
            eventsdat['fb_valence'] = eventsdat['fb_valence'].fillna(0)
            eventsdat['fb_arousal'] = eventsdat['fb_arousal'].fillna(0)
            eventsdat['reg_error'] = np.sqrt(eventsdat['fb_valence']**2 + eventsdat['fb_arousal']**2)
            print("Colnames:", eventsdat.columns)
            return eventsdat
        else:
            print("Columns present. Skipping modification.")
            return None
