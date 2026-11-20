"""BIDS layout helpers: per-task session/run metadata and volume counts."""

import pandas as pd
from nilearn.image import load_img


def get_session_metadata(task_name, bids_layout, Sessions=None, preproc_layout=None):
    if task_name.lower() in ['rest', 'resting']:
        print(f"* Task name {task_name} is resting state. Skipping. *")
        return None

    task_event_files = []
    task_bold_files = []

    if Sessions and len(Sessions) > 1:
        for session in Sessions:
            session_event_files = bids_layout.get(task=task_name, session=session, suffix="events", extension=".tsv")
            task_event_files.extend(session_event_files)

            session_bold_files = bids_layout.get(task=task_name, session=session, suffix="bold", extension=".nii.gz")
            task_bold_files.extend(session_bold_files)

        if not task_event_files:
            task_event_files.extend(
                bids_layout.get(task=task_name, suffix="events", extension=".tsv", session=None)
            )
    else:
        task_event_files = bids_layout.get(task=task_name, suffix="events", extension=".tsv")
        task_bold_files = bids_layout.get(task=task_name, suffix="bold", extension=".nii.gz")

    # Determine number of volumes
    num_volumes = get_numvolumes(task_bold_files[0].path) if task_bold_files else None
    if num_volumes is None and preproc_layout:
        # if bids not present, try fmriprep
        deriv_bold_files = preproc_layout.get(task=task_name, suffix="bold", extension=".nii.gz")
        num_volumes = get_numvolumes(deriv_bold_files[0].path) if deriv_bold_files else None

    # subject metadata by session
    subject_data_by_session = {}

    if Sessions and len(Sessions) > 1:
        # if more than 1 session
        for session in Sessions:
            subjects = bids_layout.get_subjects(task=task_name, session=session)
            subject_data = []
            for subject in subjects:
                subject_runs = bids_layout.get_runs(subject=subject, task=task_name, session=session)
                subject_data.append({
                    'Subject': f'sub-{subject}',
                    'Session': f'ses-{session}',
                    'num_runs': len(subject_runs),
                    'run_numbers': ', '.join(map(str, sorted(subject_runs))) if subject_runs else 'None'
                })
            if subject_data:
                subject_data_by_session[session] = pd.DataFrame(subject_data)
    else:
        #if only one session
        subjects = bids_layout.get_subjects(task=task_name)
        subject_data = []
        for subject in subjects:
            subject_runs = bids_layout.get_runs(subject=subject, task=task_name)
            subject_data.append({
                'Subject': f'sub-{subject}',
                'num_runs': len(subject_runs),
                'run_numbers': ', '.join(map(str, sorted(subject_runs))) if subject_runs else 'None'
            })
        if subject_data:
            subject_data_by_session['all'] = pd.DataFrame(subject_data)

    return {
        "task_event_files": task_event_files,
        "task_bold_files": task_bold_files,
        "num_volumes": num_volumes,
        "subject_data_by_session": subject_data_by_session
    }


def get_numvolumes(nifti_path_4d):
    """
    Alternative method to get number of volumes using Nilearn.
    
    Parameters:
    nifti_path(str) : Path to the fMRI NIfTI (.nii.gz) file
    
    Returns:
    Number of volumes in the fMRI data using nilearn image + shape
    """
    try:
        # Load 4D image
        img = load_img(nifti_path_4d)
        
        # Get number of volumes
        return img.shape[3] if len(img.shape) == 4 else None
    
    except Exception as e:
        print(f"Nilearn error reading file {nifti_path_4d}: {e}")
        return None
