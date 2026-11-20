"""Event fixes for ds000009."""

import numpy as np
import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds000009")
def ds000009(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds000009 by modifying trial types if applicable. 
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset 
    
    Returns:
    modified events files
    """

    if task in ["balloonanalogrisktask"]:
        eventsdat = events_df.copy()
        eventsdat['old_trial_type'] = eventsdat['trial_type']

        #  if there trial_type values in current trial_type
        if not eventsdat['trial_type'].isin(['pumps', 'explode', 'cashout']).any():
            print("Creating new 'trial_type' and demeaned values for pumps, explosions and cashouts")           
            action_to_trial_type = {
                'ACCEPT': 'pumps',
                'EXPLODE': 'explode',
                'CASHOUT': 'cashout'
            }
            eventsdat['trial_type'] = eventsdat['action'].replace(action_to_trial_type)

            # estimate pumps for trial numbers
            eventsdat['pumps_number'] = eventsdat.groupby('trial_number').cumcount() + 1

            # demean pump number only for 'pumps' rows; trial number is initial pump to end trial event, e.g. cashout or explode
            pump_mask = eventsdat['trial_type'] == 'pumps'
            mean_pumps_per_trial = eventsdat.loc[pump_mask].groupby('trial_number')['pumps_number'].transform('mean')

            # create demeaned for only pumps
            eventsdat['demeaned_pumps'] = np.nan
            eventsdat.loc[pump_mask, 'demeaned_pumps'] = eventsdat.loc[pump_mask, 'pumps_number'] - mean_pumps_per_trial

            # obtain last pump before explode/cashout & map for all rows
            terminal_pumps = eventsdat[pump_mask].groupby('trial_number')['pumps_number'].max()
            eventsdat['terminal_pump_number'] = eventsdat['trial_number'].map(terminal_pumps)

            # demeaned terminal pump number for cashout and explode events 
            eventsdat['pumpsterminal_plusone'] = eventsdat['terminal_pump_number'] + 1 # since explode/cashout is AFTER the last pump
            mean_cashout = eventsdat[eventsdat['trial_type'] == 'cashout']['pumpsterminal_plusone'].mean()
            mean_explode = eventsdat[eventsdat['trial_type'] == 'explode']['pumpsterminal_plusone'].mean()

            eventsdat['demeaned_cashout'] = np.nan
            eventsdat.loc[eventsdat['trial_type'] == 'cashout', 'demeaned_cashout'] = \
                eventsdat['pumpsterminal_plusone'] - mean_cashout

            eventsdat['demeaned_explode'] = np.nan
            eventsdat.loc[eventsdat['trial_type'] == 'explode', 'demeaned_explode'] = \
                eventsdat['pumpsterminal_plusone'] - mean_explode

            # parametric modulators cannot have N/A, so setting to 0
            eventsdat[['demeaned_explode', 'demeaned_cashout', 'demeaned_pumps']] = (
                eventsdat[['demeaned_explode', 'demeaned_cashout', 'demeaned_pumps']].fillna(0)
            )

            print("Unique trial types:",  eventsdat['trial_type'].unique())
            print("When complete, update *_scans.tsv file_name column with filename")
            # ". e.g. ds000009/ -type f -name '*scans.tsv'   -exec sed -i '1s/file_name/filename/' {} \;"

            return eventsdat

        else:
            print("No old trial_types found. Skipping modification.")
            return None

    if task in ["stopsignal"]:
        eventsdat = events_df.copy()
        eventsdat['old_trial_type'] = eventsdat['trial_type']

        eventsdat = events_df.copy()

        # if trial_type column contains whitespace
        if not eventsdat['trial_type'].isin(['unsuccessfulstop', 'unuccessfulgo', 'junk', 'successfulstop', 'successfulgo']).any():
            print("Modifying events to make trial type for 'unsuccessfulstop', 'unuccessfulgo', 'junk', 'successfulstop', 'successfulgo'")
            eventsdat['trial_type'] = eventsdat['TrialOutcome'].str.lower()
            eventsdat['response_time'] = eventsdat['ReactionTime']
            
            print("Unique trial types:",  eventsdat['trial_type'].unique())
            print("When complete, update *_scans.tsv file_name column with filename")
            # ". e.g. ds000009/ -type f -name '*scans.tsv'   -exec sed -i '1s/file_name/filename/' {} \;"

            return eventsdat
        else:
            print("All types in trial_type: 'unsuccessfulstop', 'unuccessfulgo', 'junk', 'successfulstop', 'successfulgo'. Skipping modification.")
            return None
    
    if task in ["emotionalregulation"]:
        eventsdat = events_df.copy()
        eventsdat['old_trial_type'] = eventsdat['trial_type']

        eventsdat = events_df.copy()

        # if trial_type column contains whitespace
        if not eventsdat['trial_type'].isin([{'att_neut', 'suppr_neg', 'att_neg', 'rating_par'}]).any():
            print("Modifying events to make trial type for 'att_neut', 'suppr_neg', 'att_neg', 'rating_par', 'junk_rating'")
            eventsdat['trial_type'] = eventsdat['trial_type_orig']
            eventsdat['response_time'] = eventsdat['reaction_time']
            eventsdat['response_time'] = eventsdat["response_time"].fillna(0)
            
            print("Unique trial types:",  eventsdat['trial_type'].unique())
            print("When complete, update *_scans.tsv file_name column with filename")
            # ". e.g. ds000009/ -type f -name '*scans.tsv'   -exec sed -i '1s/file_name/filename/' {} \;"

            return eventsdat
        else:
            print("All types in trial_type: 'att_neut', 'suppr_neg', 'att_neg', 'rating_par'.")
            return None

    if task in ["discounting"]:
        eventsdat = events_df.copy()

        # if columsn exist
        if not eventsdat.columns.isin(['demeaned_rlglater', 'demeaned_timedelay', 'demeaned_smsooner']).any():
            print("Modifying events to make trial type for 'demeaned_rlglater','demeaned_timedelay','demeaned_smsooner'")
            eventsdat['response_time'] = eventsdat['reaction_time']
            eventsdat['response_time'] = eventsdat["response_time"].fillna(0)
            
            # creating a relative larger later versus sooner, then creating demeaned parameters for relative large later, delay days and small sooner
            eventsdat['relative_lglater'] = eventsdat['delayed_amount'] / eventsdat['immediate_amount']
            eventsdat['demeaned_rlglater'] = eventsdat['relative_lglater'] - eventsdat['relative_lglater'].mean()
            eventsdat['demeaned_timedelay'] = eventsdat['delay_time_days'] - eventsdat['delay_time_days'].mean()
            eventsdat['demeaned_smsooner'] = eventsdat['immediate_amount'] - eventsdat['immediate_amount'].mean()


            print("Unique Column types:",  eventsdat.columns)
            print("When complete, update *_scans.tsv file_name column with filename")
            # ". e.g. ds000009/ -type f -name '*scans.tsv'   -exec sed -i '1s/file_name/filename/' {} \;"

            return eventsdat
        else:
            print("All columns present. Skipping modification.")
            return None
