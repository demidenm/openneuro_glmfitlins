import argparse
import time
import sys
import subprocess
import json
from pathlib import Path

# argument parsing
parser = argparse.ArgumentParser(description="Setup OpenNeuro study variables")
parser.add_argument("openneuro_study", type=str, help="OpenNeuro study ID")
parser.add_argument("data_dir", type=str, help="Base directory for dataset storage")
parser.add_argument("spec_dir", type=str, help="Directory for specification files for study")
parser.add_argument("is_minimal", help="Are fMRIPrep'd derivatives minimal output (yes/no)?")
args = parser.parse_args()

# asign variables
openneuro_study = args.openneuro_study
data_dir = Path(args.data_dir).resolve()
spec_dir = Path(args.spec_dir).resolve()
minimal_fp = args.is_minimal
py_script_dir = Path(__file__).parent.resolve()

# set paths
file_exclude_list = py_script_dir / "file_exclusions.json"
bids_data = data_dir / "input"
fmriprep_dir = data_dir / "fmriprep"

git_repo_url = f"https://github.com/OpenNeuroDatasets/{openneuro_study}.git"

print("Checking whether the BIDS data and fMRIprep directories exist for values: ")
print(f"    OpenNeuro Study: {openneuro_study}")
print(f"    Data Directory: {data_dir}")
print(f"    BIDS Data Path: {bids_data}")
print(f"    fMRIPrep Directory: {fmriprep_dir}")
print(f"    Git Repo URL: {git_repo_url}")
print()


#  build the AWS CLI command for OpenNeuro, FMRIPREP & MRIQC
bids_input_dir = bids_data / openneuro_study
fmriprep_out_dir = fmriprep_dir / openneuro_study

download_openneuro = [
    "uv", "run", "aws", "s3", "sync", "--no-sign-request", 
    f"s3://openneuro.org/{openneuro_study}",
    str(bids_input_dir)
]

download_fmriprep = [
    "uv", "run", "aws", "s3", "sync", "--no-sign-request",
    f"s3://openneuro-derivatives/fmriprep/{openneuro_study}-fmriprep",
    str(fmriprep_out_dir)
]

getfiles_mriqcgroup = [
    "uv", "run", "aws", "s3", "ls", "--no-sign-request", 
    f"s3://openneuro-derivatives/mriqc/{openneuro_study}-mriqc", "--recursive"
] 

# load and Add Exclusions to file
try:
    with open(file_exclude_list, "r") as file:
        data = json.load(file)
        on_exclusions = data.get("openneuro_exclusions", [])
        fp_exclusions = data.get("fmriprepderiv_exclusions", [])
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Warning: Could not load exclusions file {file_exclude_list}: {e}")
    print("Continuing without exclusions...")
    on_exclusions = []
    fp_exclusions = []

# append exclusions to commands
for pattern in on_exclusions:
    download_openneuro.extend(["--exclude", pattern])

for pattern in fp_exclusions:
    download_fmriprep.extend(["--exclude", pattern])

# BIDS input, download data (not checking if it exists, so it can restart on existing)
if minimal_fp == "yes":
    print("Downloading openneuro data while excluding files/folders specified in file_exclusions.json under openneuro_exclusions")
    try:
        subprocess.run(download_openneuro, check=True)
        print("     S3 sync completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Download failed, retrying... {e}")
        try:
            time.sleep(5)  # wait 5sec before retrying
            subprocess.run(download_openneuro, check=True)
            print("     S3 re-sync completed successfully.")
        except subprocess.CalledProcessError as retry_e:
            print(f"Error: Failed to download OpenNeuro data after retry: {retry_e}")
            sys.exit(1)

elif minimal_fp == "no":
    try:
        # Clone dataset
        print(f"Cloning BIDS and downloading full fMRIprep derivatives given minimal_fp == {minimal_fp}")
        subprocess.run(['datalad', 'clone', git_repo_url, str(bids_input_dir)], check=True)

        # Try to enable s3-PRIVATE sibling (optional)
        try:
            subprocess.run(['datalad', 'siblings', '-d', str(bids_input_dir), 'enable', '-s', 's3-PRIVATE'], check=True)
        except subprocess.CalledProcessError:
            print("        Warning: 's3-PRIVATE' sibling not found or could not be enabled. Continuing...")

        print(f"    {openneuro_study}. Dataset cloned successfully (no files downloaded).")
        
    except subprocess.CalledProcessError as e:
        if 'error: unknown option `show-origin`' in str(e):
            print("     Error: Your Git version may be outdated. Please confirm and update Git.")
            print("     Use 'git --version' to check your version.")
        else:
            print(f"        Error: Failed to clone dataset: {e}")
        sys.exit(1)
else:
    print(f"Error: Invalid value for is_minimal: '{minimal_fp}'. Must be 'yes' or 'no'.")
    sys.exit(1)

# fMRIprep data, download data (not checking if it exists, so it can restart on existing)
print("Downloading fMRIprep derivatives...")
try:
    subprocess.run(download_fmriprep, check=True, stdout=sys.stdout, stderr=sys.stderr)
    print("     S3 sync completed successfully.")
except subprocess.CalledProcessError as e:
    print(f"Download failed, retrying... {e}")
    try:
        time.sleep(5)  # wait before retrying
        subprocess.run(download_fmriprep, check=True, stdout=sys.stdout, stderr=sys.stderr)
        print("     S3 re-sync completed successfully.")
    except subprocess.CalledProcessError as retry_e:
        print(f"Error: Failed to download fMRIprep data after retry: {retry_e}")
        sys.exit(1)

# Get list of MRIQC files in repo, then only download the group files
mriqc_summ = spec_dir / "mriqc_summary"

if mriqc_summ.exists():
    print(f"        {openneuro_study} MRIQC already exists. Skipping group summary data download.")
else:
    try:
        # Create output directory if it doesn't exist
        mriqc_summ.mkdir(parents=True, exist_ok=True)
        
        # Get list of MRIQC group files
        result = subprocess.run(getfiles_mriqcgroup, capture_output=True, text=True, check=True)
        files = [line.split()[-1] for line in result.stdout.splitlines() if 'group' in line]
        print(f"Found {len(files)} group files to download")

        if not files:
            print("No 'group' files found. Skipping MRIQC download.")
        else:
            for s3_file_path in files:
                try:
                    file_path = mriqc_summ / Path(s3_file_path).name
                    download_mriqc_grpfile = [
                        "uv", "run", "aws", "cp", "--no-sign-request",
                        f"s3://openneuro-derivatives/{s3_file_path}", str(file_path)
                    ]
                    
                    subprocess.run(download_mriqc_grpfile, check=True)
                    print(f"    Downloaded: {s3_file_path} to {file_path}")
                except subprocess.CalledProcessError as e:
                    print(f"    Warning: Failed to download {s3_file_path}: {e}")
                    continue
                    
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to list MRIQC files: {e}")
        print("Continuing without MRIQC group files...")
    except OSError as e:
        print(f"Error: Failed to create MRIQC summary directory: {e}")
        sys.exit(1)

print("Script completed successfully!")