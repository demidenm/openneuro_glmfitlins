import subprocess
import sys

import pytest

from openneuro_glmfitlins.cli import build_parser
from openneuro_glmfitlins.fit.fitlins import FitOptions, build_fitlins_command


def test_import_is_cheap():
    code = ("import sys, openneuro_glmfitlins, openneuro_glmfitlins.cli, openneuro_glmfitlins.config;"
            "print(','.join(m for m in ('nilearn','bids','nbformat','IPython','matplotlib','pandas') if m in sys.modules))")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.strip()
    assert out == ""


def test_fit_args_like_old_getopts():
    a = build_parser().parse_args(["fit", "-s", "6:run:iso", "-e", "afni", "ds003425", "learning", "mod2"])
    assert (a.study_id, a.task, a.suffix, a.smoothing, a.estimator) == ("ds003425", "learning", "mod2", "6:run:iso", "afni")
    assert (a.n_cpus, a.mem_gb) == (6, 32)


def test_fit_rejects_unknown_estimator():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["fit", "-e", "spm", "ds1", "t"])


def test_report_defaults():
    a = build_parser().parse_args(["report", "ds1", "t"])
    assert (a.suffix, a.zstat_thresh, a.dice_thresh, a.voxout_thresh) == (None, 2.3, 0.85, 0.10)


def test_fitlins_command_matches_previous_shell_script():
    cmd = build_fitlins_command("BIDS", "OUT", "MODEL", "FMRIPREP", "WORK", FitOptions())
    assert cmd[1:] == [
        "BIDS", "OUT", "participant", "-m", "MODEL", "-d", "FMRIPREP",
        "--ignore", r"sub-.*_physio\.(json|tsv\.gz)", "--drop-missing",
        "--space", "MNI152NLin2009cAsym", "--desc-label", "preproc",
        "--smoothing", "5:run:iso", "--estimator", "nilearn",
        "--n-cpus", "6", "--mem-gb", "32", "-w", "WORK", "-vvv",
    ]


def test_readme_threshold_wording_unchanged_at_defaults():
    from openneuro_glmfitlins.reports.readme import _fmt_prop

    assert (_fmt_prop(0.85), _fmt_prop(0.10)) == (".85", ".10")
