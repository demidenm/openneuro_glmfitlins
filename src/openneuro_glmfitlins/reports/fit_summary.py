"""Count FitLins outputs (subjects/sessions/runs/contrasts) per node level for one analysis folder."""

from pathlib import Path

import pandas as pd
from nilearn.interfaces.bids import parse_bids_filename


def process_file_list(file_list):
    """Process a list of files using parse_bids_filename and return parsed info."""
    parsed_files = []
    for f in file_list:
        parsed = parse_bids_filename(f)
        
        # Default missing session/run
        parsed['ses'] = parsed.get('ses', 1)  # use 1 if session missing
        parsed['run'] = parsed.get('run', 1)  # use 1 if run missing
        
        # Ensure consistent types
        parsed['ses'] = str(parsed['ses'])
        parsed['run'] = int(parsed['run'])
        
        parsed_files.append(parsed)
    
    return parsed_files


def _clean_contrast(name: str):
    """Clean contrast name by removing '_stat' suffix."""
    return name.split('_stat')[0] if isinstance(name, str) else name


def create_counts_dataframe(parsed_files):
    """
    Create a DataFrame with counts across sessions, subjects, contrasts and runs.
    
    Parameters:
        parsed_files: lst of dictionaries from parse_bids_filename_robust
    
    Returns:
        Dictionary with multiple DataFrames for different count summaries
    """
    df = pd.DataFrame(parsed_files)
    df_clean = df.dropna(subset=['sub'])
    df_clean['contrast'] = df_clean['contrast'].apply(_clean_contrast)
    df['ses'] = df['ses'].fillna('1').astype(str)
    df['run'] = df['run'].fillna(1).astype(int)
    
    print(f"Total files processed: {len(df)}")
    print(f"Files with valid subject info: {len(df_clean)}")
    
    results = {
        'summary': {
            'total_files': len(df_clean),
            'unique_subjects': df_clean['sub'].nunique(),
            'unique_sessions': df_clean['ses'].nunique(),
            'unique_runs': df_clean['run'].nunique(),
            'unique_contrasts': df_clean['contrast'].nunique()
        }
    }
    
    # Subject unique mappings
    results['subject_uniques'] = (
        df_clean.groupby('sub')
        .agg({
            'ses': lambda x: sorted(set(x.dropna())),
            'run': lambda x: sorted(set(x.dropna())),
            'contrast': lambda x: sorted(set(x.dropna()))
        })
        .reset_index()
    )
    
    # Individual counts
    results['by_subject'] = (
        df_clean['sub']
        .value_counts()
        .reset_index(name='file_count')
        .rename(columns={'index': 'sub'})
        .sort_values('sub')
    )
    
    results['by_contrast'] = (
        df_clean['contrast']
        .value_counts()
        .reset_index(name='file_count')
        .rename(columns={'index': 'contrast'})
    )
    
    results['by_run'] = (
        df_clean['run']
        .value_counts()
        .reset_index(name='file_count')
        .rename(columns={'index': 'run'})
        .sort_values('run')
    )
    
    # sess counts (if sessions exist)
    if df_clean['ses'].notna().any():
        results['by_session'] = (
            df_clean['ses']
            .value_counts()
            .reset_index(name='file_count')
            .rename(columns={'index': 'ses'})
            .sort_values('ses')
        )
    
    # cross-tabs
    results['subject_x_contrast'] = pd.crosstab(
        df_clean['sub'], df_clean['contrast'], margins=True
    )
    
    results['subject_x_run'] = pd.crosstab(
        df_clean['sub'], df_clean['run'], margins=True
    )
    
    results['run_x_contrast'] = pd.crosstab(
        df_clean['run'], df_clean['contrast'], margins=True
    )
    
    results['detailed_breakdown'] = (
        df_clean.groupby(['sub', 'run', 'contrast'])
        .size()
        .reset_index(name='count')
    )
    
    results['files_per_subject_run'] = (
        df_clean.groupby(['sub', 'run'])
        .size()
        .reset_index(name='file_count')
    )
    
    return results

