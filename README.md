# OpenNeuro GLM Fitlins
[![DOI](https://zenodo.org/badge/923273141.svg)](https://doi.org/10.5281/zenodo.15376890) [![FitLins Derivatives](https://img.shields.io/badge/FitLins-Derivatives-red?style=for-the-badge)](https://github.com/orgs/OpenNeuroDerivatives/repositories?q=fitlins)


**Curator & Maintainer**: Michael Demidenko  

> *This repository would not be possible if researchers did not make their task fMRI data publicly available, and the awesome people who have worked on and continue to work on OpenNeuro, BIDS Stats Models and Fitlins.*

**Contact**: [demidenko.michael@gmail.com](mailto:demidenko.michael@gmail.com)

**Fitlins Derivatives**: All derivatives for the provided models specs are shared and available on the public bucket:
```bash
aws s3 ls --no-sign-request s3://openneuro-derivatives/fitlins/
```

## Overview

This repository helps you analyze task fMRI data with [FitLins](https://github.com/poldracklab/fitlins) and [BIDS Stats Models](https://bids-standard.github.io/stats-models/). It works with OpenNeuro datasets and with local ("house") datasets.

The goals are:

1. Make neuroimaging analysis efficient and reproducible.
2. Keep the barrier to entry low.

FitLins estimates statistical maps (for example z-stat and t-stat) at three levels:

- `runLevel`: contrast maps for each subject and run.
- `subjectLevel`: fixed-effect averages across runs.
- `dataLevel`: group-level average maps.

The specification files in `statsmodel_specs` are enough to download a dataset and reproduce its outputs. You can also use them on your own data. If you cannot run the workflow and you need the outputs, contact the maintainer.

To see the group reports only, open `statsmodel_specs/<studyID>/group_<taskname>`.

> The modeling decisions are recommendations only. Do your own quality control, behavioral data checks and sample selection.

## Quick start

```bash
git clone https://github.com/demidenm/openneuro_glmfitlins.git
cd openneuro_glmfitlins
bash setup_uv.sh                 # installs uv, creates the environment, asks for paths
uv run glmfitlins config         # shows the resolved paths
uv run glmfitlins --help         # lists all commands
```

`path_config.json` needs `datasets_folder` (BIDS, fMRIPrep and FitLins outputs) and `tmp_folder` (scratch space). For all keys and environment variables, see [docs/installation.md](docs/installation.md).

## Running a dataset

Each step is a `glmfitlins` subcommand. Run the commands from the repository folder with `uv run`. Or activate `.venv` and omit `uv run`.

| Step | Command | What it does |
|---|---|---|
| 1 | `glmfitlins details <ds>` | Downloads BIDS and fMRIPrep data. Writes the study details, subject and contrast files. |
| 2 | `sbatch scripts/cluster_jobs/recreate_fmriprep.sh <ds>` | Rebuilds minimal fMRIPrep derivatives (SLURM only, if needed). |
| 3 | `glmfitlins events <ds> <task>` | Trims dummy volumes, applies event fixes and reports missing events. |
| 4 | `glmfitlins spec <ds> <task> [suffix]` | Creates the model spec. Use `--update` to refresh an existing spec. |
| 4 | `glmfitlins validate <ds> <task> [suffix]` | Checks the spec. |
| 5 | `glmfitlins fit <ds> <task> [suffix]` | Runs FitLins. |
| 6 | `glmfitlins report <ds> <task> [suffix]` | Makes the group report in `statsmodel_specs/<ds>/group_<task>/`. |

You can give the dataset and task as positional arguments (`events ds003425 learning`) or as flags (`-d ds003425 -t learning`). The optional `[suffix]` (or `--suffix mod2`) selects a model variant. Files and folders then use the name `<task>-<suffix>`.

### Example: ds003425, task `learning`

```bash
# 1. Download the BIDS data and fMRIPrep derivatives. Write the study details.
#    Add --yes to skip the download if the data is already there.
uv run glmfitlins details -d ds003425

# 2. Set the dummy volumes and event fixes for the task (see docs/workflow.md).
#    Then apply them. This also reports missing events.
uv run glmfitlins events -d ds003425 -t learning

# 3. Create the model spec. Then review and edit it.
#    A spec that exists is never overwritten.
#    After you edit the subjects, contrasts or basic-details files, add --update.
#    This copies those values into the spec and keeps your other edits.
uv run glmfitlins spec -d ds003425 -t learning

# 4. Validate the spec. This checks that Input.task, subject and run match the study files.
#    It also checks that the contrast weights match the run-level conditions.
#    Add --check-design to build the design matrices and check for missing values.
uv run glmfitlins validate -d ds003425 -t learning

# 5. Fit the model. Choose one of these:
uv run glmfitlins fit -d ds003425 -t learning --dry-run            # prints the command only
uv run glmfitlins fit -d ds003425 -t learning                      # runs on this machine
uv run glmfitlins fit -d ds003425 -t learning -s 8:run:iso --n-cpus 8 --mem-gb 64   # overrides options
sbatch scripts/cluster_jobs/run_fitlins.sh -d ds003425 -t learning # submits a SLURM job

# 6. Make the group report.
uv run glmfitlins report -d ds003425 -t learning
```

### FitLins options

`glmfitlins fit` passes settings on to FitLins. You can change them in three ways. If a setting is given in more than one place, the first one in this list wins:

1. **Command-line flag**, for one run: `glmfitlins fit -d ds003425 -t learning -s 8:run:iso`
2. **`"fit"` block in `path_config.json`**, for every run: `"fit": {"smoothing": "8:run:iso", "n_cpus": 8}`
3. **Built-in default**, if you set nothing.

| Flag | What it sets | Default |
|---|---|---|
| `-s`, `--smoothing` | Smoothing as `FWHM:LEVEL:TYPE` | `5:run:iso` |
| `-e`, `--estimator` | Model estimator (`nilearn` or `afni`) | `nilearn` |
| `--space` | Output space | `MNI152NLin2009cAsym` |
| `--desc-label` | Description label of the preprocessed data | `preproc` |
| `--ignore` | Files to ignore | none |
| `--verbosity` | How much FitLins prints | FitLins default |
| `--n-cpus` | Number of CPUs | see below |
| `--mem-gb` | Memory in GB | see below |

For CPUs and memory, the default depends on where you run:

- **On SLURM:** the job request (`--cpus-per-task` and `--mem` in the `#SBATCH` lines).
- **On your own machine:** all CPUs and about 90% of memory.

The flags follow the [FitLins command-line arguments](https://fitlins.readthedocs.io/en/latest/usage.html#command-line-arguments). Add `--dry-run` to print the final command and values without running. For the full table, see [docs/installation.md](docs/installation.md).

Each command has `-h` for options and examples. For more detail, see [docs/workflow.md](docs/workflow.md).

## Documentation

- [Installation & configuration](docs/installation.md): prerequisites, dependencies, `path_config.json`, environment overrides
- [Analysis workflow](docs/workflow.md): each step in detail, house datasets, event fixes, spec options, FitLins and report options, legacy shell scripts
- [Repository layout & features](docs/repository.md): package structure and tests
- [Troubleshooting](docs/troubleshooting.md): common FitLins errors, removing downloaded data
- [Contributing](docs/contributing.md): reviewing specs/contrasts/event fixes, issue templates, adding a dataset

## Model Specs Available

*This repository is in active development. `Last updated: 2025-09-30`*


![OpenNeuro Fitlins Summary](docs/openneurofitlins_summary_dashboard.png)

N OpenNeuro Studies: 57

N OpenNeuro Task fMRI Group Summaries: 106

Completed fMRI Task Names: 1dNF, 1Norm, 2dNF, 2Swallow, 3HandA, 4HandB, 5Eyes, 6DeepBreathing, abstractconcretejudgment, antisaccadetaskwithfixedorder, arithm, auditoryfeedback, balloonanalogrisktask, balloonanalogrisktask, ChangeDetection, cmp, ColorDots, compL1, compLn, conditionalstopsignal, covertverbgeneration, deterministicclassification, dis, discounting, doors, dts, ec, em, emotionalfaces, emotionalregulation, Emotionregulation, encoding, epr, eye, faceexplocalizer, faceidentityoddball, facerecognition, familiarity, fb, feedback, figure2backwith1backlures, fingerfootlips, flanker, flavor, FoodChoice, FoodStimHiLo, gas, gas, GDMotor, identify1, identify2, illusion, learning, letter0backtask, letter1backtask, letter2backtask, linebisection, Memory, MGT, mid, mid, MIDmb4, MIDmb8, MIDsingle, mixedeventrelatedprobe, mixedgamblestask, modulate1, modulate2, music, nofeedback, nonmusic, objectviewing, overtverbgeneration, overtwordrepetition, ParallelAdaptation, passiveimageviewing, pc, PenaltyKik, prelearning, probabilisticclassification, prodL1, prodLn, regulate, retrieval, reversalweatherprediction, roletrait, sae, sar, socialcomparison, socialdoors, stopsignal, stopsignal, task, theoryofmindwithmanualresponse, TrainedHandTrainedSequence, TrainedHandUntrainedSequence, training, UntrainedHandTrainedSequence, UntrainedHandUntrainedSequence, verbs, viewFigure, viewing, viewRandom, visualfeedback, weatherprediction, wm

## License

This project is licensed under the MIT License. See the LICENSE file for details.
