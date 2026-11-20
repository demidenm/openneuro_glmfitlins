# Tutorial notebooks

Interactive walkthroughs of the `glmfitlins` workflow. They read **live from the public OpenNeuro buckets over HTTPS**
(no AWS account or AWS CLI needed), so they run on a laptop with no local data. Downloads are cached in `notebooks/.cache`.

Each notebook starts with a short "EDIT ME" cell (`DATASET`, `TASK`). Change them to explore any of the datasets
listed in notebook 1.

| Notebook | Topic |
|---|---|
| [01_quickstart_config.ipynb](01_quickstart_config.ipynb) | `path_config.json`, resolved paths, FitLins option precedence, what is on OpenNeuro |
| [02_study_details_and_spec.ipynb](02_study_details_and_spec.ipynb) | Basic details, subjects, contrasts and the BIDS Stats Model spec; checks against raw events |
| [03_events_and_design_matrix.ipynb](03_events_and_design_matrix.ipynb) | Events, dummy volumes, HRF choice, design matrix, correlations and VIF |
| [04_inspect_fitlins_outputs.ipynb](04_inspect_fitlins_outputs.ipynb) | Output layout, stat maps, run → subject → group, `effect`/`variance`/`t`/`z` |
| [05_group_report_walkthrough.ipynb](05_group_report_walkthrough.ipynb) | The six report steps: VIF, R-squared maps, MNI similarity QC, group z-maps |

## Run them

```bash
uv sync --extra notebooks
uv run jupyter lab notebooks/
```

`nb_utils.py` holds the small S3 listing/download helpers the notebooks share. Notebooks are stored without outputs.
