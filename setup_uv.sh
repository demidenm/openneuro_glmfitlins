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


# Proceed with setting up the environment
#  Step 1. Install based on pyproject.toml
uv sync
source .venv/bin/activate

# installing padding fix in fitlins from Jeanette
uv pip install git+https://github.com/jmumford/fitlins.git@paddedint
uv pip install setuptools
uv pip install git+https://github.com/bids-standard/pybids.git

# run to have kernel for jupyternotebook kernel
uv add --dev ipykernel
uv run ipython kernel install --user --env VIRTUAL_ENV $(pwd)/.venv --name="openneuro_glm"

# source 
source .venv/bin/activate