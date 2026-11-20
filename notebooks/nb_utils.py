"""Small helpers shared by the tutorial notebooks.

Everything is read from the *public* OpenNeuro buckets over plain HTTPS (no AWS account, no AWS CLI):

* raw BIDS data:      https://s3.amazonaws.com/openneuro.org/<dsXXXXXX>/...
* FitLins derivatives: https://openneuro-derivatives.s3.amazonaws.com/fitlins/<dsXXXXXX>-fitlins/task-<task>/...

Downloads are cached in ``notebooks/.cache`` so re-running a notebook is fast.
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

RAW_BUCKET = "https://s3.amazonaws.com/openneuro.org"
DERIV_BUCKET = "https://openneuro-derivatives.s3.amazonaws.com"
CACHE_DIR = Path(__file__).resolve().parent / ".cache"
_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


def _get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def s3_list(bucket: str, prefix: str, delimiter: str | None = "/") -> tuple[list[str], list[dict]]:
    """List one S3 "folder". Returns ``(sub_prefixes, files)``; files are ``{"key", "size"}`` dicts.

    ``delimiter=None`` lists everything below the prefix (recursive).
    """
    dirs: list[str] = []
    files: list[dict] = []
    token = None
    while True:
        params = {"list-type": "2", "prefix": prefix}
        if delimiter:
            params["delimiter"] = delimiter
        if token:
            params["continuation-token"] = token
        root = ET.fromstring(_get(f"{bucket}/?{urllib.parse.urlencode(params)}"))
        dirs += [p.findtext("s3:Prefix", namespaces=_NS) for p in root.findall("s3:CommonPrefixes", _NS)]
        files += [
            {"key": c.findtext("s3:Key", namespaces=_NS), "size": int(c.findtext("s3:Size", namespaces=_NS))}
            for c in root.findall("s3:Contents", _NS)
        ]
        if root.findtext("s3:IsTruncated", namespaces=_NS) != "true":
            return dirs, files
        token = root.findtext("s3:NextContinuationToken", namespaces=_NS)


def fetch(bucket: str, key: str, cache_dir: Path = CACHE_DIR) -> Path:
    """Download ``key`` once and return the local path."""
    dest = Path(cache_dir) / ("raw" if bucket == RAW_BUCKET else "derivatives") / key
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        tmp.write_bytes(_get(f"{bucket}/{urllib.parse.quote(key)}"))
        tmp.rename(dest)
    return dest


# ---- OpenNeuro FitLins derivatives layout -----------------------------------------------------
def list_studies() -> list[str]:
    """All dataset IDs that have FitLins derivatives."""
    dirs, _ = s3_list(DERIV_BUCKET, "fitlins/")
    return sorted(re.findall(r"fitlins/(ds\d+)-fitlins/", " ".join(dirs)))


def list_tasks(study_id: str) -> list[str]:
    """Task folders (``task-<label>``) with derivatives for a dataset."""
    dirs, _ = s3_list(DERIV_BUCKET, f"fitlins/{study_id}-fitlins/")
    return sorted(d.rstrip("/").split("task-")[-1] for d in dirs if "/task-" in d)


def deriv_prefix(study_id: str, task: str) -> str:
    return f"fitlins/{study_id}-fitlins/task-{task}/"


def list_deriv_files(study_id: str, task: str) -> list[dict]:
    """Every file below one task's derivatives (recursive; ~2000 entries for a small study)."""
    return s3_list(DERIV_BUCKET, deriv_prefix(study_id, task), delimiter=None)[1]


def list_raw_subjects(study_id: str) -> list[str]:
    dirs, _ = s3_list(RAW_BUCKET, f"{study_id}/")
    return sorted(d.rstrip("/").split("/")[-1] for d in dirs if "/sub-" in d)
