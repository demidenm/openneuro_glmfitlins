#!/bin/bash
set -euo pipefail

# required arguments
if [ $# -lt 2 ]; then
  echo "ERROR: Missing required arguments"
  echo "Usage: $0 <openneuro_id> <task_label>"
  echo "Example: $0 ds000102 flanker"
  exit 1
fi

# set study variables and paths
openneuro_id=$1 # OpenNeuro ID, e.g. ds000102
task_label=$2 # Task label, e.g. 'flanker'
task_suffix=${3:-""} # Optional third suffix for spec file creations


relative_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
config_file=$(realpath ${relative_path}/../path_config.json)

# config file exists
if [ ! -f "$config_file" ]; then
  echo "ERROR: Config file not found at $config_file"
  exit 1
fi

# grab values w/ jq
data=$(jq -r '.datasets_folder' "$config_file")
repo_dir=$(jq -r '.openneuro_glmrepo' "$config_file")
scripts_dir="${repo_dir}/scripts"
scratch=$(jq -r '.tmp_folder' "$config_file")

# Build model JSON path with optional suffix
if [[ -n "$task_suffix" ]]; then
    model_json="${repo_dir}/statsmodel_specs/${openneuro_id}/${openneuro_id}-${task_label}-${task_suffix}_specs.json"
else
    model_json="${repo_dir}/statsmodel_specs/${openneuro_id}/${openneuro_id}-${task_label}_specs.json"
fi

contrasts_json="${repo_dir}/statsmodel_specs/${openneuro_id}/${openneuro_id}-${task_label}_contrasts.json"
subjects_json="${repo_dir}/statsmodel_specs/${openneuro_id}/${openneuro_id}-${task_label}_subjects.json"

bids_dir_data_dir="${data}/input/${openneuro_id}"

# gen model specifications if not present
# Check if contrasts.json and _subjects.json exist
if [[ -f "$contrasts_json" && -f "$subjects_json" ]]; then
  echo "INFO: Required Subject and Contrast Files found. Creating model specifications..."
  # build command with optional suffix
  cmd_args=(
    "uv" "--project" "${repo_dir}" "run" "python" "${scripts_dir}/prep_report_py/create_mod_specs.py"
    "--openneuro_study" "${openneuro_id}"
    "--task" "${task_label}"
    "--script_dir" "${scripts_dir}"
    "--input_dir" "${bids_dir_data_dir}"
  )
  # add suffix if provided
  [[ -n "$task_suffix" ]] && cmd_args+=(--suffix "${task_suffix}")
  # run the command
  "${cmd_args[@]}"

else
  echo "ERROR: Cannot create model specifications."
  echo "       Missing contrasts.json or subjects.json files."
fi
