#!/bin/bash

# ======================================================
# OpenNeuro Dataset Download & Basic Summary Script
# ======================================================

# Check for AWS CLI installation
if ! command -v aws &> /dev/null; then
    echo -e "\n❌ Error: AWS CLI is not installed. Confirm your environment is activated and AWS is installed."
    exit 1
fi

# Validate OpenNeuro ID parameter
openneuro_id=$1
if [ -z "$openneuro_id" ]; then
    echo -e "\n❌ Please provide the OpenNeuro ID (e.g. ds000102) as the first argument."
    exit 1
fi

# Load configuration and set paths
echo -e "\nSetting up paths and configuration..."
relative_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
config_file=$(realpath "${relative_path}/../path_config.json")

# Extract paths from config using jq
data=$(jq -r '.datasets_folder' "$config_file")
repo_dir=$(jq -r '.openneuro_glmrepo' "$config_file")
spec_dir="${repo_dir}/statsmodel_specs/${openneuro_id}"
scripts_dir="${repo_dir}/scripts"

# Create required directories
echo -e "\nCreating necessary directories..."
for subdir in analyses fmriprep input; do 
    [ ! -d "${data}/${subdir}" ] && echo "  Creating directory: ${data}/${subdir}" && mkdir -p "${data}/${subdir}"
done

[ ! -d "$spec_dir" ] && echo "  Creating directory: $spec_dir" && mkdir -p "$spec_dir"

# Check OpenNeuro Input  on S3
echo -e "\nChecking OpenNeuro Dataset on S3..."
openneuro_info=$(uv run aws s3 ls --no-sign-request --region us-east-1 s3://openneuro.org/${openneuro_id}/ --recursive --summarize | tail -n 3)

# Check fMRIPrep derivatives on S3
echo -e "\nChecking fMRIPrep derivatives on S3..."
deriv_info=$(uv run aws s3 ls --no-sign-request s3://openneuro-derivatives/fmriprep/${openneuro_id}-fmriprep/ --recursive --summarize | tail -n 3)

# Determine if derivatives are minimal based on MNI files presence
if aws s3 ls --recursive --no-sign-request "s3://openneuro-derivatives/fmriprep/${openneuro_id}-fmriprep/" 2>/dev/null | grep -q ".*_space-MNI152.*_desc-preproc_bold.nii.gz"; then
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

echo -e "\nDataset Information on OpenNeuro.org for ${openneuro_id}:"
echo "   - Size: ${gb_rnd_on} GB"
echo "   - Files: ${n_files_on}"
echo "   - Destination: ${data}/input/${openneuro_id}"

echo -e "\nDataset Information on OpenNeuro-Derivatives for ${openneuro_id}:"
echo "   - Size: ${gb_rnd_fp} GB"
echo "   - Files: ${n_files_fp}"
echo "   - Destination: ${data}/fmriprep/${openneuro_id}/derivatives"

if [[ "$minimal_derivatives" == "yes" ]]; then
        echo "   - fMRIPrep Derivatives on s3: Minimal, will ⚠️  require running recreate_fmriprep.sh script. "
        echo -e "   - Note: OpenNeuro BIDS data size can be reduced by adding filters to './scripts/prep_report_py/file_exclusions.json'"

else
        echo "   - fMRIPrep Derivatives on s3: Full, will not require running recreate_fmriprep.sh script."
        echo -e "   - Note: Fmriprep derivatives size can be reduced by adding filters to './scripts/prep_report_py/file_exclusions.json'"
        echo -e "   - Note: BIDS Data will only download non-binary data, files number will remain the same but size will significantly decrease."

fi

# Confirm download with user
echo
read -p "❓ Do you want to proceed with the download? (yes/no): " user_input

if [[ "$user_input" == "yes" ]]; then
    echo -e "\nStarting download process..."
    
    if [[ "$minimal_derivatives" == "yes" ]]; then
        echo "   Downloading complete BIDS dataset and minimal fMRIPrep data..."
        uv run python "${scripts_dir}/prep_report_py/get_openneuro_data.py" "${openneuro_id}" "${data}" "${spec_dir}" "${minimal_derivatives}"
        echo -e "\n   \033[1;31mIMPORTANT: Run recreate_fmriprep.sh script next\033[0m"
    else
        echo "   Downloading minimal BIDS dataset and complete fMRIPrep derivatives..."
        uv run python "${scripts_dir}/prep_report_py/get_openneuro_data.py" "${openneuro_id}" "${data}" "${spec_dir}" "${minimal_derivatives}"
    fi
    
    echo -e "\nDownload completed successfully."
else
    echo -e "\n❌ Download canceled for ${openneuro_id}."
    exit 1
fi

# Create symbolic link structure for non-minimal derivatives
if [[ "$minimal_derivatives" == "no" ]]; then
    echo -e "\nCreating symbolic links from fmriprep/${openneuro_id} to fmriprep/${openneuro_id}/derivatives..."
    
    source_dir="${data}/fmriprep/${openneuro_id}"
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

# Generate study summary
echo -e "\nGenerating study summary report..."
echo "   (For large datasets, BIDSLayout processing may take some time)"

uv run python "${scripts_dir}/prep_report_py/study_simple_details.py" \
    --openneuro_study "${openneuro_id}" \
    --bids_dir "${data}/input/${openneuro_id}" \
    --fmriprep_dir "${data}/fmriprep/${openneuro_id}" \
    --spec_dir "${spec_dir}" \
    --minimal_fp "${minimal_derivatives}"

echo -e "\nProcess completed for ${openneuro_id}"

# add write rights to input to simplify deletion
chmod +w -R "${data}/input/${openneuro_id}"
