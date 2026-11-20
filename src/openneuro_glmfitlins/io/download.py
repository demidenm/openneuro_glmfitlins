"""Stage 1 data access: S3 checks, BIDS/fMRIPrep/MRIQC download and derivative hard links."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

EXCLUSIONS_FILE = Path(__file__).with_name("file_exclusions.json")
MNI_PREPROC_RE = re.compile(r"_space-MNI152.*_desc-preproc_bold\.nii\.gz")


def aws_cmd() -> list[str]:
    """AWS CLI from the active environment (falls back to ``uv run aws``)."""
    venv_aws = Path(sys.executable).parent / "aws"
    if venv_aws.exists():
        return [str(venv_aws)]
    if shutil.which("aws"):
        return ["aws"]
    return ["uv", "run", "aws"]


def aws_available() -> bool:
    try:
        subprocess.run(aws_cmd() + ["--version"], check=True, capture_output=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


@dataclass
class S3Listing:
    n_files: int
    size_bytes: int
    keys: list[str]

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 ** 3)


def s3_list(uri: str, region: Optional[str] = None) -> Optional[S3Listing]:
    """Recursive ``aws s3 ls --summarize``; None if the prefix does not exist or listing fails."""
    cmd = aws_cmd() + ["s3", "ls", "--no-sign-request"]
    if region:
        cmd += ["--region", region]
    cmd += [uri, "--recursive", "--summarize"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return None
    n_files, size, keys = 0, 0, []
    for line in res.stdout.splitlines():
        line = line.strip()
        if line.startswith("Total Objects:"):
            n_files = int(line.split(":", 1)[1])
        elif line.startswith("Total Size:"):
            size = int(line.split(":", 1)[1])
        elif line:
            parts = line.split()
            if len(parts) >= 4:
                keys.append(parts[-1])
    return S3Listing(n_files=n_files, size_bytes=size, keys=keys)


def openneuro_exists(study_id: str) -> bool:
    cmd = aws_cmd() + ["s3", "ls", "--no-sign-request", "--region", "us-east-1", f"s3://openneuro.org/{study_id}/"]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def derivatives_are_minimal(listing: Optional[S3Listing]) -> bool:
    """fMRIPrep derivatives are 'minimal' when no MNI152 preprocessed BOLD files are present."""
    if listing is None:
        return True
    return not any(MNI_PREPROC_RE.search(k) for k in listing.keys)


def load_exclusions(path: Path = EXCLUSIONS_FILE) -> tuple[list[str], list[str]]:
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get("openneuro_exclusions", []), data.get("fmriprepderiv_exclusions", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load exclusions file {path}: {e}")
        print("Continuing without exclusions...")
        return [], []


def _run_with_retry(cmd: list[str], what: str, wait: int = 5) -> None:
    try:
        subprocess.run(cmd, check=True)
        print("     S3 sync completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Download failed, retrying... {e}")
        time.sleep(wait)
        try:
            subprocess.run(cmd, check=True)
            print("     S3 re-sync completed successfully.")
        except subprocess.CalledProcessError as retry_e:
            raise RuntimeError(f"Failed to download {what} after retry: {retry_e}") from retry_e


def download_dataset(study_id: str, data_dir: Path, spec_dir: Path, minimal: bool,
                     exclusions_file: Path = EXCLUSIONS_FILE) -> None:
    """Download BIDS input (full via S3 if derivatives are minimal, else a datalad clone without
    binary content), the fMRIPrep derivatives, and the MRIQC group reports."""
    data_dir = Path(data_dir).resolve()
    spec_dir = Path(spec_dir).resolve()
    bids_input_dir = data_dir / "input" / study_id
    fmriprep_out_dir = data_dir / "fmriprep" / study_id
    git_repo_url = f"https://github.com/OpenNeuroDatasets/{study_id}.git"

    print("Checking whether the BIDS data and fMRIprep directories exist for values: ")
    print(f"    OpenNeuro Study: {study_id}")
    print(f"    Data Directory: {data_dir}")
    print(f"    BIDS Data Path: {data_dir / 'input'}")
    print(f"    fMRIPrep Directory: {data_dir / 'fmriprep'}")
    print(f"    Git Repo URL: {git_repo_url}")
    print()

    on_exclusions, fp_exclusions = load_exclusions(exclusions_file)
    download_openneuro = aws_cmd() + ["s3", "sync", "--no-sign-request",
                                      f"s3://openneuro.org/{study_id}", str(bids_input_dir)]
    download_fmriprep = aws_cmd() + ["s3", "sync", "--no-sign-request",
                                     f"s3://openneuro-derivatives/fmriprep/{study_id}-fmriprep",
                                     str(fmriprep_out_dir)]
    for pattern in on_exclusions:
        download_openneuro += ["--exclude", pattern]
    for pattern in fp_exclusions:
        download_fmriprep += ["--exclude", pattern]

    # BIDS input (no existence check, so an interrupted download can resume)
    if minimal:
        print(f"Downloading openneuro data while excluding files/folders listed under "
              f"openneuro_exclusions in {exclusions_file}")
        _run_with_retry(download_openneuro, "OpenNeuro data")
    else:
        print("Cloning BIDS and downloading full fMRIprep derivatives (derivatives are not minimal)")
        try:
            subprocess.run(["datalad", "clone", git_repo_url, str(bids_input_dir)], check=True)
        except subprocess.CalledProcessError as e:
            if "error: unknown option `show-origin`" in str(e):
                print("     Error: Your Git version may be outdated. Please confirm and update Git.")
                print("     Use 'git --version' to check your version.")
            raise RuntimeError(f"Failed to clone dataset: {e}") from e
        try:
            subprocess.run(["datalad", "siblings", "-d", str(bids_input_dir), "enable", "-s", "s3-PRIVATE"],
                           check=True)
        except subprocess.CalledProcessError:
            print("        Warning: 's3-PRIVATE' sibling not found or could not be enabled. Continuing...")
        print(f"    {study_id}. Dataset cloned successfully (no files downloaded).")

    print("Downloading fMRIprep derivatives...")
    _run_with_retry(download_fmriprep, "fMRIPrep derivatives")

    download_mriqc_group(study_id, spec_dir / "mriqc_summary")


def download_mriqc_group(study_id: str, mriqc_summ: Path) -> None:
    """Copy only the MRIQC group report files; skipped if the folder already exists."""
    if mriqc_summ.exists():
        print(f"        {study_id} MRIQC already exists. Skipping group summary data download.")
        return
    mriqc_summ.mkdir(parents=True, exist_ok=True)
    list_cmd = aws_cmd() + ["s3", "ls", "--no-sign-request",
                            f"s3://openneuro-derivatives/mriqc/{study_id}-mriqc", "--recursive"]
    try:
        result = subprocess.run(list_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to list MRIQC files: {e}")
        print("Continuing without MRIQC group files...")
        return
    files = [line.split()[-1] for line in result.stdout.splitlines() if "group" in line]
    print(f"Found {len(files)} group files to download")
    if not files:
        print("No 'group' files found. Skipping MRIQC download.")
        return
    for s3_file_path in files:
        file_path = mriqc_summ / Path(s3_file_path).name
        cmd = aws_cmd() + ["s3", "cp", "--no-sign-request",
                           f"s3://openneuro-derivatives/{s3_file_path}", str(file_path)]
        try:
            subprocess.run(cmd, check=True)
            print(f"    Downloaded: {s3_file_path} to {file_path}")
        except subprocess.CalledProcessError as e:
            print(f"    Warning: Failed to download {s3_file_path}: {e}")


def link_derivatives(source_dir: Path, dest_dir: Optional[Path] = None) -> int:
    """Hard-link every file under ``source_dir`` into ``source_dir/derivatives`` (mirroring the tree).

    Skips the destination itself, hidden paths and ``*_events.tsv``. Existing destination files are
    replaced (``ln -f``). Returns the number of files linked.
    """
    source_dir = Path(source_dir)
    dest_dir = Path(dest_dir) if dest_dir else source_dir / "derivatives"
    dest_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for dirpath, dirnames, filenames in os.walk(source_dir):
        here = Path(dirpath)
        rel_dir = here.relative_to(source_dir)
        # prune destination and hidden directories
        dirnames[:] = [d for d in dirnames
                       if not d.startswith(".") and (here / d) != dest_dir and not d.endswith("_events.tsv")]
        for d in dirnames:
            (dest_dir / rel_dir / d).mkdir(parents=True, exist_ok=True)
        for name in filenames:
            if name.startswith(".") or name.endswith("_events.tsv"):
                continue
            src = here / name
            dst = dest_dir / rel_dir / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            try:
                os.link(src, dst, follow_symlinks=False)
            except (NotImplementedError, TypeError):
                os.link(src, dst)
            n += 1
    return n


def make_user_writable(root: Path) -> None:
    """``chmod -R u+w`` without following symlinks (simplifies deleting datalad clones)."""
    root = Path(root)
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames + [""]:
            p = Path(dirpath) / name if name else Path(dirpath)
            if p.is_symlink():
                continue
            try:
                p.chmod(p.stat().st_mode | stat.S_IWUSR)
            except OSError:
                pass
