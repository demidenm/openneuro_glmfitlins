[← README](../README.md) · [Installation](installation.md) · [Workflow](workflow.md) · [Repository](repository.md) · [Troubleshooting](troubleshooting.md) · [Contributing](contributing.md)

# Contributing

Contributions can be made in several ways:

1.  **Review Design Matrices and Model Specifications:**
    * Examine the design matrices and model specifications for various studies located in the [`./statsmodel_specs/`](../statsmodel_specs/) directory.
    * Recommend fixes related to:
        * **Model Specifications:** This includes the resulting design matrices. Models can be adjusted by including or excluding regressors and modifying the convolution used.
        * **Contrast Lists:** Suggest removing or adding specific contrasts to better capture a `specific` cognitive process reflected in the estimated BOLD response.

2.  **Review Event File Modifications:**
    * Examine the per-dataset event fixes in [`./src/openneuro_glmfitlins/events/datasets/`](../src/openneuro_glmfitlins/events/datasets/) (one `dsXXXXXX.py` module per dataset).
    * Make recommendations for alternative ways to modify the events files, focusing on:
        * Improving the efficiency of the modifications.
        * Creating additional regressors that may have been overlooked.

3.  **Run Datasets and Contribute Results:**
    * Run datasets on your own machine.
    * Create model specifications and generate group-level reports.
    * Submit pull requests to add your results as contributions to the `statsmodel_specs` folder.

**Using the Issues Tab:**

For items related to specific issues, please use the `Issues` tab. There are separate templates available for:
* `Events Modification`: Revisions to current modifications to events files
* `Contrasts`: Recommendations to make changes to current contrasts lists.
* `Model Specification`: Recommendations to make changes to current model specifications.
* `Running Fitlins Models`: Requests to run OpenNeuro Datasets that have Task BOLD, Events files & fMRIPrep'd derivatives 


## Adding an event fix for a dataset

See [Workflow → step 3](workflow.md#3-modify-eventsboldconfound-files-and-check-event-counts) for the function template. Put it in `src/openneuro_glmfitlins/events/datasets/<dsXXXXXX>.py`; it is discovered automatically (`uv run glmfitlins event-fixes`).
