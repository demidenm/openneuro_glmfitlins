"""Checks on events files: missing runs/sessions, missing BOLD and suspiciously small files."""

import os

import numpy as np
import pandas as pd


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
