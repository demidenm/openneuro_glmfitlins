[← README](../README.md) · [Installation](installation.md) · [Workflow](workflow.md) · [Repository](repository.md) · [Troubleshooting](troubleshooting.md) · [Contributing](contributing.md)

# Troubleshooting

## FitLins: Most Common Sources of Errors

Before running fitlins, based on you grouping structure of nodes, ensure files are present. The below returns unique combinations of the "run" and "subject" columns. So for each run 1, subjects 1 - 13, run 2, subjects 1 - 13. If files are missing for certain cells, the workflow will fail.

```python
"GroupBy": [
        "run",
        "subject"
      ]
```

1. Imbalance in files across subjects for BOLD and/or events files (e.g., ds003425 ses-02 regulate task runs). Incorrect model spec files. Fitslins utilizes a groupby across subjects / task / runs. 
2. Differences in runs across subjects for BOLD and/or events files (e.g., ds003425 ses-02 regulate task runs). 

However, by using `--drop-missing` flag in the Fitlins call (default in this repo), if a subject is missing a run or contrast the models will still be estimated. However, if a subject is missing all values in a contrast matrices or all runs, the computation will fail with an error.  

## Removing Downloaded Data

When downloading the repositories off of s3, there are sometimes write-protected directors in the hidden `.git/annex` folder. Thus, you will need to run `chmod +w -R /input/<openneuro_id>/` and then `rm -rf /input/<openneuro_id>/` to remove the contents
