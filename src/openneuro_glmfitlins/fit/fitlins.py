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


FIT_KEYS = ("smoothing", "estimator", "n_cpus", "mem_gb", "space", "desc_label", "ignore", "verbosity")


@dataclass
class FitOptions:
    """FitLins options. Every field can be set by CLI flag or the ``fit`` block of path_config.json.

    Defaults: FitLins-specific choices have fixed defaults; resources (``n_cpus``, ``mem_gb``)
    are machine-specific, so they default to what the machine / SLURM job provides.
    """

    smoothing: str = "5:run:iso"
    estimator: str = "nilearn"
    space: str = "MNI152NLin2009cAsym"
    desc_label: str = "preproc"
    ignore: str = r"sub-.*_physio\.(json|tsv\.gz)"
    verbosity: int = 3  # number of -v flags passed to FitLins
    n_cpus: Optional[int] = None  # default: SLURM_CPUS_PER_TASK or all CPUs
    mem_gb: Optional[int] = None  # default: SLURM memory request or physical memory


def default_cpus() -> int:
    env = os.environ.get("SLURM_CPUS_PER_TASK")
    return int(env) if env else (os.cpu_count() or 1)


def default_mem_gb(n_cpus: int) -> int:
    """SLURM memory request if present, else ~90% of physical memory, else 8 GB."""
    if os.environ.get("SLURM_MEM_PER_NODE"):
        return max(1, int(os.environ["SLURM_MEM_PER_NODE"]) // 1024)
    if os.environ.get("SLURM_MEM_PER_CPU"):
        return max(1, int(os.environ["SLURM_MEM_PER_CPU"]) * n_cpus // 1024)
    try:
        total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        return max(1, int(total * 0.9 / 1024**3))
    except (ValueError, OSError, AttributeError):
        return 8


def resolve_options(cli: dict, config_fit: Optional[dict] = None) -> FitOptions:
    """Precedence: CLI flag (not None) > ``fit`` block in path_config.json > built-in default."""
    unknown = set(config_fit or {}) - set(FIT_KEYS)
    if unknown:
        raise ValueError(f"Unknown key(s) in config 'fit' block: {sorted(unknown)}. Valid: {list(FIT_KEYS)}")
    values = {k: v for k, v in (config_fit or {}).items() if v is not None}
    values.update({k: v for k, v in cli.items() if v is not None})
    opts = FitOptions(**values)
    if opts.n_cpus is None:
        opts.n_cpus = default_cpus()
    if opts.mem_gb is None:
        opts.mem_gb = default_mem_gb(opts.n_cpus)
    return opts


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
        *(["-" + "v" * opts.verbosity] if opts.verbosity else []),
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
    print(f"Space / desc-label: {opts.space} / {opts.desc_label}")
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
