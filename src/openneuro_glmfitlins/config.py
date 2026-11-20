"""Configuration loading and path resolution.

Config file lookup (first match wins):
  1. ``$GLMFITLINS_CONFIG``
  2. ``<repo root>/path_config.json``  (copy ``path_config.example.json`` to create it)

Each config key can be overridden by an environment variable (see ``ENV_OVERRIDES``).
The repo root is inferred from the package location (``$GLMFITLINS_REPO`` overrides it).

All file naming for task variants goes through ``task_label`` so specs, contrasts, subjects,
FitLins outputs and group reports use one rule: ``{task}`` or ``{task}-{suffix}``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CONFIG_ENV = "GLMFITLINS_CONFIG"
REPO_ENV = "GLMFITLINS_REPO"
CONFIG_NAME = "path_config.json"
EXAMPLE_CONFIG_NAME = "path_config.example.json"

ENV_OVERRIDES = {
    "datasets_folder": "GLMFITLINS_DATASETS_FOLDER",
    "tmp_folder": "GLMFITLINS_TMP_FOLDER",
    "data_type": "GLMFITLINS_DATA_TYPE",
    "fmriprep_simg": "GLMFITLINS_FMRIPREP_SIMG",
    "freesurfer_license": "GLMFITLINS_FREESURFER_LICENSE",
}
REQUIRED_KEYS = ("datasets_folder", "tmp_folder")
DATA_TYPES = ("openneuro", "house")


class ConfigError(RuntimeError):
    """Raised when the configuration is missing or invalid."""


def task_label(task: str, suffix: Optional[str] = None) -> str:
    """Label used in every file/dir name for a task variant: ``task`` or ``task-suffix``."""
    return f"{task}-{suffix}" if suffix else task


def _inferred_repo_root() -> Optional[Path]:
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "pyproject.toml").exists() and (candidate / "statsmodel_specs").exists():
        return candidate
    return None


def repo_root(config_values: Optional[dict] = None) -> Path:
    """Repository root: $GLMFITLINS_REPO > package location > legacy ``openneuro_glmrepo`` > cwd."""
    env = os.environ.get(REPO_ENV)
    if env:
        return Path(env).expanduser().resolve()
    inferred = _inferred_repo_root()
    if inferred:
        return inferred
    legacy = (config_values or {}).get("openneuro_glmrepo")
    if legacy:
        return Path(legacy).expanduser().resolve()
    return Path.cwd().resolve()


@dataclass(frozen=True)
class Config:
    datasets_folder: Path
    tmp_folder: Path
    repo_dir: Path
    data_type: str = "openneuro"
    fmriprep_simg: Optional[str] = None
    freesurfer_license: Optional[str] = None
    source: Optional[Path] = None
    extra: dict = field(default_factory=dict)

    @property
    def specs_root(self) -> Path:
        return self.repo_dir / "statsmodel_specs"

    def study(self, study_id: str) -> "StudyPaths":
        return StudyPaths(self, study_id)


def find_config_file() -> Path:
    env = os.environ.get(CONFIG_ENV)
    if env:
        path = Path(env).expanduser()
        if not path.is_file():
            raise ConfigError(f"${CONFIG_ENV} points to {path}, which does not exist.")
        return path
    root = repo_root()
    path = root / CONFIG_NAME
    if path.is_file():
        return path
    raise ConfigError(
        f"Config file not found at {path}.\n"
        f"Create it with:  cp {root / EXAMPLE_CONFIG_NAME} {path}  and edit the paths,\n"
        f"set ${CONFIG_ENV}, or run setup_uv.sh. Check with: uv run glmfitlins config"
    )


def load_config(path: Optional[Path] = None, env: Optional[dict] = None) -> Config:
    """Load config from ``path`` (or the default lookup) and apply env-var overrides."""
    env = os.environ if env is None else env
    values: dict = {}
    source = None
    try:
        source = Path(path) if path else find_config_file()
        with open(source) as f:
            values = json.load(f)
    except ConfigError:
        # allow a config made entirely of env vars
        if not all(env.get(ENV_OVERRIDES[k]) for k in REQUIRED_KEYS):
            raise
    except json.JSONDecodeError as e:
        raise ConfigError(f"Config file {source} is not valid JSON: {e}") from e

    for key, var in ENV_OVERRIDES.items():
        if env.get(var):
            values[key] = env[var]

    missing = [k for k in REQUIRED_KEYS if not values.get(k)]
    if missing:
        raise ConfigError(f"Config is missing required keys {missing} (file: {source}).")

    data_type = values.get("data_type", "openneuro")
    if data_type not in DATA_TYPES:
        raise ConfigError(f"Unknown data_type '{data_type}'. Expected one of {DATA_TYPES}.")

    known = set(ENV_OVERRIDES) | {"openneuro_glmrepo"}
    return Config(
        datasets_folder=Path(values["datasets_folder"]).expanduser(),
        tmp_folder=Path(values["tmp_folder"]).expanduser(),
        repo_dir=repo_root(values),
        data_type=data_type,
        fmriprep_simg=values.get("fmriprep_simg"),
        freesurfer_license=values.get("freesurfer_license"),
        source=source,
        extra={k: v for k, v in values.items() if k not in known},
    )


@dataclass(frozen=True)
class StudyPaths:
    """All paths for one dataset. ``suffix`` arguments select a task variant (see ``task_label``)."""

    cfg: Config
    study_id: str

    # ---- repo side (specs and reports)
    @property
    def spec_dir(self) -> Path:
        return self.cfg.specs_root / self.study_id

    @property
    def basic_details(self) -> Path:
        return self.spec_dir / f"{self.study_id}_basic-details.json"

    def spec_file(self, task: str, suffix: Optional[str] = None) -> Path:
        return self.spec_dir / f"{self.study_id}-{task_label(task, suffix)}_specs.json"

    def _input_file(self, task: str, suffix: Optional[str], kind: str) -> Path:
        variant = self.spec_dir / f"{self.study_id}-{task_label(task, suffix)}_{kind}.json"
        if suffix and not variant.exists():
            # variants without their own file share the task's file
            return self.spec_dir / f"{self.study_id}-{task}_{kind}.json"
        return variant

    def contrasts_file(self, task: str, suffix: Optional[str] = None) -> Path:
        return self._input_file(task, suffix, "contrasts")

    def subjects_file(self, task: str, suffix: Optional[str] = None) -> Path:
        return self._input_file(task, suffix, "subjects")

    def group_dir(self, task: str, suffix: Optional[str] = None, out_dir: Optional[Path] = None) -> Path:
        base = Path(out_dir) if out_dir else self.spec_dir
        return base / f"group_{task_label(task, suffix)}"

    # ---- data side
    @property
    def bids_dir(self) -> Path:
        return self.cfg.datasets_folder / "input" / self.study_id

    @property
    def fmriprep_root(self) -> Path:
        return self.cfg.datasets_folder / "fmriprep" / self.study_id

    @property
    def fmriprep_dir(self) -> Path:
        return self.fmriprep_root / "derivatives"

    @property
    def fmriprep_alt_dir(self) -> Path:
        return self.fmriprep_root / "derivatives_alt"

    def fit_fmriprep_dir(self) -> Path:
        """Trimmed derivatives (``derivatives_alt``) when they exist, else ``derivatives``."""
        return self.fmriprep_alt_dir if self.fmriprep_alt_dir.is_dir() else self.fmriprep_dir

    def analysis_dir(self, task: str, suffix: Optional[str] = None) -> Path:
        return self.cfg.datasets_folder / "analyses" / self.study_id / f"task-{task_label(task, suffix)}"

    def scratch_dir(self, task: str, suffix: Optional[str] = None) -> Path:
        return self.cfg.tmp_folder / "fitlins" / f"task-{task_label(task, suffix)}"

    @property
    def to_process_dir(self) -> Path:
        return self.cfg.datasets_folder / "analyses" / ".to_process"


def read_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)
