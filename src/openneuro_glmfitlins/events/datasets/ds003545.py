"""Event fixes for ds003545."""

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds003545")
def ds003545(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds003545 by modifying trial types if applicable.
    
    Remapping values in trial_type for clarity in contrast estimations/design matrices.
    For compL1 and compLn tasks, trial_type values also receive "_cor" or "_incorr" 
    suffixes based on the 'correct' column (1 = correct, 0 = incorrect).
    
    Parameters:
    events_df (DataFrame): events read from the *_events.tsv file
    ctx (EventsContext): file path, study id and (lazy) BIDS layout
    task (str): task name for dataset
    
    Returns:
    pd.DataFrame or None
        Modified events DataFrame, or None if no updates were necessary.
    """
    
    remapping = {
        "compL1": {
            "1": "printed_word",
            "2": "spoken_word", 
            "3": "fixation"
        },
        "compLn": {
            "1": "printed_word",
            "2": "spoken_word", 
            "3": "fixation"
        },
        "prodL1": {
            "1": "fixation",
            "2": "end_fixation", 
            "3": "semantic_cond", 
            "4": "control_cond", 
            "5": "irrelevant_cond"
        },
        "prodLn": {
            "1": "fixation",
            "2": "end_fixation", 
            "3": "semantic_cond", 
            "4": "control_cond", 
            "5": "irrelevant_cond"
        }
    }

    eventsdat = events_df.copy()
    eventsdat['trial_type'] = eventsdat['trial_type'].astype(str)

    if task == "compL1":
        if any(key in eventsdat['trial_type'].values for key in remapping["compL1"].keys()):
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(remapping["compL1"])
            print("Applied remapping for compL1", eventsdat['trial_type'].unique())
        else:
            print("No remapping needed for compL1 - values already present")

        #  _cor/_incorr suffix
        eventsdat['trial_type'] = eventsdat.apply(
            lambda row: (
                f"{row.trial_type}_{'cor' if row.correct == 1 else 'incorr'}"
                if row.trial_type in ["printed_word", "spoken_word"]
                else row.trial_type
            ),
            axis=1
        )
        print("Added correct/incorrect suffix for compL1", eventsdat['trial_type'].unique())

        return eventsdat

    elif task == "compLn":
        if any(key in eventsdat['trial_type'].values for key in remapping["compLn"].keys()):
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(remapping["compLn"])
            print("Applied remapping for compLn", eventsdat['trial_type'].unique())
        else:
            print("No remapping needed for compLn - values already present")

        #  _cor/_incorr suffix
        eventsdat['trial_type'] = eventsdat.apply(
            lambda row: (
                f"{row.trial_type}_{'cor' if row.correct == 1 else 'incorr'}"
                if row.trial_type in ["printed_word", "spoken_word"]
                else row.trial_type
            ),
            axis=1
        )
        print("Added correct/incorrect suffix for compLn", eventsdat['trial_type'].unique())

        return eventsdat
    
    elif task == "prodL1":
        # Check if remapping needed, apply if so
        eventsdat['trial_type'] = eventsdat['trial_type'].astype(str)
        if any(key in eventsdat['trial_type'].values for key in remapping["prodL1"].keys()):
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(remapping["prodL1"])
            print("Applied remapping for prodL1 task", eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No remapping needed for prodL1, values already present")
            return None

    elif task == "prodLn":
        # Check if remapping needed, apply if so
        eventsdat['trial_type'] = eventsdat['trial_type'].astype(str)
        if any(key in eventsdat['trial_type'].values for key in remapping["prodLn"].keys()):
            eventsdat['trial_type'] = eventsdat['trial_type'].replace(remapping["prodLn"])
            print("Applied remapping for prodLn task", eventsdat['trial_type'].unique())
            return eventsdat

        else:
            print("No remapping needed for prodLn, values already present")
            return None
    
    else:
        print(f"{task} does not match available tasks")
        return None
