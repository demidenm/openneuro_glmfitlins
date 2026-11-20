"""Shared types and helpers for per-dataset event fixes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pandas as pd


@dataclass
class EventsContext:
    """Information an event-fix function may need besides the events table.

    path : the real ``*_events.tsv`` path (write target; use ``path.name`` for messages)
    study_id : OpenNeuro dataset id
    task : task label
    bids_layout : BIDSLayout of the raw BIDS dataset (may be None)
    """

    path: Path
    study_id: str
    task: str
    bids_layout: Optional[Any] = None


def add_reactiontime_regressor(eventsdf, trial_type_col='trial_type', resp_trialtype: list = ['response'], 
                                response_colname: str = 'response_time', rtreg_name: str ='rt_reg', 
                                onset_colname: str = 'onset', duration_colname: str = 'duration', 
                                new_trialtype: str = None, resp_in_ms: bool = False):
    """
    Pull reaction time regressor rows and add them to the dataframe as regressor.
    Assumes reaction times are in milliseconds; converts [times] / 1000 to convert to seconds for "duration".

    Parameters
    ----------
    eventsdf : DataFrame containing event data with response times.
    trial_type_col (str): Column name for identifying response trials.
    resp_trialtype (list): Values in trial_type_col that have associated response times.
    response_colname (str): Column name containing response time.
    rtreg_name (str): Name for new reaction time regressor.
    onset_colname (str): Name for onset times column.
    duration_colname (str): Name for duration times column.
    new_trialtype (str): Column name to store the new regressor trial type.
    resp_in_ms (bool): Whether response time is in milliseconds (convert to seconds if True).

    Returns
    -------
    DataFrame with reaction time regressor rows added.
    """
    # Set name for new s column
    new_trial_name = new_trialtype if new_trialtype else trial_type_col

    if isinstance(resp_trialtype, str):
        resp_trialtype = [resp_trialtype]

    # Filter and copy relevant rows
    rt_reg_rows = eventsdf[eventsdf[trial_type_col].isin(resp_trialtype)].copy()
    rt_reg_rows[new_trial_name] = rtreg_name

    # Compute duration
    if resp_in_ms:
        rt_reg_rows[duration_colname] = rt_reg_rows[response_colname] / 1000
    else:
        rt_reg_rows[duration_colname] = rt_reg_rows[response_colname]

    # Replace NAs with 0 and report how many were replaced
    na_count = rt_reg_rows[duration_colname].isna().sum()
    rt_reg_rows[duration_colname] = rt_reg_rows[duration_colname].fillna(0)

    print(f"[INFO] Replaced {na_count} missing or None RT duration values with 0.")

    # Select relevant columns and concatenate
    rt_reg_rows = rt_reg_rows[[onset_colname, duration_colname, new_trial_name]]

    # sort and reset to avoid fitlins convolution error
    result_rts = pd.concat([eventsdf, rt_reg_rows], ignore_index=True).sort_values(by="onset", ascending=True).reset_index(drop=True)
    
    return result_rts

