#!/bin/bash
 
# Check if uv is installed
if ! command -v uv &> /dev/null; then
	echo "uv not found. Installing..."
	curl -LsSf https://astral.sh/uv/install.sh | sh
else
	echo "uv is already installed."
fi

# check if git is install, at least version 2.30.0
version_ge() { 
    [ "$(printf '%s\n' "$1" "$2" | sort -V | tail -n1)" == "$1" ]
}

# Check and install Git (version >= 2.30.0)
required_git_version="2.30.0"
if command -v git &> /dev/null; then
    current_git_version=$(git --version | awk '{print $3}')
    if version_ge "$current_git_version" "$required_git_version"; then
        echo "Git is up to date (version $current_git_version)."
    else
        echo "Updating Git to version $required_git_version..."
        conda install -y -c conda-forge git
    fi
else
    echo "Git is not installed. Installing..."
    conda install -y -c conda-forge git
fi


# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq not found. Installing..."
    if command -v conda &> /dev/null; then
        conda install -y -c conda-forge jq
    else
        echo "No supported package manager found for installing jq."
        exit 1
    fi
else
    echo "jq is already installed."
fi

# Check and install git-annex (version >= 8.20)
required_annex_version="8.20"
if command -v git-annex &> /dev/null; then
    current_annex_version=$(git-annex version | grep 'git-annex version:' | awk '{print $3}')
    if version_ge "$current_annex_version" "$required_annex_version"; then
        echo "git-annex is up to date (version $current_annex_version)."
    else
        echo "Updating git-annex..."
        conda install -y -c conda-forge git-annex
    fi
else
    echo "git-annex is not installed. Installing..."
    conda install -y -c conda-forge git-annex
fi


# Path configuration (path_config.json is local and not tracked by git)
cd "$(dirname "${BASH_SOURCE[0]}")"
if [ ! -f path_config.json ]; then
    echo "Creating path_config.json from path_config.example.json"
    cp path_config.example.json path_config.json
    if [ -t 0 ]; then
        echo "Enter paths (press Enter to keep the placeholder and edit path_config.json later):"
        for key in datasets_folder tmp_folder fmriprep_simg freesurfer_license data_type; do
            current=$(jq -r ".${key}" path_config.json)
            read -r -p "  ${key} [${current}]: " value
            if [ -n "$value" ]; then
                jq --arg v "$value" ".${key} = \$v" path_config.json > path_config.json.tmp && mv path_config.json.tmp path_config.json
            fi
        done
    else
        echo "  Non-interactive shell: edit path_config.json before running the pipeline."
    fi
else
    echo "path_config.json already exists:"
    cat path_config.json
fi
echo "Note: any key can be overridden with environment variables, e.g. GLMFITLINS_DATASETS_FOLDER,"
echo "      GLMFITLINS_TMP_FOLDER, GLMFITLINS_DATA_TYPE, or point GLMFITLINS_CONFIG at another file."
echo

# Proceed with setting up the environment
#  Step 1. Install based on pyproject.toml
uv sync

# run to have kernel for jupyternotebook kernel
uv add --dev ipykernel
uv run ipython kernel install --user --env VIRTUAL_ENV $(pwd)/.venv --name="openneuro_glm"

# show the resolved configuration
uv run glmfitlins config || echo "Update path_config.json, then check with: uv run glmfitlins config"
