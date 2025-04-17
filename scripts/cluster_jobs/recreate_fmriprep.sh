#!/bin/bash
#
#SBATCH --job-name=on_minfmriprep
#SBATCH --array=5401,5404,5407-5412,5414-5430,5432,5433,5435-5437,5439,5440%20 
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=6
#SBATCH --mem-per-cpu=8GB
#SBATCH -p russpold,normal,owners
# Outputs ----------------------------------
#SBATCH --output=./logs/regen_fmriprep.%A_%a.out
#SBATCH --error=./logs/regen_fmriprep.%A_%a.err
#SBATCH --mail-user=demidenm@stanford.edu
#SBATCH --mail-type=ALL
# ------------------------------------------

# open neuro ID
if [ -z "$1" ]; then
  echo "Error: OpenNeuro study ID (e.g. ds003425) is required."
  echo "sbatch recreate_fmrip.sh ds003425"
  echo
  exit 1
fi

study_id=${1}

# config paths
singularity=$(which singularity || { echo "Singularity not found. Exiting."; exit 1; })
config_file=./../../path_config.json
data_dir=$(jq -r '.datasets_folder' "$config_file")
repo_dir=$(jq -r '.openneuro_glmrepo' "$config_file")
scratch_out=$(jq -r '.tmp_folder' "$config_file")
singularity_img=$(jq -r '.fmriprep_simg' "$config_file")
fs_license=$(jq -r '.freesurfer_license' "$config_file")


# example from job array, sub=("21" "31" "78" "55" "106")
subj=$( printf %02d ${SLURM_ARRAY_TASK_ID} )
echo "SUBJECT_ID: " $subj
sub="sub-${subj}"


# create derivative and scratch dirs
[ ! -d ${scratch_out} ] && mkdir -p ${scratch_out} && echo "scratch directory created"
[ ! -d ${data_dir}/fmriprep/${study_id}/derivatives ] && mkdir -p ${data_dir}/fmriprep/${study_id}/derivatives && echo "fmriprep deriv directory created"

echo "#### Running fMRIPrep to regenerate volumetric output based on minimal input dir ####"
echo "sub: ${sub}"
echo "data_in: ${data_dir}/input/${study_id}"
echo "scratch_out: ${scratch_out}"
echo "fmriprep_dir: ${data_dir}/fmriprep/${study_id}"


# --- Run FMRIPrep ---- 
singularity run --cleanenv \
    -B "${data_dir}/input/${study_id}:/bids_dir" \
    -B "${data_dir}/fmriprep/${study_id}:/minimal_dir" \
    -B "${data_dir}/fmriprep/${study_id}/derivatives:/fmriprep_out" \
    -B "${data_dir}/fmriprep/${study_id}/sourcedata/freesurfer:/freesurf_dir" \
    -B "${scratch_out}:/wd" \
    ${singularity_img} \
    /bids_dir /fmriprep_out participant \
    --skip_bids_validation \
    --participant-label "${sub}" \
    --fs-license-file ${fs_license} \
    --output-spaces MNI152NLin2009cAsym:res-2 \
    --fs-subjects-dir /freesurf_dir \
    --derivatives /minimal_dir \
    --n_cpus 8 \
    --mem_mb 48000 \
    -vv \
    -w /wd
