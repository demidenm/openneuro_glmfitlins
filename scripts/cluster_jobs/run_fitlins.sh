#!/bin/bash
# =============================================================================
# >>> USER SETTINGS: REVIEW/EDIT THE #SBATCH LINES BELOW BEFORE SUBMITTING <<<
#   1. --mail-user : CHANGE TO YOUR OWN EMAIL ADDRESS
#   2. -p          : CHANGE TO PARTITION(S) YOU HAVE ACCESS TO ON YOUR CLUSTER
#   3. --time, --cpus-per-task, --mem : adjust to your dataset/cluster limits
#   4. --output/--error : ./logs must exist (mkdir -p logs) in the submit folder
# =============================================================================
#SBATCH --job-name=fitlins
#SBATCH --time=20:00:00              # <-- EDIT: max wall time
#SBATCH --cpus-per-task=4            # <-- EDIT: CPUs (passed to FitLins)
#SBATCH --mem=80GB                   # <-- EDIT: memory (passed to FitLins)
#SBATCH -p russpold,normal,owners    # <-- EDIT: your cluster's partition(s)

# Output and notifications
#SBATCH --output=./logs/fitlins.%A_%a.out
#SBATCH --error=./logs/fitlins.%A_%a.err
#SBATCH --mail-user=demidenko.michael@gmail.com  # <-- EDIT: YOUR EMAIL ADDRESS, pllllzzzz
#SBATCH --mail-type=ALL
# ============================ END USER SETTINGS ==============================

# SLURM version of `glmfitlins fit`. Submit from this folder:
#   sbatch run_fitlins.sh [-s FWHM:LEVEL:TYPE] [-e nilearn|afni] <dataset_id> <task> [suffix]
# CPUs/memory passed to FitLins follow the SBATCH request above (override with --n-cpus/--mem-gb).
# Thread variables (MKL/OMP/OPENBLAS=1) are set by `glmfitlins fit` for the FitLins process.
set -euo pipefail
repo_dir=${GLMFITLINS_REPO:-$(git -C "${SLURM_SUBMIT_DIR:-.}" rev-parse --show-toplevel 2>/dev/null || git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)}
n_cpus=${SLURM_CPUS_PER_TASK:-4}
mem_gb=$(( ${SLURM_MEM_PER_NODE:-81920} / 1024 ))

exec uv --project "${repo_dir}" run glmfitlins fit --n-cpus "${n_cpus}" --mem-gb "${mem_gb}" "$@"
