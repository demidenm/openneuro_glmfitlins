#!/bin/bash

# ======================================================
# OpenNeuro/House Dataset Processing & Summary Script
# ======================================================

# Validate dataset ID parameter
dataset_id=$1
if [ -z "$dataset_id" ]; then
    echo -e "\n❌ Please provide the dataset ID (e.g. ds000102) as the first argument."
    exit 1
fi


# Load configuration and set paths
echo -e "\nSetting up paths and configuration..."
relative_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
config_file=$(realpath "${relative_path}/../path_config.json")

# Extract paths and type from config using jq
data=$(jq -r '.datasets_folder' "$config_file")
repo_dir=$(jq -r '.openneuro_glmrepo' "$config_file")
config_type=$(jq -r '.data_type' "$config_file")
spec_dir="${repo_dir}/statsmodel_specs/${dataset_id}"
scripts_dir="${repo_dir}/scripts"

echo -e "\nConfiguration type: ${config_type}"

# Create required directories
echo -e "\nCreating necessary directories..."
for subdir in analyses fmriprep input; do 
    [ ! -d "${data}/${subdir}" ] && echo "  Creating directory: ${data}/${subdir}" && mkdir -p "${data}/${subdir}"
done

[ ! -d "$spec_dir" ] && echo "  Creating directory: $spec_dir" && mkdir -p "$spec_dir"