def create_counts_dataframe_datalevel(parsed_files):
    """
    Create a DataFrame with counts for group-level analyses.

    Parameters:
        parsed_files: list of dictionaries from parse_bids_filename_robust

    Returns:
        Dictionary with multiple DataFrames for group-level count summaries
    """
    df = pd.DataFrame(parsed_files)
    df['ses'] = df['ses'].fillna('1')
    df['contrast'] = df['contrast'].apply(_clean_contrast)

    print(f"Total group-level files processed: {len(df)}")

    results = {
        'summary': {
            'total_files': len(df),
            'unique_sessions': df['ses'].nunique(),
            'unique_contrasts': df['contrast'].nunique()
        }
    }

    results['group_uniques'] = (
        df[['ses', 'contrast']]
        .drop_duplicates()
        .sort_values(['ses', 'contrast'])
        .reset_index(drop=True)
    )

    results['by_contrast'] = (
        df['contrast']
        .value_counts()
        .reset_index(name='file_count')
        .rename(columns={'index': 'contrast'})
    )

    results['by_session'] = (
        df['ses']
        .astype(str)
        .value_counts()
        .reset_index(name='file_count')
        .rename(columns={'index': 'ses'})
        .sort_values('ses')
        .reset_index(drop=True)
    )

    return results


def analyze_grouplvl(list_files):
    """
    Complete analysis pipeline for group-level BIDS files.
    
    Parameters:
        list_files: list of file paths
    
    Returns:
        Tuple of (parsed_files, counts_dict)
    """
    print("Parsing BIDS files...")
    parsed_files = process_file_list(list_files)
    
    print("Running counts...")
    counts_dict = create_counts_dataframe_datalevel(parsed_files)
    
    return parsed_files, counts_dict


def analyze_subjectlvl(list_files):
    """
    Complete analysis pipeline for subject-level BIDS files.
    
    Parameters:
        list_files: list of file paths
    
    Returns:
        Tuple of (parsed_files, counts_dict)
    """
    print("Parsing BIDS files...")
    parsed_files = process_file_list(list_files)
    
    print("Running counts...")
    counts_dict = create_counts_dataframe(parsed_files)
    
    return parsed_files, counts_dict


FILE_SUFFIX = "effect_statmap.nii.gz"  # produced for each successful run at all three levels
MODEL_LEVELS = ("runLevel", "subjectLevel", "dataLevel")


def summarize_fit_outputs(analysis_dir, file_suffix=FILE_SUFFIX, model_levels=MODEL_LEVELS, out_dir=None):
    """Print per-level unique counts for ``analysis_dir`` (e.g. analyses/ds003425/task-learning).

    If ``out_dir`` is given, each level's table is also written to ``<out_dir>/<level>_uniques.tsv``.
    Returns {level: DataFrame}.
    """
    analysis_dir = Path(analysis_dir)
    tables = {}
    for mod in model_levels:
        node_folder = analysis_dir / f"node-{mod}"
        if not node_folder.exists():
            print(f"Skipping {mod}: folder not found: {node_folder}")
            continue
        file_list = list(node_folder.rglob(f"*{file_suffix}"))
        if not file_list:
            print(f"No files found for {mod} in {node_folder}")
            continue
        print(f"Processing {len(file_list)} files for {mod}...")
        if mod in ("runLevel", "subjectLevel"):
            _, counts_analysis = analyze_subjectlvl(file_list)
            df_uniques = pd.DataFrame(counts_analysis.get("subject_uniques", []))
        else:
            _, counts_analysis = analyze_grouplvl(file_list)
            df_uniques = pd.DataFrame(counts_analysis.get("group_uniques", []))
        if df_uniques.empty:
            print(f"No unique combinations found for {mod}")
            continue
        print(df_uniques.to_string(index=False))
        tables[mod] = df_uniques
        if out_dir:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            df_uniques.to_csv(Path(out_dir) / f"{mod}_uniques.tsv", sep="\t", index=False)
    return tables
