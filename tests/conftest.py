import json
from pathlib import Path

import pytest

from openneuro_glmfitlins.config import Config

REPO = Path(__file__).resolve().parents[1]
SPECS = REPO / "statsmodel_specs"


@pytest.fixture
def cfg(tmp_path):
    """Config whose repo has an empty statsmodel_specs/ under tmp_path."""
    repo = tmp_path / "repo"
    (repo / "statsmodel_specs").mkdir(parents=True)
    return Config(datasets_folder=tmp_path / "data", tmp_folder=tmp_path / "scratch", repo_dir=repo)


@pytest.fixture
def basic_details():
    return {
        "Subjects": ["01", "02", "03"],
        "Sessions": [],
        "Tasks": {
            "multi": {"bold_volumes": 100, "task_runs": [1, 2], "task_sessions": []},
            "single": {"bold_volumes": 100, "task_runs": [], "task_sessions": []},
            "sess": {"bold_volumes": 100, "task_runs": [1, 2], "task_sessions": ["01", "02"]},
        },
    }


@pytest.fixture
def contrasts():
    return [
        {"Name": "AvB", "ConditionList": ["trial_type.a", "trial_type.b"], "Weights": [1, -1], "Test": "t"},
        {"Name": "A", "ConditionList": ["trial_type.a"], "Weights": [1], "Test": "t"},
    ]


def write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return path
