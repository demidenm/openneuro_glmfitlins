"""glmfitlins: OpenNeuro + BIDS Stats Models + FitLins pipeline.

Workflow (run from the repo with `uv run glmfitlins ...`, or activate .venv and call `glmfitlins ...`):
  1. details  <ds>                     check S3, download BIDS + fMRIPrep, write study details/README
     (minimal fMRIPrep derivatives only: sbatch scripts/cluster_jobs/recreate_fmriprep.sh <ds>)
  2. events   <ds> <task>              trim dummy volumes, apply event fixes, check missing events
  3. spec     <ds> <task> [suffix]     create the model spec (--update after editing inputs)
     validate <ds> <task> [suffix]     check the spec for drift and bad contrast weights
  4. fit      <ds> <task> [suffix]     run FitLins (cluster: sbatch scripts/cluster_jobs/run_fitlins.sh)
  5. report   <ds> <task> [suffix]     group report: figures + README in statsmodel_specs/<ds>/

Other commands:
  config        print the resolved configuration (path_config.json + GLMFITLINS_* overrides)
  event-fixes   list datasets with registered event fixes
  fit-summary   count FitLins outputs per node level
  dashboard     cross-dataset summary figure

Dataset/task/suffix can be positional (ds003425 learning mod2) or flags (-d ds003425 -t learning --suffix mod2).
A [suffix] names a model variant: files and folders use '<task>-<suffix>'.
Run `glmfitlins <command> -h` for the options of each command.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .config import ConfigError, load_config, task_label

INTERACTIVE_SLURM_RE = re.compile(r"^(sys/|interactive|code-server|bash)")


EXAMPLES = {
    "details": """examples:
  glmfitlins details ds003425            # asks before downloading
  glmfitlins details -d ds003425 --yes   # flag form; no question (batch jobs)
  glmfitlins details mystudy --skip-download   # regenerate details from local data""",
    "events": """examples:
  glmfitlins events ds003425 learning
  glmfitlins events -d ds003425 -t learning""",
    "spec": """examples:
  glmfitlins spec ds003425 learning               # -> ds003425-learning_specs.json
  glmfitlins spec ds003425 learning mod2          # -> ds003425-learning-mod2_specs.json
  glmfitlins spec ds003425 learning --update      # refresh subjects/runs/sessions/contrasts
  glmfitlins spec ds003425 learning --no-check    # skip the design-matrix check""",
    "validate": """examples:
  glmfitlins validate ds003425 learning
  glmfitlins validate ds003425 learning mod2 --check-design
  glmfitlins validate -d ds003425 -t learning --suffix mod2""",
    "fit": """examples:
  glmfitlins fit ds003425 learning
  glmfitlins fit ds003425 learning mod2
  glmfitlins fit -s 8:subject:iso -e afni ds003425 learning
  glmfitlins fit --n-cpus 8 --mem-gb 64 ds003425 learning
  glmfitlins fit --dry-run ds003425 learning      # print the FitLins command only
  glmfitlins fit -d ds003425 -t learning --suffix mod2 -s 5:run:iso
  glmfitlins fit ds003425 learning --space MNI152NLin6Asym --desc-label preproc --verbosity 1

defaults: flag > "fit" block in path_config.json > built-in (see docs/installation.md)""",
    "report": """examples:
  glmfitlins report ds003425 learning
  glmfitlins report ds003425 learning mod2 --zstat-thresh 3.1
  glmfitlins report ds003425 learning --out-dir /tmp/reports""",
    "dashboard": """examples:
  glmfitlins dashboard --out-dir docs""",
    "fit-summary": """examples:
  glmfitlins fit-summary ds003425 learning --out-dir /tmp/counts""",
}


def _sub(sub, name: str, help: str) -> argparse.ArgumentParser:
    return sub.add_parser(name, help=help, description=help, epilog=EXAMPLES.get(name),
                          formatter_class=argparse.RawDescriptionHelpFormatter)


