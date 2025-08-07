#!/bin/bash
set -euo pipefail

# check required arguments and set vars
if [ $# -lt 2 ]; then
  echo "ERROR: Missing required arguments"
  echo "Usage: $0 <openneuro_id> <task_label>"
  echo "Example: $0 ds000102 flanker"
  exit 1
fi

openneuro_id=$1 # OpenNeuro ID, e.g. ds000102
task_label=$2 # Task label, e.g. 'flanker'
task_suffix=${3:-""} # Optional third suffix for writeout to grp, empty string if not provided

# set paths for config & check existence
relative_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
config_file=$(realpath "${relative_path}/../path_config.json")

if [ ! -f "$config_file" ]; then
  echo "ERROR: Config file not found at $config_file"
  exit 1
fi

# extra values using jq from config
data=$(jq -r '.datasets_folder' "$config_file")
repo_dir=$(jq -r '.openneuro_glmrepo' "$config_file")
scratch_out=$(jq -r '.tmp_folder' "$config_file")
specs_dir="${repo_dir}/statsmodel_specs"
scripts_dir="${repo_dir}/scripts"
analysis_dir="${data}/analyses/${openneuro_id}/task-${task_label}"
scratch_data_dir="${scratch_out}/fitlins/task-${task_label}"

echo "INFO: Running group map report script for:"
echo "      Dataset: ${openneuro_id}, Task: ${task_label}"
echo "      Analysis Directory: ${analysis_dir}"

uv --project ${repo_dir} \
    run ${scripts_dir}/prep_report_py/groupmap_report.py \
    --openneuro_study ${openneuro_id} \
    --taskname ${task_label} \
    --analysis_dir ${analysis_dir} \
    --spec_dir ${specs_dir} \
    --scratch_dir ${scratch_data_dir} \
    --tasksuffix "${task_suffix}"

echo "SUCCESS: Group map report completed"
echo