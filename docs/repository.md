[← README](../README.md) · [Installation](installation.md) · [Workflow](workflow.md) · [Repository](repository.md) · [Troubleshooting](troubleshooting.md) · [Contributing](contributing.md)

# Repository Layout & Features

## Features

- **Automatic Environment Setup**: Uses [setup_uv.sh](../setup_uv.sh) to install [uv](https://docs.astral.sh/uv/guides/install-python/) Python package manager, verify dependencies (GitHub, DataLad, git-annex), and create an environment with required packages (for more details on uv and packaging notes, see [Dr. Mumford's repo](https://github.com/jmumford/packaging-notes?tab=readme-ov-file#uv)
- **Automated Data Retrieval**: Leverages DataLad and AWS CLI to clone BIDS input data and download fMRIPrep preprocessed MRI/fMRI data, automatically determining preprocessing completeness
- **Flexible Analysis Configuration**: Generates summaries of relevant subject, run, and task fMRI data to facilitate statistical model creation
- **Reproducible Environments**: Ensures computational reproducibility through `uv` environment and exported specification files
- **HPC Integration**: Simplifies recomputation of minimally preprocessed MRI data and FitLins modeling on high-performance computing clusters
- **Comprehensive Reporting**: Generates detailed summary reports at both individual and group levels, including event details, model specifications, contrasts, regressors, variance inflation factors and group-statistical z-scored statistical maps

## Repository Structure

- `src/openneuro_glmfitlins/`: The Python package and the `glmfitlins` command line interface (`uv run glmfitlins --help`)
   - `cli.py`: The `glmfitlins` commands (`details`, `events`, `spec`, `validate`, `fit`, `report`, ...)
   - `config.py`: Reads `path_config.json` (+ environment overrides) and resolves every path; task variants use `<task>-<suffix>`
   - `io/`: S3/DataLad download, derivative hard links, BIDS helpers, volume trimming
   - `events/`: Event-file fixes, one module per dataset in `events/datasets/` (registered with `@register_events("dsXXXXXX")`)
   - `specs/`: Spec template, builder (`spec`), drift checker (`validate`) and design-matrix check
   - `qc/`: VIF, R-squared similarity and events-file checks
   - `reports/`: Study README, group report, dashboard
   - `fit/`: FitLins command builder
   - Users typically only need to modify:
     - `events/datasets/dsXXXXXX.py`: For preprocessing events files
     - `io/file_exclusions.json`: To limit OpenNeuro Dataset & fMRIPrep derivatives download size
- `scripts/cluster_jobs/`: SLURM job scripts (`recreate_fmriprep.sh`, `run_fitlins.sh`)
- `scripts/1_*.sh` ... `5_*.sh`: Legacy shortcuts for the commands above (see [Legacy shell scripts](workflow.md#legacy-shell-scripts))
- `tests/`: pytest suite (`uv run --extra dev pytest`)
- `examples/nilearn_pilots/`: Pilot nilearn-only first-level/group code (not part of the pipeline)

- `statsmodel_specs/`: JSON files defining statistical models for each OpenNeuro study, including MRIQC summaries and README files
- `LICENSE`: MIT License
- `path_config.example.json`: Template for your local `path_config.json` (which is not tracked by git)

## Tests

```bash
uv run --extra dev pytest
```