def _add_dataset_flag(p: argparse.ArgumentParser) -> None:
    p.add_argument("study_id", nargs="?", default=None, metavar="dataset",
                   help="OpenNeuro dataset id, e.g. ds003425 (or use -d/--dataset)")
    p.add_argument("-d", "--dataset", dest="dataset_flag", default=None, metavar="DATASET",
                   help="dataset id, same as the positional argument")


def _add_study_task(p: argparse.ArgumentParser, suffix: bool = True) -> None:
    """Dataset/task/suffix as positionals (``ds task [suffix]``) or flags (``-d ds -t task --suffix s``)."""
    _add_dataset_flag(p)
    p.add_argument("task", nargs="?", default=None, help="task label, e.g. learning (or use -t/--task)")
    p.add_argument("-t", "--task", dest="task_flag", default=None, metavar="TASK",
                   help="task label, same as the positional argument")
    if suffix:
        p.add_argument("suffix", nargs="?", default=None,
                       help="optional model variant; files and folders use '<task>-<suffix>' "
                            "(or use --suffix)")
        p.add_argument("--suffix", dest="suffix_flag", default=None, metavar="SUFFIX",
                       help="model variant, same as the positional argument")


def _resolve_ids(args, parser: argparse.ArgumentParser) -> None:
    """Merge positional and flag forms of dataset/task/suffix into ``study_id``/``task``/``suffix``."""
    for attr, flag, required in (("study_id", "dataset_flag", True), ("task", "task_flag", True),
                                 ("suffix", "suffix_flag", False)):
        if not hasattr(args, flag):
            continue
        pos, opt = getattr(args, attr, None), getattr(args, flag)
        if pos and opt and pos != opt:
            parser.error(f"{attr}: got '{pos}' as a positional and '{opt}' as a flag; use one form")
        value = opt or pos
        if required and not value:
            name = {"study_id": "dataset (-d)", "task": "task (-t)"}[attr]
            parser.error(f"missing {name}")
        setattr(args, attr, value)


# --------------------------------------------------------------------------- commands
def cmd_config(args) -> int:
    cfg = load_config()
    print(f"config file      : {cfg.source}")
    print(f"repo_dir         : {cfg.repo_dir}")
    print(f"datasets_folder  : {cfg.datasets_folder}")
    print(f"tmp_folder       : {cfg.tmp_folder}")
    print(f"data_type        : {cfg.data_type}")
    print(f"fmriprep_simg    : {cfg.fmriprep_simg}")
    print(f"freesurfer_license: {cfg.freesurfer_license}")
    return 0


def _confirm_download(assume_yes: bool) -> bool:
    if assume_yes:
        return True
    job_id, job_name = os.environ.get("SLURM_JOB_ID"), os.environ.get("SLURM_JOB_NAME", "")
    if job_id:
        if not INTERACTIVE_SLURM_RE.match(job_name):
            print(f"Running in batch Slurm job: {job_id} ({job_name})")
            print("Skipping confirmation question...")
            return True
        print(f"Running in interactive Slurm session (job {job_id})\n")
    else:
        print("Not running in Slurm job\n")
    if not sys.stdin.isatty():
        print("No terminal to ask for confirmation; pass --yes to download non-interactively.")
        return False
    return input("❓ Do you want to proceed with the download? (yes/no): ").strip() == "yes"


