#!/bin/bash

# Set data / environment paths for data download and BIDS Stats Models
openneuro_id=$1 # OpenNeuro ID, e.g. ds000102
if [ -z "$openneuro_id" ]; then
  echo "Please provide the OpenNeuro ID (e.g. ds000001) as the first argument."
  exit 1
fi

task_label=${2} # Task label, e.g. 'flanker'
if [ -z "$task_label" ]; then
  echo "Please provide the task label (e.g. 'balloonanalogrisktask') as the second argument."
  exit 1
fi

# sets paths from config file
config_file="../path_config.json"

# Extract values using jq
data=$(jq -r '.datasets_folder' "$config_file")
repo_dir=$(jq -r '.openneuro_glmrepo' "$config_file")
model_json="${repo_dir}/statsmodel_specs/${openneuro_id}/${openneuro_id}-${task_label}_specs.json"
scripts_dir="${repo_dir}/scripts"
scratch=$(jq -r '.tmp_folder' "$config_file")


read -p "If subject/contrast specs are setup, do you want to run create_mod-specs.py? (yes/no): " run_create_specs

if [[ "$run_create_specs" == "yes" ]]; then
    python ${scripts_dir}/create_mod-specs.py --openneuro_study ${openneuro_id} --task ${task_label} --script_dir ${scripts_dir}

else
  echo "Skipping creation of model specs."
fi

read -p "If the ${openneuro_id}_specs.json file is read, do you want to run the Fitlins Docker container? (yes/no): " run_docker

if [[ "$run_docker" == "yes" ]]; then
  echo
  echo "Running docker with the paths:"
  echo "BIDS input: ${data}/input/${openneuro_id}"
  echo "fmriprep derivatives: ${data}/fmriprep/${openneuro_id}/derivatives"
  echo "Analyses output: ${data}/analyses/${openneuro_id}"
  echo "Model specs: ${model_json}"
  echo 

  docker run --rm -it \
    -v ${data}/input/${openneuro_id}:/bids \
    -v ${data}/fmriprep/${openneuro_id}/derivatives:/fmriprep_deriv \
    -v ${data}/analyses/${openneuro_id}:/analyses_out \
    -v ${model_json}:/bids/model_spec \
    -v ${scratch}:/workdir \
    poldracklab/fitlins:0.11.0 \
    /bids /analyses_out run \
    -m /bids/model_spec -d /fmriprep_deriv \
    --space MNI152NLin2009cAsym --desc-label preproc \
    --smoothing 5:run:iso --estimator nilearn \
    --n-cpus 1 \
    --mem-gb 24 \
    -w /workdir
else
  echo "Docker execution skipped."
  exit 1
fi

 


#singularity run --cleanenv \
#-B ${data}/raw/dsX:/data/raw/dsX \
#-B ${data}/prep/dsX/fmriprep:/data/prep/dsX/fmriprep \
#-B ${data}/analyzed/dsX:/data/analyzed/dsX \
#-B ${scratch}:/scratch \
#  ${sif_img}/fitlins-0.11.0.simg \
#    /data/raw/dsX /data/analyzed/dsX dataset \
#    -d /data/prep/dsX/fmriprep \
#    -w /scratch
#