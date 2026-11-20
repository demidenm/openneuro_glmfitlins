#!/bin/bash
#
#SBATCH --job-name=rn_nilearn
#SBATCH --array=1-13%20 # 
#SBATCH --time=05:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=6GB
#SBATCH -p russpold,normal,owners
# Outputs ----------------------------------
#SBATCH --output=./logs/nilearn.%A_%a.out
#SBATCH --error=./logs/nilearn.%A_%a.err
#SBATCH --mail-user=demidenm@stanford.edu
#SBATCH --mail-type=ALL
# ------------------------------------------

sub_id=$(printf "%02d" ${SLURM_ARRAY_TASK_ID})
session="01"
fwhm=5

# OpenNeuro Study ID Check
if [ -z "$1" ]; then
  echo "Error: OpenNeuro study ID (e.g. ds003425) is required."
  echo "Usage: sbatch recreate_fmrip.sh ds003425"
  exit 1
fi

study_id=${1}

# Config paths
config_file=./../../path_config.json
data_dir=$(jq -r '.datasets_folder' "$config_file")
repo_dir=$(git -C "${SLURM_SUBMIT_DIR:-.}" rev-parse --show-toplevel)
tmp=$(jq -r '.tmp_folder' "$config_file")
analysis_out="${data_dir}/nilearn/${study_id}"
scratch_out="${tmp}/${study_id}"
mkdir -p "${scratch_out}"
mkdir -p "${analysis_out}"


# Set up `uv` environment
echo "Setting up Python environment with uv..."
source "${repo_dir}/.venv/bin/activate"

# Run Python script with correct syntax
uv run python ${repo_dir}/examples/nilearn_pilots/run_firstfixed.py --study ${study_id} \
    --sub sub-${sub_id} --task learning \
    --ses ${session} \
    --smooth ${fwhm} \
    --beh_path "/oak/stanford/groups/russpold/data/openneuro_fitlins/input/${study_id}" \
    --fmriprep_path "/oak/stanford/groups/russpold/data/openneuro_fitlins/fmriprep/${study_id}/derivatives" \
    --output ${scratch_out} \
    --mask ${repo_dir}/examples/nilearn_pilots/mask/MNI152NLin2009cAsym_res-02_desc-brain_mask.nii.gz

if [ $? -ne 0 ]; then
    echo "First and Fix Effect Modeling Failed"
    exit 1
else
    # copy recursively while preserving timestamps // attributes
    #cp -a "${tmp}/${study_id}/"* "${data_dir}/nilearn/${study_id}/"
    rsync -av "${tmp}/${study_id}/" "${data_dir}/nilearn/${study_id}/"

fi

 