# Process based on configuration type
if [[ "$config_type" == "openneuro" ]]; then
    echo -e "\nProcessing OpenNeuro dataset..."
    
    # Check for AWS CLI installation
    if ! command -v aws &> /dev/null; then
        echo -e "\n❌ Error: AWS CLI is not installed. Confirm your environment is activated and AWS is installed."
        exit 1
    fi

    # Check if BIDS directory exists on S3
    if ! uv run aws s3 ls --no-sign-request --region us-east-1 s3://openneuro.org/${dataset_id}/ >/dev/null 2>&1; then
        echo "ERROR: BIDS Dataset for ${dataset_id} not found. Dataset may not be processed yet. Check study id and try again."
        echo "Exiting..."
        echo
        exit 1
    fi

    # Check OpenNeuro Input on S3
    echo -e "\nChecking OpenNeuro Dataset on S3..."
    openneuro_info=$(uv run aws s3 ls --no-sign-request --region us-east-1 s3://openneuro.org/${dataset_id}/ --recursive --summarize | tail -n 3)

    # Check fMRIPrep derivatives on S3
    echo -e "\nChecking fMRIPrep derivatives on S3..."
    deriv_info=$(uv run aws s3 ls --no-sign-request s3://openneuro-derivatives/fmriprep/${dataset_id}-fmriprep/ --recursive --summarize | tail -n 3)

    # Determine if derivatives are minimal based on MNI files presence
    if aws s3 ls --recursive --no-sign-request "s3://openneuro-derivatives/fmriprep/${dataset_id}-fmriprep/" 2>/dev/null | grep -q ".*_space-MNI152.*_desc-preproc_bold.nii.gz"; then
        minimal_derivatives="no"
        echo "Found complete derivatives with MNI152 space files"
    else
        minimal_derivatives="yes"
        echo -e "⚠️  Only minimal derivatives available\n   \033[1;31mYou will need to run recreate_fmriprep.sh script after download\033[0m"
    fi

    # Extract and display file information
    # openneuro
    n_files_on=$(echo "$openneuro_info" | grep "Total Objects" | awk -F':' '{print $2}' | tr -d ' ')
    total_size_bytes_on=$(echo "$openneuro_info" | grep "Total Size" | awk -F':' '{print $2}' | tr -d ' ')
    gb_size_on=$(echo "scale=6; $total_size_bytes_on / (1024*1024*1024)" | bc)
    gb_rnd_on=$(printf "%.1f" $gb_size_on)

    #fmriprep'd openneuro
    n_files_fp=$(echo "$deriv_info" | grep "Total Objects" | awk -F':' '{print $2}' | tr -d ' ')
    total_size_bytes_fp=$(echo "$deriv_info" | grep "Total Size" | awk -F':' '{print $2}' | tr -d ' ')
    gb_size_fp=$(echo "scale=6; $total_size_bytes_fp / (1024*1024*1024)" | bc)
    gb_rnd_fp=$(printf "%.1f" $gb_size_fp)

    echo -e "\nDataset Information on OpenNeuro.org for ${dataset_id}:"
    echo "   - Size: ${gb_rnd_on} GB"
    echo "   - Files: ${n_files_on}"
    echo "   - Destination: ${data}/input/${dataset_id}"

    echo -e "\nDataset Information on OpenNeuro-Derivatives for ${dataset_id}:"
    echo "   - Size: ${gb_rnd_fp} GB"
    echo "   - Files: ${n_files_fp}"
    echo "   - Destination: ${data}/fmriprep/${dataset_id}/derivatives"


    if [[ "$minimal_derivatives" == "yes" ]]; then
        echo "   - fMRIPrep Derivatives on s3: Minimal, will ⚠️  require running recreate_fmriprep.sh script. "
        echo -e "   - Note: OpenNeuro BIDS data size can be reduced by adding filters to './scripts/prep_report_py/file_exclusions.json'"
    else
        echo "   - fMRIPrep Derivatives on s3: Full, will not require running recreate_fmriprep.sh script."
        echo -e "   - Note: Fmriprep derivatives size can be reduced by adding filters to './scripts/prep_report_py/file_exclusions.json'"
        echo -e "   - Note: BIDS Data will only download non-binary data, files number will remain the same but size will significantly decrease."
    fi

    # Confirm download with user
    if [[ -n "$SLURM_JOB_ID" ]]; then
        # Skip questions ONLY for non-interactive slurm job names (i.e., want question in interactive vs-code/jupyter slurm sessions)
        if [[ "$SLURM_JOB_NAME" =~ ^(sys/|interactive|code-server|bash) ]]; then
            echo "Running in interactive Slurm session (job $SLURM_JOB_ID)"
            echo
            read -p "❓ Do you want to proceed with the download? (yes/no): " user_input
        else
            echo "Running in batch Slurm job: $SLURM_JOB_ID ($SLURM_JOB_NAME)"
            echo "Skipping confirmation question..."
            user_input="yes"
        fi
    else
        echo "Not running in Slurm job"
        echo
        read -p "❓ Do you want to proceed with the download? (yes/no): " user_input
    fi

    if [[ "$user_input" == "yes" ]]; then
        echo -e "\nStarting download process..."
        
        if [[ "$minimal_derivatives" == "yes" ]]; then
            echo "   Downloading complete BIDS dataset and minimal fMRIPrep data..."
            uv run python "${scripts_dir}/prep_report_py/get_openneuro_data.py" "${dataset_id}" "${data}" "${spec_dir}" "${minimal_derivatives}"
            echo -e "\n   \033[1;31mIMPORTANT: Run recreate_fmriprep.sh script next\033[0m"
        else
            echo "   Downloading minimal BIDS dataset and complete fMRIPrep derivatives..."
            uv run python "${scripts_dir}/prep_report_py/get_openneuro_data.py" "${dataset_id}" "${data}" "${spec_dir}" "${minimal_derivatives}"
        fi
        
        echo -e "\nDownload completed successfully."
    else
        echo -e "\n❌ Download canceled for ${dataset_id}."
        exit 1
    fi

    # Create symbolic link structure for non-minimal derivatives
    if [[ "$minimal_derivatives" == "no" ]]; then
        echo -e "\nCreating symbolic links from fmriprep/${dataset_id} to fmriprep/${dataset_id}/derivatives..."
        
        source_dir="${data}/fmriprep/${dataset_id}"
        dest_dir="${source_dir}/derivatives"
        
        # Create the derivatives directory
        mkdir -p "$dest_dir"
        
        # Find all files and directories, create symbolic links
        find "$source_dir" -mindepth 1 -not -path "$dest_dir*" -not -path "*/\.*" -not -name "*_events.tsv" | while read item; do
            rel_path="${item#$source_dir/}"
            
            if [[ -d "$item" ]]; then
                mkdir -p "$dest_dir/$rel_path"
            else
                mkdir -p "$(dirname "$dest_dir/$rel_path")"
                ln -f "$item" "$dest_dir/$rel_path"
            fi
        done
        
        echo "   Created symbolic link structure for complete derivatives."
    fi

    # Add write rights to input to simplify deletion (only for openneuro datasets)
    chmod -R +w "${data}/input/${dataset_id}"

elif [[ "$config_type" == "house" ]]; then
    echo -e "\n In-house dataset..."
    echo -e "   Skipping data size checks and download steps."
    echo -e "   Proceeding directly to summary generation and file specs creation."
    
    # assuming they have complete data
    minimal_derivatives="no"
    
else
    echo -e "\n❌ Error: Unknown configuration type '${config_type}'. Expected 'openneuro' or 'house'."
    exit 1
fi

# Generate study summary (common for both types)
echo -e "\nGenerating study summary report..."
echo "   (For large datasets, BIDSLayout processing may take some time)"

uv run python "${scripts_dir}/prep_report_py/study_simple_details.py" \
    --openneuro_study "${dataset_id}" \
    --bids_dir "${data}/input/${dataset_id}" \
    --fmriprep_dir "${data}/fmriprep/${dataset_id}" \
    --spec_dir "${spec_dir}" \
    --minimal_fp "${minimal_derivatives}"

echo -e "\nProcess completed for ${dataset_id}"