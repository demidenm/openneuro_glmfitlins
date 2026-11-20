import numpy as np
import pandas as pd
import pytest

from openneuro_glmfitlins.events import EventsContext, get_events_fixer, register_events, registered_studies
from openneuro_glmfitlins.events.prep import alt_path, apply_events_fix, backup_path


def _ctx(tmp_path, study="dsX", task="t"):
    return EventsContext(path=tmp_path / "sub-01_task-t_events.tsv", study_id=study, task=task)


def test_registry_has_every_dataset_once():
    studies = registered_studies()
    assert len(studies) == len(set(studies)) == 35
    assert {"ds000001", "ds001357", "ds004656", "ds002294"} <= set(studies)


def test_unknown_dataset_raises():
    with pytest.raises(LookupError, match="ds999999"):
        get_events_fixer("ds999999")


def test_duplicate_registration_raises(monkeypatch):
    from openneuro_glmfitlins.events import registry

    monkeypatch.setattr(registry, "_REGISTRY", dict(registry._REGISTRY))

    @register_events("ds_test_dup")
    def first(df, task, ctx):
        return None

    with pytest.raises(ValueError, match="registered twice"):
        @register_events("ds_test_dup")
        def second(df, task, ctx):
            return None


def test_ds000001_fills_nans(tmp_path):
    cols = ["cash_demean", "control_pumps_demean", "explode_demean", "pumps_demean", "response_time"]
    df = pd.DataFrame({"onset": [0, 1], "duration": [1, 1], "trial_type": ["a", "b"],
                       **{c: [1.0, np.nan] for c in cols}})
    fix = get_events_fixer("ds000001")
    out = fix(df, "balloonanalogrisktask", _ctx(tmp_path))
    assert not out[cols].isna().any().any()
    assert fix(out, "balloonanalogrisktask", _ctx(tmp_path)) is None  # already clean
    assert fix(df, "othertask", _ctx(tmp_path)) is None


def test_ds001357_messy_headers(tmp_path):
    # leading-space headers and values, as in the raw files
    df = pd.DataFrame({"onset": [" 1.5", "3"], " duration": [" 2", "x"], " events": [" face A", "house"]})
    out = get_events_fixer("ds001357")(df, "viewing", _ctx(tmp_path))
    assert list(out["trial_type"]) == ["faceA", "house"]
    assert list(out["onset"]) == [1.5, 3.0]
    assert list(out["duration"]) == [2.0, 0.0]  # non-numeric -> 0


def _fix_add_col(df, task, ctx):
    if "fixed" in df.columns:
        return None
    df = df.copy()
    df["fixed"] = 1
    return df


def test_apply_events_fix_backs_up_once_and_is_idempotent(tmp_path):
    f = tmp_path / "sub-01_task-t_events.tsv"
    original = "onset\tduration\ttrial_type\n0\t1\ta\n"
    f.write_text(original)

    assert apply_events_fix(_fix_add_col, f, "t", "dsX") == "modified"
    assert backup_path(f).read_text() == original
    first = f.read_text()
    assert "fixed" in first

    # second run reads the backup, so the fix is not stacked and nothing is rewritten
    assert apply_events_fix(_fix_add_col, f, "t", "dsX") == "unchanged"
    assert f.read_text() == first
    assert backup_path(f).read_text() == original


def test_apply_events_fix_no_change_writes_nothing(tmp_path):
    f = tmp_path / "sub-01_task-t_events.tsv"
    f.write_text("onset\tduration\n0\t1\n")
    assert apply_events_fix(lambda df, task, ctx: None, f, "t", "dsX") == "unchanged"
    assert not backup_path(f).exists()
    # returning an identical table also writes nothing
    assert apply_events_fix(lambda df, task, ctx: df, f, "t", "dsX") == "unchanged"
    assert not backup_path(f).exists()


def test_apply_events_fix_restores_original_when_fix_no_longer_applies(tmp_path):
    f = tmp_path / "sub-01_task-t_events.tsv"
    original = "onset\tduration\n0\t1\n"
    f.write_text(original)
    apply_events_fix(_fix_add_col, f, "t", "dsX")
    assert apply_events_fix(lambda df, task, ctx: None, f, "t", "dsX") == "modified"
    assert f.read_text() == original


def test_alt_path_replaces_only_the_root(tmp_path):
    deriv = tmp_path / "derivatives_x" / "fmriprep" / "ds1" / "derivatives"
    alt = deriv.parent / "derivatives_alt"
    bold = deriv / "sub-01" / "func" / "sub-01_derivatives_bold.nii.gz"
    bold.parent.mkdir(parents=True)
    bold.touch()
    assert alt_path(bold, deriv, alt) == alt / "sub-01" / "func" / "sub-01_derivatives_bold.nii.gz"
    with pytest.raises(ValueError):
        alt_path(tmp_path / "elsewhere.nii.gz", deriv, alt)
