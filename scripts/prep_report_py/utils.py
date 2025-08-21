import os
import nbformat
import re
import json
import copy
import pandas as pd
import numpy as np
from collections import defaultdict
from pathlib import Path
from typing import List, Optional, Tuple, Callable, Any
from IPython.display import display, Markdown
from bids.modeling import BIDSStatsModelsGraph
from bids.layout import BIDSLayout, BIDSLayoutIndexer
from nilearn.interfaces.bids import parse_bids_filename
from nilearn.image import index_img, load_img, new_img_like, mean_img
from nilearn.glm import expression_to_contrast_vector
from pyrelimri import similarity
import matplotlib.pyplot as plt


# Metadata

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

def get_bidstats_events(bids_path, spec_cont, scan_length=125, ignored=None, return_events_num=0):
    """
    Initializes a BIDS layout, processes a BIDSStatsModelsGraph, 
    and returns a DataFrame of the first collection's entities.

    Parameters:
    - bids_inp (str): Path to the BIDS dataset.
    - spec_cont: Specification content for BIDSStatsModelsGraph.
    - scan_length (int, optional): Scan length parameter for load_collections. Default is 125.
    - ignored (list, optional): List of regex patterns to ignore during indexing.
    - return_events_num (int, optional): Number of events to return. Default is 0.

    Returns:
    - DataFrame: Data representation of the first collection with entities, or None if errors occur.
    """
    try:
        indexer = BIDSLayoutIndexer(ignore=ignored) if ignored else BIDSLayoutIndexer()
    except Exception as e:
        print(f"Error initializing BIDSLayoutIndexer: {e}")
        return None

    try:
        bids_layout = BIDSLayout(root=bids_path, reset_database=True, indexer=indexer)
    except Exception as e:
        print(f"Error initializing BIDSLayout: {e}")
        return None

    try:
        graph = BIDSStatsModelsGraph(bids_layout, spec_cont)
        graph.load_collections(scan_length=scan_length)
    except Exception as e:
        print(f"Error creating or loading BIDSStatsModelsGraph: {e}")
        return None

    try:
        root_node = graph.root_node
        colls = root_node.get_collections()
        if not colls:
            raise ValueError("No collections found in the root node.")
        return colls[return_events_num].to_df(entities=True), root_node, graph
    except Exception as e:
        print(f"Error processing root node collections: {e}")
        return None


def debug_bids_consistency(bids_path, spec_cont, scan_length=125, ignored=None):
    """
    Debug BIDS layout by checking:
    1. Subject entity index mapping
    2. Data consistency for specified task and subjects
    """
    
    
    try:
        indexer = BIDSLayoutIndexer(ignore=ignored) if ignored else BIDSLayoutIndexer()
        bids_layout = BIDSLayout(root=bids_path, reset_database=True, indexer=indexer)
        print(f"✓ BIDS Layout initialized: {bids_path}")
    except Exception as e:
        print(f"ERROR: Failed to initialize BIDS layout: {e}")
        return None


    # Get basic layout info
    all_subjects = bids_layout.get_subjects()
    all_tasks = bids_layout.get_tasks()
    all_runs = bids_layout.get_runs()

    print("\n=== MODEL SPECIFICATION ANALYSIS ===")
    
    # Extract info from model spec
    spec_subjects = spec_cont.get('Input', {}).get('subject', [])
    spec_tasks = spec_cont.get('Input', {}).get('task', [])
    spec_runs = spec_cont.get('Input', {}).get('run', [])
    
    print(f"Model expects:")
    print(f"  Subjects: {len(spec_subjects)} - {spec_subjects[:5]}...")
    print(f"  Tasks: {spec_tasks}")
    print(f"  Runs: {spec_runs}")
    
    # Check subject overlap
    spec_subjects_set = set(spec_subjects)
    layout_subjects_set = set(all_subjects)
    
    missing_in_layout = spec_subjects_set - layout_subjects_set
    missing_in_spec = layout_subjects_set - spec_subjects_set
    
    print(f"\nSubject comparison:")
    print(f"  In spec but not in layout: {len(missing_in_layout)} - {list(missing_in_layout)[:5]}")
    print(f"  In layout but not in spec: {len(missing_in_spec)} - {list(missing_in_spec)[:5]}")

    print("\n=== DATA CONSISTENCY CHECK ===")
    
    # For the main task, check data consistency
    target_task = spec_tasks[0] if spec_tasks else None
    if not target_task:
        print("No target task specified in model")
        return None
        
    print(f"Checking data consistency for task: {target_task}")
    
    # Get all files for this task
    data_summary = defaultdict(lambda: defaultdict(list))
    
    for subject in spec_subjects:
        # Check BOLD files
        bold_files = bids_layout.get(
            subject=subject, 
            task=target_task, 
            suffix='bold', 
            extension='.nii.gz'
        )
        
        # Check events files  
        events_files = bids_layout.get(
            subject=subject,
            task=target_task,
            suffix='events',
            extension='.tsv'
        )
        
        for bf in bold_files:
            run = bf.get_entities().get('run', 'no_run')
            data_summary[subject]['bold'].append(run)
            
        for ef in events_files:
            run = ef.get_entities().get('run', 'no_run') 
            data_summary[subject]['events'].append(run)
    
    # Analyze consistency
    print(f"\nData consistency analysis:")
    
    consistent_subjects = []
    problematic_subjects = []
    
    expected_runs = set(spec_runs)
    
    for subject in spec_subjects:
        bold_runs = set(data_summary[subject]['bold'])
        events_runs = set(data_summary[subject]['events'])
        
        # Check if subject has expected runs
        has_all_bold = expected_runs.issubset(bold_runs)
        has_all_events = expected_runs.issubset(events_runs)
        runs_match = bold_runs == events_runs
        
        if has_all_bold and has_all_events and runs_match:
            consistent_subjects.append(subject)
        else:
            problematic_subjects.append({
                'subject': subject,
                'bold_runs': sorted(bold_runs),
                'events_runs': sorted(events_runs), 
                'expected_runs': sorted(expected_runs),
                'missing_bold': sorted(expected_runs - bold_runs),
                'missing_events': sorted(expected_runs - events_runs)
            })
    
    print(f"  Consistent subjects: {len(consistent_subjects)}/{len(spec_subjects)}")
    print(f"  Problematic subjects: {len(problematic_subjects)}")
    
    if problematic_subjects:
        print(f"\nFirst 10 problematic subjects:")
        for i, prob in enumerate(problematic_subjects[:10]):
            print(f"  {prob['subject']}:")
            print(f"    BOLD runs: {prob['bold_runs']}")
            print(f"    Events runs: {prob['events_runs']}")
            if prob['missing_bold']:
                print(f"    Missing BOLD: {prob['missing_bold']}")
            if prob['missing_events']:
                print(f"    Missing events: {prob['missing_events']}")
            print()
    
    return {
        'consistent_subjects': consistent_subjects,
        'problematic_subjects': problematic_subjects,
    }


