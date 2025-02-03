import argparse
import time
import os
import sys
import subprocess
import json


# Set up argument parsing
parser = argparse.ArgumentParser(description="Setup OpenNeuro study variables")
parser.add_argument("openneuro_study", type=str, help="OpenNeuro study ID")
parser.add_argument("data_dir", type=str, help="Base directory for dataset storage")
parser.add_argument("spec_dir", type=str, help="Specification directory where to output MRIQC group summaries") 

args = parser.parse_args()

# Assign arguments to variables
openneuro_study = args.openneuro_study
data_dir = os.path.abspath(args.data_dir)
spec_dir = os.path.abspath(args.spec_dir)

# Define paths
file_exclude_list = os.path.join('.', "file_exclusions.json")
bids_data = os.path.join(data_dir, "input")
fmriprep_dir = os.path.join(data_dir, "fmriprep")
mriqc_dir = os.path.join(data_dir, "mriqc", openneuro_study)

git_repo_url = f"https://github.com/OpenNeuroDatasets/{openneuro_study}.git"

print("Checking whether the BIDS data and fMRIprep directories exist for values: ")
print(f"    OpenNeuro Study: {openneuro_study}")
print(f"    Data Directory: {data_dir}")
print(f"    BIDS Data Path: {bids_data}")
print(f"    fMRIPrep Directory: {fmriprep_dir}")
print(f"    Git Repo URL: {git_repo_url}")
print()

bids_input_dir = os.path.join(bids_data, openneuro_study)
if os.path.exists(bids_input_dir):
    print(f"        {openneuro_study} already exists. Skipping BIDS data clone.")
else:
    try:
        # Run the datalad clone command
        subprocess.run(['datalad', 'clone', git_repo_url, bids_input_dir], check=True)
        print(f"    {openneuro_study}. Dataset cloned successfully.")

    except subprocess.CalledProcessError as e:
        # Check if the error is related to an outdated Git version
        if 'error: unknown option `show-origin`' in str(e):
            print("     Error: Your Git version may be outdated. Please confirm and update Git.")
            print("     Use 'git --version' to check your version.")

        else:
            print(f"        An error occurred while cloning the dataset: {e}")


# Build the AWS CLI command
fmriprep_out_dir = os.path.join(fmriprep_dir, openneuro_study, "derivatives")
download_fmriprep = [
    "aws", "s3", "sync", "--no-sign-request",
    f"s3://openneuro-derivatives/fmriprep/{openneuro_study}-fmriprep",
    fmriprep_out_dir
]
getfiles_mriqcgroup = [
    "aws", "s3", "ls", "--no-sign-request", 
    f"s3://openneuro-derivatives/mriqc/{openneuro_study}-mriqc", "--recursive"
]

# Get list of MRIQC files in repo, then only download the group files
if os.path.exists(spec_dir):
    mriqc_files = subprocess.run(getfiles_mriqcgroup, capture_output=True, text=True)
    files = [line.split()[-1] for line in mriqc_files.stdout.splitlines() if 'group' in line]
    print(files)
    
    if not files:
            print("No 'group' files found. Exiting.")
    else:
        for s3_file_path in files:
            file_path = os.path.join(spec_dir, os.path.basename(s3_file_path))
            download_mriqc_grpfile = [
                    "aws", "s3", "cp", "--no-sign-request",
                    f"s3://openneuro-derivatives/{s3_file_path}", file_path
                ]
        
            subprocess.run(download_mriqc_grpfile, capture_output=True, text=True)
            print(f"    Downloaded: {s3_file_path} to {file_path}")


# Check if the fMRIprep directory exists, if not, download data
if os.path.exists(fmriprep_out_dir):
    print(f"        fMRIprep Directory already exists. Skipping fMRIprep data download for {openneuro_study}")
else:
    # Load and Add Exclusions to file
    with open(file_exclude_list, "r") as file:
        data = json.load(file)
        exclusions = data.get("exclusions", [])
    for pattern in exclusions:
        download_fmriprep.extend(["--exclude", pattern])
    
    try:
        subprocess.run(download_fmriprep, check=True)
        print("     S3 sync completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Download failed, retrying... {e}")
        time.sleep(5)  # wait before retrying
        subprocess.run(download_fmriprep, check=True)
        print("     S3 re-sync completed successfully.")
