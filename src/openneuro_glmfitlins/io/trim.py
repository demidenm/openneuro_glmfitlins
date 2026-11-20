"""Trim dummy/calibration volumes from preprocessed BOLD and confounds."""

from pathlib import Path

import pandas as pd
from nilearn.image import index_img


def trim_derivatives(boldpath: str, confpath: str, num_totrim: int):
    """
    Trim a specified number of initial volumes from an fMRI NIfTI file and confounds file.
    
    Parameters:
    boldpath (str) : Path to the fMRI NIfTI (.nii.gz) file
    confpath (str) : Path to the counfounds (.tsv) file
    num_totrim (int) : number of initial volumes to remove, int

    Returns:
    BOLD NIfTI, confounds dataframe
    """
    nifti_data = trim_calibration_volumes(bold_path=boldpath, num_voltotrim=num_totrim)
    confounds_data = trim_confounds(confounds_path=confpath, num_rowstotrim=num_totrim)

    return nifti_data, confounds_data


def trim_calibration_volumes(bold_path: str, num_voltotrim:int):
    """
    Trim a specified number of initial volumes from an fMRI NIfTI file.
    
    Parameters:
    bold_path (str): Path to the 4D fMRI NIfTI file (.nii or .nii.gz)
    num_voltotrim (int): Number of initial volumes to remove
    
    Returns:
    Trimmed nifti file
    """
    bold_path = Path(bold_path)  # Ensure it's a Path object

    if not bold_path.exists():
        raise FileNotFoundError(f"File not found: {bold_path}")
    
    # load nifti & trim. 
    try:
        print(f"Trimming {num_voltotrim} initial volumes...")
        trimmed_img = index_img(str(bold_path), slice(num_voltotrim, None))
        
        total_vols = trimmed_img.shape[3] if len(trimmed_img.shape) == 4 else None
        original_vols = total_vols + num_voltotrim if total_vols else None
        
        if total_vols is None:
            raise ValueError(f"Invalid NIfTI file: {bold_path}")
        
        print(f"    Output shape: {trimmed_img.shape}")
        
        return trimmed_img

    except Exception as e:
        raise ValueError(f"Error loading NIfTI file: {e}")


def trim_confounds(confounds_path:str, num_rowstotrim:int):
    """
    Trim confounds rows by specified N of calibration volumes
    
    Parameters:
    confounds_path (str) : Path to the confounds tsv file
    num_rowstotrim (int) : Number of initial rows to remove
    
    Returns:
    modified confounds dataframe
    """
    # file exists 
    confounds_path = Path(confounds_path)  # Ensure a Path object

    if not confounds_path.exists():
        raise FileNotFoundError(f"File not found: {confounds_path}")
    
    # load file
    try:
        confounds_df = pd.read_csv(confounds_path, sep='\t')
    except Exception as e:
        raise ValueError(f"Error reading confounds file: {e}")
    
    # Check number of rows
    total_rows = len(confounds_df)
    
    if num_rowstotrim >= total_rows:
        raise ValueError(f"Number of rows to trim ({num_rowstotrim}) exceeds total rows ({total_rows}).")
    
    # trim rows
    trimmed_df = confounds_df.iloc[num_rowstotrim:].reset_index(drop=True)
    
    return trimmed_df