def cmd_details(args) -> int:
    from .io import download as dl
    from .reports.details import generate_study_details

    cfg = load_config()
    paths = cfg.study(args.study_id)
    print(f"\nConfiguration type: {cfg.data_type}")
    for sub in ("analyses", "fmriprep", "input"):
        (cfg.datasets_folder / sub).mkdir(parents=True, exist_ok=True)
    paths.spec_dir.mkdir(parents=True, exist_ok=True)

    if cfg.data_type == "openneuro" and not args.skip_download:
        print("\nProcessing OpenNeuro dataset...")
        if not dl.aws_available():
            print("\n❌ Error: AWS CLI is not available. Confirm your environment is set up (uv sync).")
            return 1
        if not dl.openneuro_exists(args.study_id):
            print(f"ERROR: BIDS Dataset for {args.study_id} not found. Dataset may not be processed yet. "
                  "Check study id and try again.")
            return 1

        print("\nChecking OpenNeuro Dataset on S3...")
        on_info = dl.s3_list(f"s3://openneuro.org/{args.study_id}/", region="us-east-1")
        print("\nChecking fMRIPrep derivatives on S3...")
        fp_info = dl.s3_list(f"s3://openneuro-derivatives/fmriprep/{args.study_id}-fmriprep/")
        minimal = dl.derivatives_are_minimal(fp_info)
        if minimal:
            print("⚠️  Only minimal derivatives available\n   "
                  "\033[1;31mYou will need to run recreate_fmriprep.sh script after download\033[0m")
        else:
            print("Found complete derivatives with MNI152 space files")

        for title, info, dest in (
            ("OpenNeuro.org", on_info, paths.bids_dir),
            ("OpenNeuro-Derivatives", fp_info, paths.fmriprep_dir),
        ):
            print(f"\nDataset Information on {title} for {args.study_id}:")
            print(f"   - Size: {info.size_gb:.1f} GB" if info else "   - Size: unknown")
            print(f"   - Files: {info.n_files}" if info else "   - Files: unknown")
            print(f"   - Destination: {dest}")
        excl = dl.EXCLUSIONS_FILE
        if minimal:
            print("   - fMRIPrep Derivatives on s3: Minimal, will ⚠️  require running recreate_fmriprep.sh script. ")
            print(f"   - Note: OpenNeuro BIDS data size can be reduced by adding filters to '{excl}'")
        else:
            print("   - fMRIPrep Derivatives on s3: Full, will not require running recreate_fmriprep.sh script.")
            print(f"   - Note: Fmriprep derivatives size can be reduced by adding filters to '{excl}'")
            print("   - Note: BIDS Data will only download non-binary data, files number will remain the same "
                  "but size will significantly decrease.")

        if not _confirm_download(args.yes):
            print(f"\n❌ Download canceled for {args.study_id}.")
            return 1

        print("\nStarting download process...")
        try:
            dl.download_dataset(args.study_id, cfg.datasets_folder, paths.spec_dir, minimal=minimal)
        except RuntimeError as e:
            print(f"Error: {e}")
            return 1
        print("\nDownload completed successfully.")
        if minimal:
            print("\n   \033[1;31mIMPORTANT: Run recreate_fmriprep.sh script next\033[0m")
        else:
            print(f"\nCreating hard links from fmriprep/{args.study_id} to fmriprep/{args.study_id}/derivatives...")
            n = dl.link_derivatives(paths.fmriprep_root)
            print(f"   Hard-linked {n} files into {paths.fmriprep_dir}.")
        dl.make_user_writable(paths.bids_dir)
    else:
        if cfg.data_type == "house":
            print("\n In-house dataset...\n   Skipping data size checks and download steps.")
        else:
            print("\n --skip-download given; using existing data.")
        # in-house data is assumed complete; with --skip-download, detect from the local tree
        minimal = args.minimal if args.minimal is not None else False

    print("\nGenerating study summary report...")
    print("   (For large datasets, BIDSLayout processing may take some time)")
    generate_study_details(args.study_id, paths.bids_dir, paths.fmriprep_root, paths.spec_dir,
                           minimal_fp=minimal, out_dir=args.out_dir)
    print(f"\nProcess completed for {args.study_id}")
    return 0


