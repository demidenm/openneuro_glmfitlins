"""Event fixes for ds002294."""

from pathlib import Path

import pandas as pd

from ..common import EventsContext
from ..registry import register_events


@register_events("ds002294")
def ds002294(events_df: pd.DataFrame, task: str, ctx: EventsContext):
    """
    Process event data for ds002294, setting up BIDS-compliant events.
    Parse events file to individual run/subejct specific values and drop run/Subject entities to not conflict with BIDS values

    Parameters
    ----------
    events_df : pd.DataFrame
        Events read from the *_events.tsv file
    task : str
        Task name for dataset
    ctx : EventsContext
        Uses ctx.path and ctx.bids_layout

    Returns
    -------
    None
    """
    # Load main events file from root
    eventsdat = events_df.copy()
    event_file = ctx.path


    if task.lower() == "roletrait" and event_file.is_file():
        bold_files = ctx.bids_layout.get(task=task, suffix="bold", extension=".nii.gz")
        for bold in bold_files:
            subject = bold.entities['subject']
            run = bold.entities['run']

            # grab from main events file for this subject/run
            run_df = eventsdat[(eventsdat['Subject'] == int(subject)) & (eventsdat['run'] == run)].copy()
            run_df = run_df.drop(columns=['run', 'Subject'])

            if run_df.empty:
                continue

            # use the real path
            bold_path = Path(bold.path)
            events_filepath = bold_path.with_name(bold_path.name.replace("bold.nii.gz", "events.tsv"))
            print("Created events file for", events_filepath)
            run_df.to_csv(events_filepath, sep='\t', index=False)
        
        # move old file so it no longer exists and allows script to run
        old_events_file = event_file.with_name(event_file.name.replace("events", "old-events"))
        print("move OG root events file to", old_events_file)

        event_file.rename(old_events_file)
    else:
        print(f"Task {task} not recognized for dataset, skipping modifications")
