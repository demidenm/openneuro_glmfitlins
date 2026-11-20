import pytest

from openneuro_glmfitlins.cli import _resolve_ids, build_parser


def parse(argv):
    p = build_parser()
    a = p.parse_args(argv)
    _resolve_ids(a, p)
    return a


def test_positional_and_flags_equivalent():
    a = parse(["fit", "ds1", "tsk", "mod"])
    b = parse(["fit", "-d", "ds1", "-t", "tsk", "--suffix", "mod"])
    assert (a.study_id, a.task, a.suffix) == (b.study_id, b.task, b.suffix) == ("ds1", "tsk", "mod")


def test_details_flag():
    assert parse(["details", "-d", "ds1"]).study_id == "ds1"


def test_missing_task_errors():
    with pytest.raises(SystemExit):
        parse(["validate", "-d", "ds1"])


def test_conflict_errors():
    with pytest.raises(SystemExit):
        parse(["fit", "ds1", "tsk", "-t", "other"])


def test_fit_option_precedence(monkeypatch):
    from openneuro_glmfitlins.fit.fitlins import resolve_options

    monkeypatch.setenv("SLURM_CPUS_PER_TASK", "3")
    monkeypatch.setenv("SLURM_MEM_PER_NODE", "20480")
    o = resolve_options({"smoothing": None, "n_cpus": None}, {"smoothing": "8:run:iso", "estimator": "afni"})
    assert (o.smoothing, o.estimator, o.n_cpus, o.mem_gb) == ("8:run:iso", "afni", 3, 20)
    o = resolve_options({"smoothing": "4:run:iso", "n_cpus": 2}, {"smoothing": "8:run:iso"})
    assert (o.smoothing, o.n_cpus) == ("4:run:iso", 2)
    with pytest.raises(ValueError):
        resolve_options({}, {"bogus": 1})
