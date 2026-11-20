import json

import pytest

from openneuro_glmfitlins.config import ConfigError, load_config, task_label


def test_task_label():
    assert task_label("learning") == "learning"
    assert task_label("learning", None) == "learning"
    assert task_label("learning", "") == "learning"
    assert task_label("learning", "mod2") == "learning-mod2"


@pytest.mark.parametrize("suffix,label", [(None, "learning"), ("mod2", "learning-mod2")])
def test_paths_use_one_label(cfg, suffix, label):
    p = cfg.study("ds003425")
    assert p.spec_file("learning", suffix).name == f"ds003425-{label}_specs.json"
    assert p.analysis_dir("learning", suffix).name == f"task-{label}"
    assert p.scratch_dir("learning", suffix).name == f"task-{label}"
    assert p.group_dir("learning", suffix).name == f"group_{label}"
    assert p.group_dir("learning", suffix, out_dir=cfg.tmp_folder).parent == cfg.tmp_folder


def test_variant_inputs_fall_back_to_task_files(cfg):
    p = cfg.study("ds1")
    p.spec_dir.mkdir(parents=True)
    assert p.contrasts_file("t", "v").name == "ds1-t_contrasts.json"
    (p.spec_dir / "ds1-t-v_contrasts.json").write_text("{}")
    assert p.contrasts_file("t", "v").name == "ds1-t-v_contrasts.json"
    assert p.subjects_file("t", "v").name == "ds1-t_subjects.json"


def test_fit_fmriprep_dir_prefers_alt(cfg):
    p = cfg.study("ds1")
    assert p.fit_fmriprep_dir() == p.fmriprep_dir
    p.fmriprep_alt_dir.mkdir(parents=True)
    assert p.fit_fmriprep_dir() == p.fmriprep_alt_dir


def test_load_config_file_and_env_override(tmp_path):
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"datasets_folder": "/a", "tmp_folder": "/b", "data_type": "house"}))
    cfg = load_config(f, env={"GLMFITLINS_TMP_FOLDER": "/override"})
    assert str(cfg.datasets_folder) == "/a"
    assert str(cfg.tmp_folder) == "/override"
    assert cfg.data_type == "house"


def test_load_config_from_env_only(monkeypatch, tmp_path):
    monkeypatch.setenv("GLMFITLINS_CONFIG", str(tmp_path / "missing.json"))
    with pytest.raises(ConfigError):
        load_config(env={})
    cfg = load_config(env={"GLMFITLINS_DATASETS_FOLDER": "/d", "GLMFITLINS_TMP_FOLDER": "/t"})
    assert str(cfg.datasets_folder) == "/d"


def test_load_config_rejects_bad_values(tmp_path):
    f = tmp_path / "c.json"
    f.write_text(json.dumps({"datasets_folder": "/a"}))
    with pytest.raises(ConfigError, match="tmp_folder"):
        load_config(f, env={})
    f.write_text(json.dumps({"datasets_folder": "/a", "tmp_folder": "/b", "data_type": "cloud"}))
    with pytest.raises(ConfigError, match="data_type"):
        load_config(f, env={})
