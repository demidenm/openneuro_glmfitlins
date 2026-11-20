[← README](../README.md) · [Installation](installation.md) · [Workflow](workflow.md) · [Repository](repository.md) · [Troubleshooting](troubleshooting.md) · [Contributing](contributing.md)

# Installation & Configuration

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/demidenm/openneuro_glmfitlins.git
   ```

2. **Set up environment**:
   ```bash
   cd openneuro_glmfitlins
   bash setup_uv.sh
   ```

3. **Configure paths** in `path_config.json` (`setup_uv.sh` creates it from `path_config.example.json` and prompts for each value; check with `uv run glmfitlins config`):
   - `datasets_folder`: Location for BIDS, fMRIPrep, and analyses data
   - `tmp_folder`: Temporary/scratch space for FitLins processing
   - `fmriprep_simg`: Singularity image for fMRIPrep
   - `freesurfer_license`: Path to Freesurfer license file  (can be obtained from [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/registration.html))
   - `data_type`: Whether 'openneuro' or 'house' (default: openneuro)
   - The repository location is detected automatically (the old `openneuro_glmrepo` key is no longer needed).
   - Any key can be overridden with an environment variable: `GLMFITLINS_DATASETS_FOLDER`, `GLMFITLINS_TMP_FOLDER`, `GLMFITLINS_DATA_TYPE`, `GLMFITLINS_FMRIPREP_SIMG`, `GLMFITLINS_FREESURFER_LICENSE`; `GLMFITLINS_CONFIG` points to a different config file.

   - `fit` (optional): default FitLins options for this machine, e.g. `"fit": {"smoothing": "8:run:iso", "estimator": "nilearn", "n_cpus": 8, "mem_gb": 64}`. Valid keys: `smoothing`, `estimator`, `space`, `desc_label`, `ignore`, `verbosity`, `n_cpus`, `mem_gb`.

   **FitLins option precedence** (`glmfitlins fit`): command-line flag > `fit` block in `path_config.json` > built-in default.

   | Option (flag) | Built-in default |
   |---|---|
   | `-s/--smoothing` | `5:run:iso` |
   | `-e/--estimator` | `nilearn` |
   | `--space` | `MNI152NLin2009cAsym` |
   | `--desc-label` | `preproc` |
   | `--ignore` | `sub-.*_physio\.(json\|tsv\.gz)` |
   | `--verbosity` | `3` (passes `-vvv`) |
   | `--n-cpus` | not fixed: `SLURM_CPUS_PER_TASK`, else all CPUs on the machine |
   | `--mem-gb` | not fixed: the SLURM memory request, else ~90% of physical memory |

   Use `glmfitlins fit ... --dry-run` to see the values that will be used.

4. **Run the CLI.** All steps are subcommands of `glmfitlins`. From the repository folder, prefix commands with `uv run` (no activation needed); or activate the environment once (`source .venv/bin/activate`) and call `glmfitlins` directly. The documentation uses `uv run`.
   ```bash
   uv run glmfitlins --help            # workflow overview and all commands
   uv run glmfitlins config            # check the resolved paths
   uv run glmfitlins spec -h           # options and examples for one command
   ```

## Prerequisites

- **System Dependencies**:
  - [DataLad](https://www.datalad.org/)
  - Git (≥ 2.2)

### Python Dependencies

- **Python version**: 3.12+  

- **Major packages**:
  - `numpy` (≥ 1.26.0)
  - `pandas` (≥ 2.0.0)
  - `datalad` (≥ 0.16.0)
  - `nilearn` (≥ 0.9.2) - pre-dates issue for returned maps in computed_fixed estimates for `precision_weighted=True`
  - `matplotlib` (>=3.7.0)
  - `seaborn` (>=0.12.0)
  - Jupyter ecosystem:
    - `nbformat` (≥ 5.8.0)
    - `IPython` (≥ 8.0.0)
    - `jupyter` (≥ 1.0.0)
    - `notebook` (≥ 7.0.0)
  - `awscli`
  - `scipy`
  - `argparse`
  - `pyrelimri`
  - `templateflow`
  - Custom installations to resolve compatibility issues:
    - fitlins: `git+https://github.com/poldracklab/fitlins.git@dev`
    - pybids: `git+https://github.com/bids-standard/pybids.git@26b3f7e`

The authoritative list is [`pyproject.toml`](../pyproject.toml).
