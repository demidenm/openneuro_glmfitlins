#!/bin/bash
#SBATCH --job-name=fitlins
#SBATCH --time=20:00:00
#SBATCH --cpus-per-task=6
#SBATCH --mem-per-cpu=16GB
#SBATCH -p russpold,normal,owners

# Output and notifications
#SBATCH --output=./logs/fitlins.%A_%a.out
#SBATCH --error=./logs/fitlins.%A_%a.err
#SBATCH --mail-user=demidenm@stanford.edu
#SBATCH --mail-type=ALL

# Prevent SLURM jobs runaway errors, i.e instances where more threads are ran than requested
# Per Chris Markewicz, 
# "FitLins will set the environment variable for subprocesses that are tagged as able to use more threads, but if these are not 1, 
#   then nipype can't accurately track resource usage."
MKL_NUM_THREADS=1
OMP_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
# -------------------- Parameter Checking --------------------
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: sbatch $0 <OpenNeuro Study ID> <Task Label>"
  echo "Example: sbatch $0 ds003425 learning"
  exit 1
fi

openneuro_id=$1
task_label=$2

# -------------------- Load Configuration --------------------
config_file="../../path_config.json"

if [ ! -f "$config_file" ]; then
  echo "Error: Configuration file $config_file not found."
  exit 1
fi

data_dir=$(jq -r '.datasets_folder' "$config_file")
repo_dir=$(jq -r '.openneuro_glmrepo' "$config_file")
model_json="${repo_dir}/statsmodel_specs/${openneuro_id}/${openneuro_id}-${task_label}_specs.json"
scratch_out=$(jq -r '.tmp_folder' "$config_file")
smoothing_type="5:run:iso"


# -------------------- Set Up Environment --------------------
echo "Setting up Python environment with uv..."
cd "$repo_dir" || { echo "Error: Failed to change directory to $repo_dir"; exit 1; }
source ".venv/bin/activate"

# -------------------- Set Up Input, Scratch, Output Directories --------------------
bids_data_dir="${data_dir}/input/${openneuro_id}"
scratch_data_dir="${scratch_out}/fitlins/task-${task_label}"
output_data_dir="${data_dir}/analyses/${openneuro_id}/task-${task_label}"

if [ -d "${data_dir}/fmriprep/${openneuro_id}/derivatives_alt" ]; then
  fmriprep_data_dir="${data_dir}/fmriprep/${openneuro_id}/derivatives_alt"
else
  fmriprep_data_dir="${data_dir}/fmriprep/${openneuro_id}/derivatives"
fi

# make directories
mkdir -p "${scratch_data_dir}"
mkdir -p "${output_data_dir}"

# -------------------- Run Fitlins --------------------
echo "#### Running Fitlins models to generate statistical maps ####"
echo "Study ID: ${openneuro_id}"
echo "Task Label: ${task_label}"
echo "Input Events: ${bids_data_dir}"
echo "Scratch Output: ${scratch_data_dir}"
echo "FMRIPrep Directory: ${fmriprep_data_dir}"
echo "Model Spec: ${model_json}"
echo "Smoothing type: ${smoothing_type}"

uv --project "$repo_dir" \
      run fitlins "${bids_data_dir}" "${output_data_dir}" \
      participant \
      -m "${model_json}" \
      -d "${fmriprep_data_dir}" \
      --ignore "sub-.*_physio\.(json|tsv\.gz)" \
      --drop-missing \
      --space MNI152NLin2009cAsym --desc-label preproc \
      --smoothing "${smoothing_type}" --estimator nilearn \
      --n-cpus 6 \
      --mem-gb 96 \
      -w "${scratch_data_dir}" \
      -vvv


# On sherlock: check exist code status to add to list to push on s3
run_status=$?
if [ $run_status -eq 0 ]; then
    target_dir="${data_dir}/analyses/${openneuro_id}/.to_process"
    if [ -d "$target_dir" ]; then
        touch "${target_dir}/${openneuro_id}"
        echo "Success: Flag file created"
    else
        echo "Warning: Directory $target_dir does not exist"
    fi
else
    echo "Error: Fitlins failed with exit code $run_status"
    exit $run_status
fi