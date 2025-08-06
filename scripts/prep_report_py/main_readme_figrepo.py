import re
import json
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import argparse

plt.switch_backend('Agg')

# Set up argument parsing
parser = argparse.ArgumentParser(description="Provide OpenNeuro study variables")
parser.add_argument("--stats_modelspath", type=str, help="Path to spec/model outputs for datasets", required=True)
parser.add_argument("--outfolder", type=str, help="Path to save imgs/dataframe", required=True)

args = parser.parse_args()

# Set variables from arguments - convert to Path objects
models_dir = Path(args.stats_modelspath)
out_folder = Path(args.outfolder)

# Ensure output directory exists
out_folder.mkdir(parents=True, exist_ok=True)

# dataset IDs - use Path methods only
study_ids = [item.name for item in models_dir.iterdir() 
            if item.is_dir()]

# empty lists and iteration
data = []
all_contrasts = set()

for study_id in study_ids:
    study_path = models_dir / study_id
    
    if not study_path.exists():
        continue
        
    # all group_* directories
    group_dirs = list(study_path.glob("group_*"))
    
    # contrasts for this dataset
    study_contrasts = set()
    for group_dir in group_dirs:
        files_dir = group_dir / "files"
        if files_dir.exists():
            png_files = list(files_dir.glob("*.png"))
            for png_file in png_files:
                contrast_match = re.search(r'_contrast-([^_]+)', png_file.name)
                if contrast_match:
                    contrast_name = contrast_match.group(1)
                    study_contrasts.add(contrast_name)
                    all_contrasts.add(contrast_name)
    
    # subject N from basic-details file
    basic_details_file = study_path / f"{study_id}_basic-details.json"
    n_subjects = 0
    if basic_details_file.exists():
        try:
            with open(basic_details_file, 'r') as f:
                basic_details = json.load(f)
                n_subjects = len(basic_details.get("Subjects", []))
        except (json.JSONDecodeError, KeyError):
            n_subjects = 0
    
    # append data
    data.append({
        'study_id': study_id,
        'n_subjects': n_subjects,
        'group_tasks_count': len(group_dirs),
        'contrasts_count': len(study_contrasts),
        'contrasts': sorted(list(study_contrasts)) if study_contrasts else []
    })

# Results DataFrame
df = pd.DataFrame(data)
df.to_csv(out_folder / 'openneurofitlins_dataset_summary.csv', index=False)

# summary statistics for fig
total_studies = len(df)
total_subjects = df['n_subjects'].sum()
total_group_reports = df['group_tasks_count'].sum()
total_contrasts = df['contrasts_count'].sum()

# define 2x2 panel
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(3, 3))

# color scheme
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Blue, Orange, Green, Red

# Panel 1: N datasets
ax1.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor=colors[0]))
ax1.text(0.5, 0.7, str(total_studies), ha='center', va='center', 
         fontsize=26, fontweight='bold', color='white')
ax1.text(0.5, 0.3, 'Total Datasets', ha='center', va='center', 
         fontsize=12, fontweight='bold', color='white')

# Panel 2: N Subjects
ax2.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor=colors[1]))
ax2.text(0.5, 0.7, str(total_subjects), ha='center', va='center', 
         fontsize=26, fontweight='bold', color='white')
ax2.text(0.5, 0.3, 'Total Subjects', ha='center', va='center', 
         fontsize=12, fontweight='bold', color='white')

# Panel 3: N Group Reports
ax3.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor=colors[2]))
ax3.text(0.5, 0.7, str(total_group_reports), ha='center', va='center', 
         fontsize=26, fontweight='bold', color='white')
ax3.text(0.5, 0.3, 'Total Group Reports', ha='center', va='center', 
         fontsize=12, fontweight='bold', color='white')

# Panel 4: N Computed Contrasts
ax4.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor=colors[3]))
ax4.text(0.5, 0.7, str(total_contrasts), ha='center', va='center', 
         fontsize=26, fontweight='bold', color='white')
ax4.text(0.5, 0.3, 'Total Contrasts', ha='center', va='center', 
         fontsize=12, fontweight='bold', color='white')

# no ticks/axes
for ax in [ax1, ax2, ax3, ax4]:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

# tight spacing, no gaps
plt.tight_layout(pad=0)
plt.subplots_adjust(hspace=0, wspace=0)

# save figure to output path
fig.savefig(out_folder / 'openneurofitlins_summary_dashboard.png', dpi=300, bbox_inches='tight')
plt.close(fig)