# nilearn pilots (example, not part of the pipeline)

An alternative nilearn-only first-level / fixed-effects / group path used for piloting.
The supported pipeline is FitLins (`scripts/4_run_fitlins.sh`) plus the group report
(`scripts/5_run_groupreport.sh`).

Submit from this folder: `sbatch run_nilearn.sh ds003425` (edit the SBATCH array, task and paths first).
