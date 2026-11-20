"""Stage 4: build and run the FitLins command for one task variant."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..config import StudyPaths, task_label

ESTIMATORS = ("nilearn", "afni")
THREAD_ENV = {"MKL_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"}


@dataclass
class FitOptions:
    smoothing: str = "5:run:iso"
    estimator: str = "nilearn"
    n_cpus: int = 6
    mem_gb: int = 32
    space: str = "MNI152NLin2009cAsym"
    desc_label: str = "preproc"
    ignore: str = r"sub-.*_physio\.(json|tsv\.gz)"
    verbosity: str = "-vvv"


def fitlins_executable() -> str:
    exe = Path(sys.executable).parent / "fitlins"
    if exe.exists():
        return str(exe)
    return shutil.which("fitlins") or "fitlins"


def build_fitlins_command(bids_dir: Path, output_dir: Path, model_json: Path, fmriprep_dir: Path,
                          work_dir: Path, opts: FitOptions) -> list[str]:
    if opts.estimator not in ESTIMATORS:
        raise ValueError(f"Invalid estimator '{opts.estimator}'. Must be one of: {', '.join(ESTIMATORS)}")
    return [
        fitlins_executable(), str(bids_dir), str(output_dir), "participant",
        "-m", str(model_json),
        "-d", str(fmriprep_dir),
        "--ignore", opts.ignore,
        "--drop-missing",
        "--space", opts.space, "--desc-label", opts.desc_label,
        "--smoothing", opts.smoothing, "--estimator", opts.estimator,
        "--n-cpus", str(opts.n_cpus),
        "--mem-gb", str(opts.mem_gb),
        "-w", str(work_dir),
        opts.verbosity,
    ]


def run_fit(paths: StudyPaths, task: str, suffix: Optional[str], opts: FitOptions, dry_run: bool = False) -> int:
    """Run FitLins; on success touch ``analyses/.to_process/<study_id>`` if that folder exists."""
    model_json = paths.spec_file(task, suffix)
    label = task_label(task, suffix)
    bids_dir = paths.bids_dir
    work_dir = paths.scratch_dir(task, suffix)
    output_dir = paths.analysis_dir(task, suffix)
    fmriprep_dir = paths.fit_fmriprep_dir()

    if not model_json.is_file():
        print(f"Error: Model specification file not found: {model_json}")
        return 1

    print("#### Running Fitlins models to generate statistical maps ####")
    print(f"Study ID: {paths.study_id}")
    print(f"Task Label: {task}")
    if suffix:
        print(f"Task Suffix: {suffix}")
    print(f"Task Output Label: {label}")
    print(f"Input Events: {bids_dir}")
    print(f"Scratch Output: {work_dir}")
    print(f"FMRIPrep Directory: {fmriprep_dir}")
    print(f"Model Spec: {model_json}")
    print(f"Smoothing type: {opts.smoothing}")
    print(f"Estimator: {opts.estimator}")
    print(f"Resources: {opts.n_cpus} CPUs & {opts.mem_gb} GB memory")

    cmd = build_fitlins_command(bids_dir, output_dir, model_json, fmriprep_dir, work_dir, opts)
    if dry_run:
        print(" ".join(cmd))
        return 0

    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, **THREAD_ENV}
    status = subprocess.run(cmd, env=env).returncode
    if status != 0:
        print(f"Error: Fitlins failed with exit code {status}")
        return status

    flag_dir = paths.to_process_dir
    if flag_dir.is_dir():
        (flag_dir / paths.study_id).touch()
        print("Success: Flag file created")
    else:
        print(f"Warning: Directory {flag_dir} does not exist")
    return 0
