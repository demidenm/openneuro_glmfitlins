# OpenNeuro GLM Fitlins
[![DOI](https://zenodo.org/badge/923273141.svg)](https://doi.org/10.5281/zenodo.15376890)

**Curator & Maintainer**: Michael Demidenko  

> *This repository would not be possible if researchers did not make their task fMRI data publicly available, and the awesome people who have worked on and continue to work on OpenNeuro, BIDS Stats Models and Fitlins.*

**Contact**: [demidenko.michael@gmail.com](mailto:demidenko.michael@gmail.com)

*This repository is in active development. `Last updated: 2025-09-30`*


![OpenNeuro Fitlins Summary](docs/openneurofitlins_summary_dashboard.png)

N OpenNeuro Studies: 57

N OpenNeuro Task fMRI Group Summaries: 106

Completed fMRI Task Names: 1dNF, 1Norm, 2dNF, 2Swallow, 3HandA, 4HandB, 5Eyes, 6DeepBreathing, abstractconcretejudgment, antisaccadetaskwithfixedorder, arithm, auditoryfeedback, balloonanalogrisktask, balloonanalogrisktask, ChangeDetection, cmp, ColorDots, compL1, compLn, conditionalstopsignal, covertverbgeneration, deterministicclassification, dis, discounting, doors, dts, ec, em, emotionalfaces, emotionalregulation, Emotionregulation, encoding, epr, eye, faceexplocalizer, faceidentityoddball, facerecognition, familiarity, fb, feedback, figure2backwith1backlures, fingerfootlips, flanker, flavor, FoodChoice, FoodStimHiLo, gas, gas, GDMotor, identify1, identify2, illusion, learning, letter0backtask, letter1backtask, letter2backtask, linebisection, Memory, MGT, mid, mid, MIDmb4, MIDmb8, MIDsingle, mixedeventrelatedprobe, mixedgamblestask, modulate1, modulate2, music, nofeedback, nonmusic, objectviewing, overtverbgeneration, overtwordrepetition, ParallelAdaptation, passiveimageviewing, pc, PenaltyKik, prelearning, probabilisticclassification, prodL1, prodLn, regulate, retrieval, reversalweatherprediction, roletrait, sae, sar, socialcomparison, socialdoors, stopsignal, stopsignal, task, theoryofmindwithmanualresponse, TrainedHandTrainedSequence, TrainedHandUntrainedSequence, training, UntrainedHandTrainedSequence, UntrainedHandUntrainedSequence, verbs, viewFigure, viewing, viewRandom, visualfeedback, weatherprediction, wm

## Overview

`openneuro_glmfitlins` provides a streamlined workflow for analyzing neuroimaging datasets using [FitLins](https://github.com/poldracklab/fitlins)</a> via [BIDS Stats Models](https://bids-standard.github.io/stats-models/). The repository supports both **OpenNeuro datasets** and **local "house" datasets**, generating comprehensive reports for datasets and tasks processed through GLM Fitlins, with two primary goals:

1. Facilitate efficient and reproducible neuroimaging data analysis
2. Provide minimal barriers to entry for researchers at all levels

The FitLins workflow estimates statistical maps (e.g., z-stat, t-stat) across several levels, including `runLevel` (subject-level run contrast maps), `subjectLevel` (fixed-effect averages across runs), and `dataLevel` (group-level average maps). Group results summarize the models and activation maps for each study and task. The provided specification files are sufficient to download and reproduce all outputs for OpenNeuro datasets, or to analyze your local datasets. If you are unable to run the workflow but are interested in outputs for any of the datasets listed in `statsmodel_specs`, please feel free to reach out.


*Note: If you're simply interested in looking at the task-specific group reports, all of that information is in the subfolders `statsmodel_specs/<studyID>/group_<taskname>`. *
> The modeling decisions reported here are only recommendations. Each analysis should embark on its own quality control, behavioral data evaluation and final sample selection.

## Quick start

```bash
git clone https://github.com/demidenm/openneuro_glmfitlins.git
cd openneuro_glmfitlins
bash setup_uv.sh                 # installs uv, creates the environment, prompts for paths (path_config.json)
uv run glmfitlins config         # check the resolved paths
uv run glmfitlins --help         # all commands
```

`path_config.json` needs at least `datasets_folder` (BIDS, fMRIPrep and FitLins outputs) and `tmp_folder` (scratch). See [docs/installation.md](docs/installation.md) for all keys, environment-variable overrides and prerequisites.

## Running a dataset

All steps are `glmfitlins` subcommands. Run them from the repository folder with `uv run` (or activate `.venv` and drop the `uv run`).

| Step | Command | What it does |
|---|---|---|
| 1 | `glmfitlins details <ds>` | Check S3, download BIDS + fMRIPrep (+ MRIQC), write study details, subjects/contrasts files, README |
| 2 | `sbatch scripts/cluster_jobs/recreate_fmriprep.sh <ds>` | Only if fMRIPrep derivatives are minimal (SLURM) |
| 3 | `glmfitlins events <ds> <task>` | Trim dummy volumes, apply event fixes, check missing events |
| 4 | `glmfitlins spec <ds> <task> [suffix]` | Create the model spec (`--update` after editing inputs); `glmfitlins validate` checks it |
| 5 | `glmfitlins fit <ds> <task> [suffix]` | Run FitLins (`sbatch scripts/cluster_jobs/run_fitlins.sh` on a cluster) |
| 6 | `glmfitlins report <ds> <task> [suffix]` | Group report: figures + README in `statsmodel_specs/<ds>/group_<task>/` |

Example:

```bash
uv run glmfitlins details ds003425
uv run glmfitlins events  ds003425 learning
uv run glmfitlins spec    ds003425 learning      # review/edit the spec, then:
uv run glmfitlins validate ds003425 learning
uv run glmfitlins fit     ds003425 learning
uv run glmfitlins report  ds003425 learning
```

An optional `[suffix]` runs a model variant (files and folders are named `<task>-<suffix>`). Every command has `-h` with options and examples. Step-by-step details, example output and options are in [docs/workflow.md](docs/workflow.md).

## Documentation

- [Installation & configuration](docs/installation.md): prerequisites, dependencies, `path_config.json`, environment overrides
- [Analysis workflow](docs/workflow.md): each step in detail, house datasets, event fixes, spec options, FitLins and report options, legacy shell scripts
- [Repository layout & features](docs/repository.md): package structure and tests
- [Troubleshooting](docs/troubleshooting.md): common FitLins errors, removing downloaded data
- [Contributing](docs/contributing.md): reviewing specs/contrasts/event fixes, issue templates, adding a dataset

## License

This project is licensed under the MIT License. See the LICENSE file for details.