def cmd_events(args) -> int:
    from .config import read_json
    from .events.prep import run_events_step

    paths = load_config().study(args.study_id)
    print("#### Preparing data for Fitlins Models ####")
    print(f"\tStudy ID: {args.study_id}")
    print(f"\tTask Label: {args.task}")
    print(f"\tInput Data: {paths.bids_dir}")
    print(f"\tfMRIPrep Derivatives Directory: {paths.fmriprep_dir}\n")
    return run_events_step(args.study_id, args.task, read_json(paths.basic_details), paths.bids_dir,
                           paths.fmriprep_dir, paths.fmriprep_alt_dir, check_missing=not args.no_missing_check)


def cmd_spec(args) -> int:
    from .specs.build import run_spec_step

    paths = load_config().study(args.study_id)
    return run_spec_step(paths, args.task, args.suffix, update=args.update, check=not args.no_check,
                         template=args.template)


def cmd_validate(args) -> int:
    from .specs.validate import run_validate

    paths = load_config().study(args.study_id)
    return run_validate(paths, args.task, args.suffix, check_design=args.check_design)


def cmd_fit(args) -> int:
    from .fit.fitlins import FIT_KEYS, resolve_options, run_fit

    cfg = load_config()
    paths = cfg.study(args.study_id)
    cli = {k: getattr(args, k) for k in FIT_KEYS}
    try:
        opts = resolve_options(cli, cfg.extra.get("fit"))
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    return run_fit(paths, args.task, args.suffix, opts, dry_run=args.dry_run)


def cmd_report(args) -> int:
    from .reports.groupmap import ReportOptions, run_group_report

    paths = load_config().study(args.study_id)
    print("INFO: Running group map report script for:")
    print(f"      Dataset: {args.study_id}")
    print(f"      Original Task: {args.task}")
    if args.suffix:
        print(f"      Task Suffix: {args.suffix}")
    print(f"      Task Output Label: {task_label(args.task, args.suffix)}")
    print(f"      Analysis Directory: {paths.analysis_dir(args.task, args.suffix)}")
    opts = ReportOptions(zstat_thresh=args.zstat_thresh, dice_thresh=args.dice_thresh,
                         voxout_thresh=args.voxout_thresh, n_workers=args.n_workers)
    status = run_group_report(
        study_id=args.study_id,
        task=args.task,
        spec_file=paths.spec_file(args.task, args.suffix),
        basic_details_file=paths.basic_details,
        analysis_dir=paths.analysis_dir(args.task, args.suffix),
        scratch_dir=paths.scratch_dir(args.task, args.suffix),
        group_dir=paths.group_dir(args.task, args.suffix, out_dir=args.out_dir),
        opts=opts,
    )
    if status == 0:
        print("SUCCESS: Group map report completed")
    return status


def cmd_dashboard(args) -> int:
    from .reports.dashboard import make_dashboard

    specs = Path(args.specs_dir) if args.specs_dir else load_config().specs_root
    make_dashboard(specs, args.out_dir)
    return 0


def cmd_fit_summary(args) -> int:
    from .reports.fit_summary import summarize_fit_outputs

    paths = load_config().study(args.study_id)
    tables = summarize_fit_outputs(paths.analysis_dir(args.task, args.suffix), out_dir=args.out_dir)
    return 0 if tables else 1


def cmd_event_fixes(args) -> int:
    from .events.registry import registered_studies

    print("\n".join(registered_studies()))
    return 0


