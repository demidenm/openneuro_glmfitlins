"""Per-task subject/run count figures for the study README (stage 1)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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
    plt.close(fig)
    
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
    plt.close(fig)
    
    return output_filename
