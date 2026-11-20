import sys
import json
import os
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from model_utils import group_onesample


parser = argparse.ArgumentParser(description="Process fMRI data using Nilearn")
parser.add_argument("--study", help="openneuro id, e.g ds003425")
parser.add_argument("--task", help="task type -- e.g., mid, reward, etc")
parser.add_argument("--ses", help="session, include the session type without prefix, e.g., 1, 01, baselinearm1")
parser.add_argument("--mask", help="path the to a binarized brain mask (e.g., MNI152 or "
                                   "constrained mask in MNI space, spec-network",
                    default=None)
parser.add_argument("--mask_label", help="label for mask, e.g. mni152, yeo-network, etc",
                    default=None)
parser.add_argument("--input", help="Path to fixed effects")
parser.add_argument("--output", help="output folder where to write out and save information")
args = parser.parse_args()

# Now you can access the arguments as attributes of the 'args' object.
study_id = args.study
task = args.task
ses = args.ses
brainmask = args.mask
mask_label = args.mask_label
inp_path = args.input
scratch_out = args.output



json_file = Path(__file__).parent / "study_req.json"
with open(json_file, "r") as f:
    json_data = json.load(f)

contrasts = set(json_data[study_id][task]["contrasts"])


grp_out=Path(scratch_out) / "group_out"
for contrast in contrasts:
    list_maps = sorted(Path(inp_path).rglob(f"*ses-{ses}_task-{task}_*contrast-{contrast}_stat-effect.nii.gz"))
    print(f"For {contrast}, {len(list_maps)} images found.")
    group_onesample(fixedeffect_paths=list_maps, session=ses, task_type=task,
                    contrast_type=contrast, group_outdir=grp_out,
                    mask=brainmask, save_zstat=True)

