#!/bin/bash
set -euo pipefail

# Prevent runaway thread errors (same as sbatch version)
export MKL_NUM_THREADS=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

# -------------------- Parse Params --------------------
show_help() {
    echo "Usage: $0 [-s smoothing_type] [-e estimator] <OpenNeuro Study ID> <Task Label> [Task Suffix]"
    echo ""
    echo "Options:"
    echo "  -s <smoothing>   Smooth BOLD series with FWHM mm kernel prior to fitting at LEVEL."
    echo "                   Optional analysis LEVEL (default: l1) may be specified numerically"
    echo "                   (e.g., l1) or by name (run, subject, session or dataset)."
    echo "                   Optional smoothing TYPE (default: iso) must be one of:"
    echo "                   - iso: isotropic additive smoothing"
    echo "                   - isoblurto: isotropic smoothing progressively applied till target"
    echo "                     smoothness is reached"
    echo "                   Format: FWHM:LEVEL:TYPE (default: 5:run:iso)"
    echo "                   Example: -s 5:dataset:iso performs 5mm FWHM isotropic smoothing"
    echo "                   on subject-level maps, before evaluating the dataset level."
    echo ""
    echo "  -e <estimator>   Estimator to use to fit the (first level) models (default: nilearn)"
    echo "                   Possible choices: nilearn, nistats, afni"
    echo "                   - nilearn: Default estimator using nilearn.glm"
    echo "                   - nistats: Deprecated synonym for nilearn"
    echo "                   - afni: 3dREMLfit"
    echo ""
    echo "  -h               Show this help message"
    echo ""
    echo "Arguments:"
    echo "  OpenNeuro Study ID    Required. The dataset identifier (e.g., ds003425)"
    echo "  Task Label           Required. The task name (e.g., learning)"
    echo "  Task Suffix          Optional. Additional suffix for model spec file and output directories"
    echo ""
    echo "Examples:"
    echo "  $0 ds003425 learning"
    echo "  $0 ds003425 learning run1"
    echo "  $0 -s 6:run:iso ds003425 learning session1"
    echo "  $0 -e afni ds003425 learning"
    echo "  $0 -s 4:subject:iso -e nilearn ds003425 learning block1"
    echo "  $0 -s 8:dataset:isoblurto -e afni ds003425 learning pilot"
}

# Defaults
smoothing_type="5:run:iso"
estimator="nilearn"

# Validate estimator
validate_estimator() {
    case "$1" in
        nilearn|afni)
            return 0
            ;;
        *)
            echo "Error: Invalid estimator '$1'. Must be one of: nilearn, afni" >&2
            return 1
            ;;
    esac
}

# Parse options
while getopts "s:e:h" opt; do
    case $opt in
        s)
            smoothing_type="$OPTARG"
            ;;
        e)
            if validate_estimator "$OPTARG"; then
                estimator="$OPTARG"
            else
                show_help
                exit 1
            fi
            ;;
        h)
            show_help
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            show_help
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument" >&2
            show_help
            exit 1
            ;;
    esac
done

# Shift past the options
shift $((OPTIND-1))

# Get positional arguments
openneuro_id="$1"
task_label="$2"
task_suffix=${3:-""} # Optional third suffix for spec file creations

# Check required parameters
if [[ -z "$openneuro_id" ]] || [[ -z "$task_label" ]]; then
    echo "Error: Missing required arguments"
    show_help
    exit 1
fi

# -------------------- Load Configuration --------------------
# Set paths from config file (using same relative path logic as your version)
relative_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
config_file=$(realpath "${relative_path}/../path_config.json")

# Check config file exists
if [ ! -f "$config_file" ]; then
    echo "Error: Configuration file $config_file not found."
    exit 1
fi

data_dir=$(jq -r '.datasets_folder' "$config_file")
repo_dir=$(jq -r '.openneuro_glmrepo' "$config_file")

# Build model JSON path with optional suffix (same logic as sbatch version)
if [[ -n "$task_suffix" ]]; then
    model_json="${repo_dir}/statsmodel_specs/${openneuro_id}/${openneuro_id}-${task_label}${task_suffix}_specs.json"
    task_output_label="${task_label}${task_suffix}"
else
    model_json="${repo_dir}/statsmodel_specs/${openneuro_id}/${openneuro_id}-${task_label}_specs.json"
    task_output_label="${task_label}"
fi

scratch_out=$(jq -r '.tmp_folder' "$config_file")

# -------------------- Set Up Environment --------------------
echo "Setting up Python environment with uv..."
cd "$repo_dir" || { echo "Error: Failed to change directory to $repo_dir"; exit 1; }
source ".venv/bin/activate"

# -------------------- Set Up Input, Scratch, Output Directories --------------------
# Use same BIDS data dir as sbatch version (input folder, not fmriprep)
bids_data_dir="${data_dir}/input/${openneuro_id}"
scratch_data_dir="${scratch_out}/fitlins/task-${task_output_label}"
output_data_dir="${data_dir}/analyses/${openneuro_id}/task-${task_output_label}"

if [ -d "${data_dir}/fmriprep/${openneuro_id}/derivatives_alt" ]; then
  fmriprep_data_dir="${data_dir}/fmriprep/${openneuro_id}/derivatives_alt"
else
  fmriprep_data_dir="${data_dir}/fmriprep/${openneuro_id}/derivatives"
fi

# Make directories
mkdir -p "${scratch_data_dir}"
mkdir -p "${output_data_dir}"

# Verify model spec file exists
if [ ! -f "$model_json" ]; then
    echo "Error: Model specification file not found: $model_json"
    exit 1
fi

# -------------------- Run Fitlins --------------------
echo "#### Running Fitlins models to generate statistical maps ####"
echo "Study ID: ${openneuro_id}"
echo "Task Label: ${task_label}"
if [[ -n "$task_suffix" ]]; then
    echo "Task Suffix: ${task_suffix}"
fi
echo "Task Output Label: ${task_output_label}"
echo "Input Events: ${bids_data_dir}"
echo "Scratch Output: ${scratch_data_dir}"
echo "FMRIPrep Directory: ${fmriprep_data_dir}"
echo "Model Spec: ${model_json}"
echo "Smoothing type: ${smoothing_type}"
echo "Estimator: ${estimator}"

uv --project "$repo_dir" \
      run fitlins "${bids_data_dir}" "${output_data_dir}" \
      participant \
      -m "${model_json}" \
      -d "${fmriprep_data_dir}" \
      --ignore "sub-.*_physio\.(json|tsv\.gz)" \
      --drop-missing \
      --space MNI152NLin2009cAsym --desc-label preproc \
      --smoothing "${smoothing_type}" --estimator "${estimator}" \
      --n-cpus 6 \
      --mem-gb 32 \
      -w "${scratch_data_dir}" \
      -vvv

# Check exit code status (same as sbatch version)
run_status=$?
if [ $run_status -eq 0 ]; then
    target_dir="${data_dir}/analyses/.to_process"
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