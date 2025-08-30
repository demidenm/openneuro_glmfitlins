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

if [[ -n "$task_suffix" ]]; then
    task_output_label="${task_label}-${suffix}"
    analysis_dir="${data}/analyses/${openneuro_id}/task-${task_output_label}"
    scratch_data_dir="${scratch_out}/fitlins/task-${task_output_label}"
    
else
    task_output_label="${task_label}"
    analysis_dir="${data}/analyses/${openneuro_id}/task-${task_output_label}"
    scratch_data_dir="${scratch_out}/fitlins/task-${task_output_label}"
fi

echo "INFO: Running group map report script for:"
echo "      Dataset: ${openneuro_id}"
echo "      Original Task: ${task_label}"
if [[ -n "$task_suffix" ]]; then
    echo "      Task Suffix: ${task_suffix}"
fi
echo "      Task Output Label: ${task_output_label}"
echo "      Analysis Directory: ${analysis_dir}"

# Check if analysis directory exists
if [ ! -d "$analysis_dir" ]; then
    echo "ERROR: Analysis directory not found: ${analysis_dir}"
    exit 1
fi

cmd_args=(
    "uv" "--project" "${repo_dir}" "run" "${scripts_dir}/prep_report_py/groupmap_report.py"
    "--openneuro_study" "${openneuro_id}"
    "--taskname" "${task_label}"
    "--analysis_dir" "${analysis_dir}"
    "--spec_dir" "${specs_dir}"
    "--scratch_dir" "${scratch_data_dir}"
)
# add suffix if provided
[[ -n "$task_suffix" ]] && cmd_args+=(--tasksuffix "${task_suffix}")
# run the command
"${cmd_args[@]}"

echo "SUCCESS: Group map report completed"