def spectest_subject_batches(bids_inp: str, base_spec: dict, get_bidstats_events: 
    Callable, TR: int = 2, volumes: int = 250, max_batch_size: int = 10) -> List[str]:
    """
    Test BIDS model with adaptive batch sizes to efficiently identify problematic subjects.
    
    Parameters
    ----------
    bids_inp : str
        BIDS input path/layout.
    base_spec : dict
        Original test_spec dictionary.
    get_bidstats_events : callable
        Function for retrieving BIDS stats events.
    TR : int, optional
        Repetition time (default: 2).
    volumes : int, optional
        Number of volumes (default: 250).
    max_batch_size : int, optional
        Maximum subjects per batch (default: 10).
        
    Returns
    -------
    List[str]
        List of problematic subjects identified.
    """

    def test_batch(subjects_batch: List[str], batch_name: str) -> Tuple[bool, Optional[str]]:
        """Run the model on a batch of subjects and report success/failure."""
        print(f"\nTesting {batch_name}: {subjects_batch}")
        
        batch_spec = copy.deepcopy(base_spec)
        batch_spec["Input"]["subject"] = subjects_batch

        try:
            _, root_mod, _ = get_bidstats_events(
                bids_inp, 
                batch_spec, 
                scan_length=volumes * TR, 
                ignored=[r"sub-.*_physio\.(json|tsv\.gz)"], 
                return_events_num=0
            )

            if root_mod is None:
                print(f"❌ FAILED: {subjects_batch} - No root model returned")
                return False, "No root model returned"

            root_mod.run(
                group_by=root_mod.group_by, 
                force_dense=False, 
                transformation_history=True
            )
            
            print(f"✅ SUCCESS: {subjects_batch}")
            return True, None

        except Exception as e:
            print(f"❌ FAILED: {subjects_batch}")
            print(f"   Error: {e}")
            return False, str(e)

    def binary_search_problems(subjects_batch: List[str], batch_name: str) -> List[str]:
        """Recursively find problematic subjects in a failed batch."""
        if len(subjects_batch) == 1:
            print(f"⚠️ Problematic subject identified: {subjects_batch[0]}")
            return subjects_batch

        mid = len(subjects_batch) // 2
        left_batch = subjects_batch[:mid]
        right_batch = subjects_batch[mid:]
        problematic_subjects = []

        # Test left batch
        if left_batch:
            success, _ = test_batch(left_batch, f"{batch_name}_left")
            if not success:
                problematic_subjects.extend(
                    binary_search_problems(left_batch, f"{batch_name}_left")
                )

        # Test right batch
        if right_batch:
            success, _ = test_batch(right_batch, f"{batch_name}_right")
            if not success:
                problematic_subjects.extend(
                    binary_search_problems(right_batch, f"{batch_name}_right")
                )

        return problematic_subjects

    # Validate inputs
    if not base_spec.get("Input", {}).get("subject"):
        print("ERROR: No subjects found in base_spec")
        return []

    subjects = base_spec["Input"]["subject"]
    total_subjects = len(subjects)

    if total_subjects == 0:
        print("ERROR: Empty subjects list")
        return []

    # Choose starting batch size
    if total_subjects <= 15:
        initial_batch_size = 2
    elif total_subjects < 30:
        initial_batch_size = 5
    else:
        initial_batch_size = min(max_batch_size, total_subjects // 4)

    print(f"Testing {total_subjects} subjects in batches of {initial_batch_size}...")
    print("=" * 60)

    all_problematic_subjects = []

    # Process batches
    for batch_num, i in enumerate(range(0, total_subjects, initial_batch_size), start=1):
        batch = subjects[i:i + initial_batch_size]
        batch_name = f"batch_{batch_num}"

        success, _ = test_batch(batch, batch_name)

        if not success:
            print("   Batch failed, using binary search to identify problematic subjects...")
            problematic = binary_search_problems(batch, batch_name)
            all_problematic_subjects.extend(problematic)

    # Summary
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    if all_problematic_subjects:
        print(f"⚠️ Problematic subjects found: {all_problematic_subjects}")
    else:
        print("✅ No problematic subjects found")

    return all_problematic_subjects


def get_runnode(bids_path: str, spec_cont: dict, scan_length: int = 125, ignored: Optional[List[str]] = None) -> Optional[Any]:
    """
    Enhanced version that runs debugging first, then attempts model creation.
    
    Parameters
    ----------
    bids_path : str
        Path to BIDS dataset.
    spec_cont : dict
        Model specification container.
    scan_length : int, optional
        Length of scan in TRs (default: 125).
    ignored : List[str], optional
        List of patterns to ignore when indexing.
        
    Returns
    -------
    Optional[Any]
        Run specifications if successful, None otherwise.
    """
    
    print("=== RUNNING CONSISTENCY DEBUGGING ===")
    
    # Run debugging if function exists
    try:
        debug_info = debug_bids_consistency(bids_path, spec_cont, scan_length, ignored)
        
        if debug_info:
            print(f"\n=== SUMMARY ===")
            print(f"Consistent subjects: {len(debug_info.get('consistent_subjects', []))}")
            print(f"Problematic subjects: {len(debug_info.get('problematic_subjects', []))}")
        else:
            print("Debugging failed, proceeding with limited information")
    except NameError:
        print("Warning: debug_bids_consistency function not available, skipping debugging")
        debug_info = None
    except Exception as e:
        print(f"Warning: Debugging failed with error: {e}")
        debug_info = None
        
    # Initialize BIDSLayoutIndexer
    try:
        indexer = BIDSLayoutIndexer(ignore=ignored) if ignored else BIDSLayoutIndexer()
    except Exception as e:
        print(f"ERROR: Failed to initialize BIDSLayoutIndexer: {e}")
        return None

    # Initialize BIDSLayout
    try:
        bids_layout = BIDSLayout(root=bids_path, reset_database=True, indexer=indexer)
    except Exception as e:
        print(f"ERROR: Failed to initialize BIDSLayout: {e}")
        print(f"Check that the BIDS directory exists and is valid: {bids_path}")
        return None

    # Create BIDSStatsModelsGraph
    try:
        graph = BIDSStatsModelsGraph(bids_layout, spec_cont)
    except Exception as e:
        print(f"ERROR: Failed to create BIDSStatsModelsGraph: {e}")
        if "'Dict' nodes are not implemented" in str(e):
            print("This error typically occurs with DummyContrasts specification.")
            print("Try removing subject/dataset level nodes or check the BIDSStatsModelsGraph implementation.")
        return None

    # Get run level node
    try:
        _, run_level_node, _ = get_bidstats_events(
            bids_path, 
            spec_cont, 
            scan_length, 
            ignored, 
            return_events_num=0
        )
        
        if run_level_node is None:
            print("ERROR: Could not find 'run_level' node in the model specification")
            available_nodes = [node.name for node in graph.nodes]
            print(f"Available nodes: {available_nodes}")
            
            # Run batch testing as fallback
            print("\n=== RUNNING BATCH TESTING AS FALLBACK ===")
            try:
                problematic_subjects = spectest_subject_batches(
                    bids_path, 
                    spec_cont,
                    get_bidstats_events, 
                    TR=2,
                    volumes=scan_length,
                    max_batch_size=10
                )
                
                if problematic_subjects:
                    print(f"Batch testing completed. Problematic subjects: {problematic_subjects}")
                else:
                    print("Batch testing completed. No problematic subjects found.")
                    
            except Exception as batch_e:
                print(f"ERROR: Batch testing also failed: {batch_e}")
            return None

    except Exception as e:
        print(f"ERROR: Failed to get run_level node: {e}")
        
        # Run batch testing as fallback
        print("\n=== RUNNING BATCH TESTING AS FALLBACK ===")
        try:
            problematic_subjects = spectest_subject_batches(
                bids_path, 
                spec_cont,
                get_bidstats_events, 
                TR=2,
                volumes=scan_length,
                max_batch_size=10
            )
            
            if problematic_subjects:
                print(f"Batch testing completed. Problematic subjects: {problematic_subjects}")
            else:
                print("Batch testing completed. No problematic subjects found.")
                
        except Exception as batch_e:
            print(f"ERROR: Batch testing also failed: {batch_e}")
        return None

    # Run the model
    try:
        run_specs = run_level_node.run(
            group_by=run_level_node.group_by,
            force_dense=False,
            transformation_history=True
        )
        return run_specs

    except TypeError as e:
        if "'<' not supported between instances of 'str' and 'float'" in str(e):
            print("ERROR: Mixed data types found in 'amplitude' column.")
            print("This suggests that columns being Factored and convolved have a combination of numeric and string values.")
            print("TYPICAL CAUSES:")
            print("1. NA/NaN values in the columns being factored/convolved")
            print("2. Mixed data types in event files (e.g., some values are strings, others are numbers)")
            print("3. Inconsistent formatting across event files")
            print("\nSUGGESTED FIXES:")
            print("- Check your *_events.tsv files for missing values or inconsistent data types")
            print("- Ensure all numeric columns contain only numeric values or are properly handled")
            print("- Consider using pandas to clean your events files before running the model")
            return None
        else:
            print(f"ERROR: TypeError in run_level_node.run(): {e}")
            raise
    except Exception as e:
        print(f"ERROR: Failed to run the model: {e}")
        print("This could be due to:")
        print("- Missing or malformed event files")
        print("- Incompatible model specification with your data")
        print("- Missing required columns in events files")
        return None


def extract_model_info(model_spec):
    """
    Extracts subject numbers, node levels, convolve model type, regressors, and contrasts from a BIDS model specification,
    and multiplies each condition by its corresponding weight.

    Parameters:
    model_spec (dict): The BIDS model specification dictionary.

    Returns:
    dict: A dictionary containing the extracted information, including weighted conditions.
    """

    extracted_info = {
        "subjects": model_spec.get("Input", {}).get("subject", []),
        "nodes": [],
    }

    for node in model_spec.get("Nodes", []):
        node_info = {
            "level": node.get("Level"),
            "regressors": node.get("Model", {}).get("X", []),
            "contrasts": [
                {
                    "name": contrast.get("Name", "Unnamed Contrast"),
                    "conditions": contrast.get("ConditionList", []),
                    "weights": contrast.get("Weights", []),
                    "test": contrast.get("Test", "t")  # Default test type to "t"
                }
                for contrast in node.get("Contrasts", [])
            ],
            "convolve_model": "spm",  # Default value spm
            "convolve_inputs": [],            # Obtain regressors that were convolved
            "if_derivative_hrf": False,    # Track if HRF derivative is used
            "if_dispersion_hrf": False,    # Track if HRF dispersion is used
            "target_var": [] # Track values receiving an assignment duration (e.g. not parametric)
        }

        # Extract HRF convolution model type and derivative status
        transformations = node.get("Transformations", {}).get("Instructions", [])
        for instruction in transformations:
            if instruction.get("Name") == "Convolve":
                node_info["convolve_model"] = instruction.get("Model", "Unknown")
                node_info["if_derivative_hrf"] = instruction.get("Derivative", False) == True
                node_info["if_dispersion_hrf"] = instruction.get("Dispersion", False) == True
                node_info["convolve_inputs"] = instruction.get("Input", [])
                break  # Stop searching after finding first Convolve transformation
            
            if instruction.get("Name") == "Assign" and instruction.get("TargetAttr") == "duration":
                targets = instruction.get("Target", [])
                if isinstance(targets, str):
                    targets = [targets]
                node_info["target_var"].extend(targets)

        extracted_info["nodes"].append(node_info)
    
    return extracted_info


# Plotting

def create_task_plots(taskname, subj_data, sess_list, output_dir):
    """
    Generate and save comprehensive plots for basic details figure
    Parameters:
    -----------
    task_name : str
        Name of the task
    subj_data : dict
        Dictionary with session keys and DataFrames containing subject/run info
    sess_list : list
        List of sessions
    output_dir : str
        Directory to save plots
        
    Returns:
    --------
    None
    """
    # a single comprehensive figure for all cases
    if sess_list and len(sess_list) > 1:
        return _create_multi_session_plots(taskname, subj_data, sess_list, output_dir)
    else:
        return _create_single_session_plots(taskname, subj_data, output_dir)


def _create_multi_session_plots(task_name, subject_data_by_session, sessions, output_dir):
    """Create 3-panel plot for multi-session data."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    
    session_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    # Collect data for all sessions
    session_subject_counts = {}
    all_run_counts = {}
    
    for i, (session_key, df) in enumerate(subject_data_by_session.items()):
        if df.empty:
            continue
        
        color = session_colors[i % len(session_colors)]
        run_counts = df['num_runs'].value_counts().sort_index()
        
        session_subject_counts[session_key] = len(df)
        all_run_counts[session_key] = run_counts
        
        # Plot 1: Subject count by session
        ax1.bar(i, len(df), color=color, edgecolor='black', label=f'Session {session_key}')
    
    # Configure Plot 1: Subject counts
    ax1.set_xlabel('')
    ax1.set_ylabel('Num Subjects')
    ax1.set_title(f'Subject Count by Session - {task_name}')
    ax1.set_xticks(range(len(session_subject_counts)))
    ax1.set_xticklabels([f'Session {s}' for s in session_subject_counts.keys()])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Plot 2: Run distribution comparison
    max_runs = max([max(rncnt.index) if len(rncnt) > 0 else 0 for rncnt in all_run_counts.values()])
    for i, (session_key, run_counts) in enumerate(all_run_counts.items()):
        color = session_colors[i % len(session_colors)]
        x_pos = np.arange(1, max_runs + 1) + i * 0.35
        run_values = [run_counts.get(j, 0) for j in range(1, max_runs + 1)]
        ax2.bar(x_pos, run_values, width=0.3, color=color, edgecolor='black', label=f'Session {session_key}')
    
    ax2.set_xlabel('Num Runs')
    ax2.set_ylabel('Num Subjects')
    ax2.set_title(f'Run Frequency Dist Across Subjects - {task_name}')
    ax2.set_xticks(np.arange(1, max_runs + 1) + 0.175)
    ax2.set_xticklabels(range(1, max_runs + 1))
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    # Plot 3: Combined run pattern frequencies across all sessions
    combined_df = pd.concat([df for df in subject_data_by_session.values() if not df.empty], ignore_index=True)
    run_lists = combined_df['run_numbers'].value_counts().sort_index()
    
    ax3.bar(range(len(run_lists)), run_lists.values, color='maroon', edgecolor='black')
    ax3.set_xlabel('')
    ax3.set_ylabel('Frequency')
    ax3.set_title(f'Count Run List Patterns - {task_name}')
    ax3.set_xticks(range(len(run_lists)))
    ax3.set_xticklabels(run_lists.index, rotation=45, ha='right')
    ax3.grid(axis='y', alpha=0.3)
    
    filename_suffix = f"{task_name}_session_summary"
    
    plt.tight_layout()
    
    # Save the plot
    output_filename = Path(output_dir) / f"{filename_suffix}.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.show()
    
    return output_filename


def _create_single_session_plots(task_name, subject_data_by_session, output_dir):
    """Create 3-panel plot for single session data."""
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    
    # Get the single dataframe
    df = list(subject_data_by_session.values())[0]
    run_counts = df['num_runs'].value_counts().sort_index()
    run_lists = df['run_numbers'].value_counts().sort_index()
    
    # Plot 1: Total subject count
    ax1.bar([0], [len(df)], color='darkblue', edgecolor='black')
    ax1.set_xlabel('Dataset')
    ax1.set_ylabel('Number of Subjects')
    ax1.set_title(f'Total Subjects - {task_name}')
    ax1.set_xticks([0])
    ax1.set_xticklabels([task_name])
    ax1.grid(axis='y', alpha=0.3)
    
    # Plot 2: Run frequency distribution
    ax2.bar(run_counts.index, run_counts.values, color='black', edgecolor='black')
    ax2.set_xlabel('Num Runs')
    ax2.set_ylabel('Num Subjects')
    ax2.set_title(f'Run Frequency Dist Across Subjects - {task_name}')
    ax2.set_xticks(run_counts.index)
    ax2.grid(axis='y', alpha=0.3)
    
    # Plot 3: Run patterns frequency
    run_lists = df['run_numbers'].value_counts().sort_index()
    
    ax3.bar(range(len(run_lists)), run_lists.values, color='maroon', edgecolor='black')
    ax3.set_xlabel('')
    ax3.set_ylabel('Frequency')
    ax3.set_title(f'Count Run List Patterns - {task_name}')
    ax3.set_xticks(range(len(run_lists)))
    ax3.set_xticklabels(run_lists.index, rotation=45, ha='right')
    ax3.grid(axis='y', alpha=0.3)

    filename_suffix = f"{task_name}_summary"
    
    plt.tight_layout()
    
    # Save the plot
    output_filename = Path(output_dir) / f"{filename_suffix}.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.show()
    
    return output_filename



# transforming data

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
    
    # load nifti & trim
    try:
        img = load_img(bold_path)
        total_vols = img.shape[3] if len(img.shape) == 4 else None
        if total_vols is None:
            raise ValueError(f"Invalid NIfTI file: {bold_path}")
        
        print("Trimming {} volumes from {} volumes".format(num_voltotrim, total_vols))
        trimmed_img = index_img(img, slice(num_voltotrim, None))

    except Exception as e:
        raise ValueError(f"Error loading NIfTI file: {e}")    
    
    return trimmed_img


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


# readme creation

def generate_tablecontents(notebook_name):
    """Generate a Table of Contents from markdown headers in the current Jupyter Notebook."""
    toc = ["# Table of Contents\n"]

    # Get the current notebook name dynamically
    notebook_file = Path.cwd() / notebook_name
    
    if not notebook_file:
        print("No notebook file found in the directory.")
        return
    
    # Load the notebook content
    with open(notebook_file, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    for cell in notebook.cells:
        if cell.cell_type == "markdown":  # Only process markdown cells
            lines = cell.source.split("\n")
            for line in lines:
                match = re.match(r"^(#+)\s+([\d.]+)?\s*(.*)", line)  # Match headers with optional numbering
                if match:
                    level = len(match.group(1))  # Number of `#` determines header level
                    header_number = match.group(2) or ""  # Capture section number if present
                    header_text = match.group(3).strip()  # Extract actual text
                    
                    # Format the anchor link correctly for Jupyter:
                    # 1. Keep original casing
                    # 2. Preserve periods
                    # 3. Replace spaces with hyphens
                    # 4. Remove special characters except `.` and `-`
                    anchor = f"{header_number} {header_text}"
                    anchor = anchor.replace(" ", "-")  # Convert spaces to hyphens
                    anchor = re.sub(r"[^\w.\-]", "", anchor)  # Remove special characters except `.` and `-`

                    toc.append(f"{'  ' * (level - 1)}- [{header_number} {header_text}](#{anchor})")

    # diplay table of contents in markdown
    display(Markdown("\n".join(toc)))


# file creation: functions for subjects and contrasts generic files
def create_subjects_json(subj_list, studyid, taskname, specpath):
    subjects_file_path = Path(specpath) / f'{studyid}-{taskname}_subjects.json'
    subjects_data = {
        "Subjects": subj_list
    }
    with open(subjects_file_path, 'w') as f:
        json.dump(subjects_data, f, indent=4)
    print(f"\t\tSaved subjects file for task {taskname} to {subjects_file_path}")

def create_gencontrast_json(studyid, taskname, specpath):
    contrasts_file_path = Path(specpath) / f'{studyid}-{taskname}_contrasts.json'
    contrasts_data = {
        "Contrasts": [
            {
                "Name": "AvB",
                "ConditionList": ["trial_type.a", "trial_type.b"],
                "Weights": [1, -1],
                "Test": "t"
            },
            {
                "Name": "FacesvPlaces",
                "ConditionList": ["trial_type.faces", "trial_type.places"],
                "Weights": [1, -1],
                "Test": "t"
            }
        ]
    }
    with open(contrasts_file_path, 'w') as f:
        json.dump(contrasts_data, f, indent=4)
    print(f"\t\tSaved contrasts file for task {taskname} to {contrasts_file_path}")


# parameter estimation

# below est_contrast_vifs code is courtsey of Jeanette Mumford's repo: https://github.com/jmumford/vif_contrasts
def est_contrast_vifs(desmat, contrasts):
    """
    IMPORTANT: This is only valid to use on design matrices where each regressor represents a condition vs baseline
     or if a parametrically modulated regressor is used the modulator must have more than 2 levels.  If it is a 2 level modulation,
     split the modulation into two regressors instead.

    Calculates VIF for contrasts based on the ratio of the contrast variance estimate using the
    true design to the variance estimate where between condition correaltions are set to 0
    desmat : pandas DataFrame, design matrix
    contrasts : dictionary of contrasts, key=contrast name,  using the desmat column names to express the contrasts
    returns: pandas DataFrame with VIFs for each contrast
    """
    desmat_copy = desmat.copy()
    # find location of constant regressor and remove those columns (not needed here)
    desmat_copy = desmat_copy.loc[
        :, (desmat_copy.nunique() > 1) | (desmat_copy.isnull().any())
    ]
    # Scaling stabilizes the matrix inversion
    nsamp = desmat_copy.shape[0]
    desmat_copy = (desmat_copy - desmat_copy.mean()) / (
        (nsamp - 1) ** 0.5 * desmat_copy.std()
    )
    vifs_contrasts = {}
    for contrast_name, contrast_string in contrasts.items():
        try:
            contrast_cvec = expression_to_contrast_vector(
                contrast_string, desmat_copy.columns
            )
            true_var_contrast = (
                contrast_cvec
                @ np.linalg.inv(desmat_copy.transpose() @ desmat_copy)
                @ contrast_cvec.transpose()
            )
            # The folllowing is the "best case" scenario because the between condition regressor correlations are set to 0
            best_var_contrast = (
                contrast_cvec
                @ np.linalg.inv(
                    np.multiply(
                        desmat_copy.transpose() @ desmat_copy,
                        np.identity(desmat_copy.shape[1]),
                    )
                )
                @ contrast_cvec.transpose()
            )
            vifs_contrasts[contrast_name] = true_var_contrast / best_var_contrast
        except Exception as e:
            print(f"Error computing VIF for regressor '{contrast_name}': {e}")

    return vifs_contrasts


def gen_vifdf(designmat, contrastdict, nuisance_regressors):
    """
    Create a Pandas DataFrame with VIF values for contrasts and regressors.

    Parameters
    designmat: The design matrix used in the analysis.
    modconfig (dict): A dictionary containing model configuration, including:
        - 'nuisance_regressors': A regex pattern to filter out nuisance regressors.
           - 'contrasts': A dictionary of contrast definitions.

    Returns
    Returns contrasts & regressors vif dict & DataFrame of combined VIFs w/ columns ['type', 'name', 'value'].
    """
    filtered_columns = designmat.columns[~designmat.columns.isin(nuisance_regressors)]
    regressor_dict = {item: item for item in filtered_columns if item != "intercept"}

    
    # est VIFs for contrasts and regressors
    con_vifs = est_contrast_vifs(desmat=designmat, contrasts=contrastdict)
    reg_vifs = est_contrast_vifs(desmat=designmat, contrasts=regressor_dict)

    # convert to do
    df_con = pd.DataFrame(list(con_vifs.items()), columns=["name", "value"])
    df_con["type"] = "contrast"
    df_reg = pd.DataFrame(list(reg_vifs.items()), columns=["name", "value"])
    df_reg["type"] = "regressor"

    # combine & rename cols
    df = pd.concat([df_con, df_reg], ignore_index=True)
    df = df[["type", "name", "value"]]

    return con_vifs,reg_vifs,df


def calc_niftis_meanstd(path_imgs):
    """
    Calculate the mean & standard deviation across a list of NIfTI images.

    Parameters:
    - images_paths: List of paths to NIfTI images.

    Returns:
    NIfTI Image for mean and std in position 1 , 2
    """
    # if path_imgs list is empty
    assert len(path_imgs) > 0, "Error: The list of image paths is empty."

    # load ref image to obtain header info
    reference_img = load_img(path_imgs[0])
    
    # load / stack image data
    loaded_images = [load_img(img_path).get_fdata() for img_path in path_imgs]
    img_data_array = np.array(loaded_images)

    # data array is not empty and has more than 1 image
    assert img_data_array.size > 0, "Error: No valid image data were loaded."
    assert img_data_array.shape[0] > 1, "Error: At least two images are required for mean and std calculation."

    # calculate the mean and std across images (axis=0)
    mean_imgs = np.mean(img_data_array, axis=0)
    std_imgs = np.std(img_data_array, axis=0, ddof=1)  # ddof=1 for sample std

    # Create NIfTI images for the mean and std
    mean_nifti = new_img_like(reference_img, mean_imgs)
    std_nifti = new_img_like(reference_img, std_imgs)

    return mean_nifti, std_nifti


def voxel_inout_ratio(img_path, mask_path):
    """
    Calculates the percentage of non-zero voxels inside and outside a brain mask 
    for a given image

    Parameters:
    img_path (str): Path to the NIfTI image file.
    mask_path (str): Path to the corresponding brain mask (same space).

    Returns:
    percent_inside: Percentage of non-zero voxels inside the brain mask.
    percent_outside: Percentage of non-zero voxels outside the brain mask.
    ratio_invout: ratio of inside versus outside 
    """
    img_nifit = load_img(img_path)
    mask_nifti = load_img(mask_path)

    # extract numpy arrays & get nonzeros
    img_data = img_nifit.get_fdata()
    mask_data = mask_nifti.get_fdata() > 0      
    nonzero_inside = np.count_nonzero(img_data[mask_data])
    nonzero_outside = np.count_nonzero(img_data[~mask_data])
    total_nonzero = nonzero_inside + nonzero_outside

    # percentages and ratio
    percent_inside = (nonzero_inside / total_nonzero) * 100 if total_nonzero != 0 else 0
    percent_outside = (nonzero_outside / total_nonzero) * 100 if total_nonzero != 0 else 0
    ratio_invout = percent_inside / percent_outside if percent_outside != 0 else float('inf')

    return percent_inside, percent_outside, ratio_invout


def similarity_boldstand_metrics(img_path, brainmask_path):
    # Parse filename to extract BIDS info
    parsed_dat = parse_bids_filename(img_path)
    parts = []
    if 'sub' in parsed_dat:
        parts.append(f"sub-{parsed_dat['sub']}")
    if 'ses' in parsed_dat:
        parts.append(f"ses-{parsed_dat['ses']}")
    if 'run' in parsed_dat:
        parts.append(f"run-{parsed_dat['run']}")

    sub_run_info = '_'.join(parts)
    
    # dice similarity
    dice_est = similarity.image_similarity(
        imgfile1=img_path,
        imgfile2=brainmask_path,
        mask=None,
        thresh=None,
        similarity_type='dice'
    )

    perc_in, perc_out, inout_ratio =  voxel_inout_ratio(img_path=img_path, mask_path=brainmask_path)

    # results as a dictionary
    return {
        "img1": sub_run_info,
        "img2": "mni152",
        "dice": dice_est,
        "voxinmask": perc_in,
        "voxoutmask": perc_out,
        "ratio_inoutmask": inout_ratio,
    }


def get_low_quality_subs(ratio_df, dice_thresh=0.85, voxout_thresh=0.10):
    """
    Get sorted list of low-quality image names based on: 'dice' score < dice_thresh & 'voxoutmask' > voxout_thresh

    Parameters:
    ratio_df: DataFrame with 'voxoutmask', 'dice', and 'img1' columns.
    dice_thresh: Threshold for the 'dice' metric.
    voxout_thresh: Threshold for the 'voxoutmask' metric.

    Returns:
    Sorted list of image names that fall below the quality thresholds.
    """
    low_quality = ratio_df[
        (ratio_df['dice'] < dice_thresh) &
        (ratio_df['voxoutmask'] > voxout_thresh)
    ]
    
    low_quality_imgs = sorted(low_quality['img1'].tolist())
    return low_quality_imgs


def analyze_file_sizes(events_list, size_threshold=0.5):
        """Analyze file sizes and identify suspiciously small files"""
        file_sizes = {}
        file_line_counts = {}
        small_file_alerts = []
        
        for event_file in events_list:
            try:
                subject = event_file.entities['subject']
                file_path = event_file.path
                
                # Get file size in bytes
                file_size = os.path.getsize(file_path)
                
                # Count lines in file (excluding header)
                try:
                    df = pd.read_csv(file_path, sep='\t')
                    line_count = len(df)
                except Exception as e:
                    # Fallback to simple line counting if pandas fails
                    with open(file_path, 'r') as f:
                        line_count = sum(1 for line in f) - 1  # Subtract header
                
                if subject not in file_sizes:
                    file_sizes[subject] = []
                    file_line_counts[subject] = []
                
                file_sizes[subject].append(file_size)
                file_line_counts[subject].append(line_count)
                
            except Exception as e:
                print(f"Error analyzing file size for {event_file.path}: {e}")
                continue
        
        # Calculate statistics and identify outliers
        all_sizes = [size for sizes in file_sizes.values() for size in sizes]
        all_line_counts = [count for counts in file_line_counts.values() for count in counts]
        
        if all_sizes:
            median_size = np.median(all_sizes)
            median_line_count = np.median(all_line_counts)
            size_threshold_bytes = median_size * size_threshold
            line_threshold = median_line_count * size_threshold
            
            # Flag subjects with suspiciously small files
            for subject, sizes in file_sizes.items():
                line_counts = file_line_counts[subject]
                
                for i, (size, lines) in enumerate(zip(sizes, line_counts)):
                    run_info = f"run-{i+1}" if len(sizes) > 1 else "single run"
                    
                    if size < size_threshold_bytes:
                        small_file_alerts.append(
                            f"⚠️ Subject {subject} ({run_info}): Event file suspiciously small "
                            f"({size} bytes vs median {median_size:.0f} bytes)"
                        )
                    
                    if lines < line_threshold:
                        small_file_alerts.append(
                            f"⚠️ Subject {subject} ({run_info}): Event file has low event counts"
                            f"({lines} events vs median {median_line_count:.0f} events)"
                        )
        
        return small_file_alerts, file_sizes, file_line_counts
        
# qc subjects' events files 
def eval_missing_events(dir_layout, taskname, size_threshold=0.5):
    """
    Evaluate missing event files, flag subjects with suspiciously small files,
    and check for missing corresponding BOLD files in a BIDS dataset.
    
    Parameters:
    dir_layout: BIDSLayout() object
    taskname: The name of the task to analyze
    size_threshold: Threshold for flagging small files (default 0.5 = files smaller than 50% of median)
        
    Returns:
    Dictionary containing analysis results for each session (or entire dataset if no sessions)
    """
    
    def check_missing_bold(event_file):
        """Return True if corresponding BOLD file is missing."""
        entities = event_file.entities
        subject = entities.get('subject')
        session = entities.get('session', None)
        task = entities.get('task')
        run = entities.get('run', None)
        
        bold_files = dir_layout.get(subject=subject,
                                    session=session,
                                    task=task,
                                    run=run,
                                    suffix='bold',
                                    extension=['.nii', '.nii.gz'])
        return len(bold_files) == 0
    
    all_subjects = dir_layout.get_subjects()
    sess_info = dir_layout.get_sessions(task=taskname)
    all_results = {}
    alerts = []
    
    print(f"Total subjects in dataset: {len(all_subjects)}")
    
    # Iterate over sessions if they exist
    if sess_info:
        print(f"\n_________ANALYZING TASK: *{taskname}* across {len(sess_info)} sessions: {sess_info}_________")
        for sess in sess_info:
            session_alerts = []
            print(f"\n=== Analysis for Session: {sess} ===")
            events_list = dir_layout.get(task=taskname, session=sess, suffix="events", extension=".tsv")
            subject_counts = {}
            file_sizes, file_line_counts = {}, {}
            
            # Analyze file sizes
            small_file_alerts, fsizes, flines = analyze_file_sizes(events_list, size_threshold)
            session_alerts.extend(small_file_alerts)
            file_sizes.update(fsizes)
            file_line_counts.update(flines)
            
            # Count event files and check BOLD for each subject
            for i, event_file in enumerate(events_list):
                try:
                    subject = event_file.entities['subject']
                    subject_counts[subject] = subject_counts.get(subject, 0) + 1
                    
                    # Check missing BOLD
                    if check_missing_bold(event_file):
                        run = event_file.entities.get('run', 'NA')
                        alert_msg = f"⚠️ Session {sess}: Subject {subject} run {run} has event file but NO corresponding BOLD file"
                        session_alerts.append(alert_msg)
                        print(alert_msg)
                        
                except (AttributeError, KeyError, IndexError) as e:
                    print(f"Error accessing subject for event file {event_file}: {e}")
                    continue
            
            # Calculate max events and incomplete subjects
            max_events = max(subject_counts.values()) if subject_counts else 0
            incomplete_subjects = {subj: count for subj, count in subject_counts.items() if count < max_events}
            
            # Subjects with no event files
            subjects_with_events = set(subject_counts.keys())
            subjects_without_events = set(all_subjects) - subjects_with_events
            
            # Count missing files
            total_missing_from_incomplete = sum(max_events - count for count in incomplete_subjects.values())
            total_missing_from_no_events = len(subjects_without_events) * max_events if max_events > 0 else len(subjects_without_events)
            total_missing = total_missing_from_incomplete + total_missing_from_no_events
            
            # Print results and generate alerts
            print(f"Subjects with {taskname} events in session {sess}: {len(subjects_with_events)}")
            print(f"Subjects without {taskname} events in session {sess}: {len(subjects_without_events)}")
            
            if incomplete_subjects:
                print("\nSubjects with incomplete event files:")
                for subject, count in incomplete_subjects.items():
                    missing_count = max_events - count
                    print(f"  {subject}: {count} event file(s) (missing N = {missing_count} runs)")
                    session_alerts.append(f"⚠️ Session {sess}: Subject {subject} is missing {missing_count} event file(s)")
            if subjects_without_events:
                print(f"\nSubjects with NO {taskname} event files:")
                for subject in sorted(subjects_without_events):
                    print(f"  Subject {subject}")
                    session_alerts.append(f"⚠️ Session {sess}: Subject {subject} has NO event files")
            
            # File size alerts
            if small_file_alerts:
                print(f"\nFile size/content alerts for session {sess}:")
                for alert in small_file_alerts:
                    print(f"  {alert}")
            
            # Store results
            all_results[sess] = {
                "max_events_per_subject": max_events,
                "subjects_with_events": subjects_with_events,
                "subjects_without_events": subjects_without_events,
                "incomplete_subjects": incomplete_subjects,
                "total_subjects": len(all_subjects),
                "subjects_with_events_count": len(subjects_with_events),
                "subjects_without_events_count": len(subjects_without_events),
                "incomplete_subjects_count": len(incomplete_subjects),
                "missing_files_from_incomplete": total_missing_from_incomplete,
                "missing_files_from_no_events": total_missing_from_no_events,
                "total_missing_files": total_missing,
                "file_sizes": file_sizes,
                "file_line_counts": file_line_counts,
                "small_file_alerts": small_file_alerts,
                "alerts": session_alerts
            }
            alerts.extend(session_alerts)
        
    # No session info — analyze entire dataset
    else:
        print(f"\n_________ANALYZING TASK: *{taskname}* (no sessions)_________")
        events_list = dir_layout.get(task=taskname, suffix="events", extension=".tsv")
        subject_counts = {}
        file_sizes, file_line_counts = {}, {}
        
        small_file_alerts, fsizes, flines = analyze_file_sizes(events_list, size_threshold)
        alerts.extend(small_file_alerts)
        file_sizes.update(fsizes)
        file_line_counts.update(flines)
        
        for event_file in events_list:
            try:
                subject = event_file.entities['subject']
                subject_counts[subject] = subject_counts.get(subject, 0) + 1
                
                if check_missing_bold(event_file):
                    run = event_file.entities.get('run', 'NA')
                    alert_msg = f"⚠️ Subject {subject} run {run} has event file but NO corresponding BOLD file"
                    alerts.append(alert_msg)
                    print(alert_msg)
                    
            except (AttributeError, KeyError, IndexError) as e:
                print(f"Error accessing subject for event file {event_file}: {e}")
                continue
        
        max_events = max(subject_counts.values()) if subject_counts else 0
        incomplete_subjects = {subj: count for subj, count in subject_counts.items() if count < max_events}
        subjects_with_events = set(subject_counts.keys())
        subjects_without_events = set(all_subjects) - subjects_with_events
        
        total_missing_from_incomplete = sum(max_events - count for count in incomplete_subjects.values())
        total_missing_from_no_events = len(subjects_without_events) * max_events if max_events > 0 else len(subjects_without_events)
        total_missing = total_missing_from_incomplete + total_missing_from_no_events
        
        # Return dataset-level results
        all_results = {
            "max_events_per_subject": max_events,
            "subjects_with_events": subjects_with_events,
            "subjects_without_events": subjects_without_events,
            "incomplete_subjects": incomplete_subjects,
            "total_subjects": len(all_subjects),
            "subjects_with_events_count": len(subjects_with_events),
            "subjects_without_events_count": len(subjects_without_events),
            "incomplete_subjects_count": len(incomplete_subjects),
            "missing_files_from_incomplete": total_missing_from_incomplete,
            "missing_files_from_no_events": total_missing_from_no_events,
            "total_missing_files": total_missing,
            "file_sizes": file_sizes,
            "file_line_counts": file_line_counts,
            "small_file_alerts": small_file_alerts,
            "alerts": alerts
        }
    
    # Summary
    print("\n_____Summary of All Issues_____")
    if alerts:
        print(f"Total alerts: {len(alerts)}")
        for alert in alerts:
            print(alert)
    else:
        print(f"No missing {taskname} files, small files, or missing BOLD detected.")
    
    return all_results

def pull_contrast_conditions_spec(spec_content):
    """
    get unique condition list values from spec content
    """
    condition_vals = set()
    
    # At node with contrasts, get condition lists
    for node in spec_content.get("Nodes", []):
        for contrast in node.get("Contrasts", []):
            condition_list = contrast.get("ConditionList", [])

            for condition in condition_list:
                condition_vals.add(condition)
                
    return sorted(list(condition_vals))