# --------------------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="glmfitlins", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    p = _sub(sub, "config", help="print the resolved configuration")
    p.set_defaults(func=cmd_config)

    p = _sub(sub, "details", help="stage 1: download data and write study details")
    _add_dataset_flag(p)
    p.add_argument("-y", "--yes", action="store_true", help="download without asking for confirmation")
    p.add_argument("--skip-download", action="store_true", help="only (re)generate details from local data")
    p.add_argument("--minimal", type=lambda s: s.lower() in ("yes", "true", "1"), default=None,
                   help="with --skip-download: are the fMRIPrep derivatives minimal (yes/no)? default no")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="where README/figures go (default statsmodel_specs/<study_id>)")
    p.set_defaults(func=cmd_details)

    p = _sub(sub, "events", help="stage 2: trim volumes, fix events, check missing events")
    _add_study_task(p, suffix=False)
    p.add_argument("--no-missing-check", action="store_true", help="skip the missing-events report")
    p.set_defaults(func=cmd_events)

    p = _sub(sub, "spec", help="stage 3: create/update the model spec and check design columns")
    _add_study_task(p)
    p.add_argument("--update", action="store_true",
                   help="refresh subjects/runs/sessions/Run contrasts in an existing spec; keep other edits")
    p.add_argument("--no-check", action="store_true", help="skip the design-matrix check")
    p.add_argument("--template", type=Path, default=None, help="alternative spec template JSON")
    p.set_defaults(func=cmd_spec)

    p = _sub(sub, "validate", help="report drift between a spec and its input files")
    _add_study_task(p)
    p.add_argument("--check-design", action="store_true",
                   help="also build design matrices and check contrast columns (needs BIDS data)")
    p.set_defaults(func=cmd_validate)

    from .fit.fitlins import ESTIMATORS, FitOptions

    d = FitOptions()
    p = _sub(sub, "fit", help="stage 4: run FitLins")
    p.add_argument("-s", "--smoothing", default=None,
                   help=f"FWHM:LEVEL:TYPE, e.g. 5:run:iso or 8:dataset:isoblurto (default {d.smoothing})")
    p.add_argument("-e", "--estimator", choices=ESTIMATORS, default=None, help=f"default {d.estimator}")
    p.add_argument("--n-cpus", type=int, default=None,
                   help="default: SLURM_CPUS_PER_TASK, else all CPUs on the machine")
    p.add_argument("--mem-gb", type=int, default=None,
                   help="default: SLURM memory request, else ~90%% of physical memory")
    p.add_argument("--space", default=None, help=f"default {d.space}")
    p.add_argument("--desc-label", default=None, help=f"fMRIPrep desc label, default {d.desc_label}")
    p.add_argument("--ignore", default=None, help=f"regex of files FitLins ignores, default {d.ignore}")
    p.add_argument("--verbosity", type=int, choices=range(0, 4), default=None,
                   help=f"number of -v flags given to FitLins (0-3), default {d.verbosity}")
    p.add_argument("--dry-run", action="store_true", help="print the FitLins command and exit")
    _add_study_task(p)
    p.set_defaults(func=cmd_fit)

    from .reports.groupmap import ReportOptions

    r = ReportOptions()
    p = _sub(sub, "report", help="stage 5: group report")
    _add_study_task(p)
    p.add_argument("--out-dir", type=Path, default=None,
                   help="parent of group_<label>/ (default statsmodel_specs/<study_id>)")
    p.add_argument("--zstat-thresh", type=float, default=r.zstat_thresh)
    p.add_argument("--dice-thresh", type=float, default=r.dice_thresh)
    p.add_argument("--voxout-thresh", type=float, default=r.voxout_thresh)
    p.add_argument("--n-workers", type=int, default=None, help="default: all CPUs but 2")
    p.set_defaults(func=cmd_report)

    p = _sub(sub, "dashboard", help="cross-dataset summary figure")
    p.add_argument("--specs-dir", default=None, help="default: <repo>/statsmodel_specs")
    p.add_argument("--out-dir", required=True)
    p.set_defaults(func=cmd_dashboard)

    p = _sub(sub, "fit-summary", help="count FitLins outputs per node level")
    _add_study_task(p)
    p.add_argument("--out-dir", default=None, help="also write <level>_uniques.tsv here")
    p.set_defaults(func=cmd_fit_summary)

    p = _sub(sub, "event-fixes", help="list datasets with registered event fixes")
    p.set_defaults(func=cmd_event_fixes)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _resolve_ids(args, parser)
    try:
        return int(args.func(args) or 0)
    except ConfigError as e:
        print(f"CONFIG ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
