"""Build BIDS Stats Models graphs to check a spec against the data (design-matrix columns)."""

import copy
from collections import defaultdict
from typing import Any, Callable, List, Optional, Tuple

from bids.layout import BIDSLayout, BIDSLayoutIndexer
from bids.modeling import BIDSStatsModelsGraph


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
            
            
            return None

    except Exception as e:
        print(f"ERROR: Failed to get run_level node: {e}")
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
