import copy
import json

import pytest

from conftest import SPECS, write_json
from openneuro_glmfitlins.specs.build import build_spec, find_node, load_template, run_spec_step, update_spec
from openneuro_glmfitlins.specs.validate import check_contrast_weights, run_validate, validate_spec

SUBJECTS = ["01", "02", "03"]


def test_build_multi_run(basic_details, contrasts):
    spec = build_spec(load_template(), "ds1", "multi", SUBJECTS, basic_details, contrasts)
    assert spec["Name"] == "ds1"
    assert spec["Input"] == {"subject": SUBJECTS, "task": ["multi"], "run": [1, 2]}
    assert find_node(spec, "Run")["Contrasts"] == contrasts
    assert find_node(spec, "Subject") is not None


def test_build_single_run_drops_subject_node_by_level(basic_details, contrasts):
    template = load_template()
    template["Nodes"].reverse()  # Subject node no longer second
    spec = build_spec(template, "ds1", "single", SUBJECTS, basic_details, contrasts)
    assert find_node(spec, "Subject") is None
    assert {n["Level"] for n in spec["Nodes"]} == {"Run", "Dataset"}
    assert "run" not in spec["Input"]


def test_build_sessions_added_to_groupby(basic_details, contrasts):
    spec = build_spec(load_template(), "ds1", "sess", SUBJECTS, basic_details, contrasts)
    assert spec["Input"]["session"] == ["01", "02"]
    assert all("session" in n["GroupBy"] for n in spec["Nodes"])


def test_build_does_not_mutate_template(basic_details, contrasts):
    template = load_template()
    before = copy.deepcopy(template)
    build_spec(template, "ds1", "sess", SUBJECTS, basic_details, contrasts)
    assert template == before


def test_update_preserves_hand_edits(basic_details, contrasts):
    spec = build_spec(load_template(), "ds1", "multi", SUBJECTS, basic_details, contrasts)
    run = find_node(spec, "Run")
    run["Transformations"]["Instructions"].append({"Name": "Scale", "Input": ["rt"]})
    run["Model"]["X"].append("rt")

    new_contrasts = contrasts[:1]
    new, changes = update_spec(spec, "ds1", "multi", ["01", "02"], basic_details, new_contrasts)
    assert new["Input"]["subject"] == ["01", "02"]
    assert find_node(new, "Run")["Contrasts"] == new_contrasts
    assert find_node(new, "Run")["Transformations"] == run["Transformations"]
    assert find_node(new, "Run")["Model"]["X"][-1] == "rt"
    assert len(changes) == 2

    again, changes = update_spec(new, "ds1", "multi", ["01", "02"], basic_details, new_contrasts)
    assert again == new and changes == []


def test_update_removes_run_when_single_run(basic_details, contrasts):
    spec = build_spec(load_template(), "ds1", "multi", SUBJECTS, basic_details, contrasts)
    new, changes = update_spec(spec, "ds1", "single", SUBJECTS, basic_details, contrasts)
    assert "run" not in new["Input"]
    assert any("Input.run: removed" in c for c in changes)


def test_validate_clean_and_drift(basic_details, contrasts):
    spec = build_spec(load_template(), "ds1", "multi", SUBJECTS, basic_details, contrasts)
    assert validate_spec(spec, "multi", SUBJECTS, basic_details, contrasts) == []
    # subject order does not matter
    assert validate_spec(spec, "multi", SUBJECTS[::-1], basic_details, contrasts) == []

    issues = validate_spec(spec, "multi", ["01", "02"], basic_details, contrasts[:1])
    errors = [i.message for i in issues if i.level == "error"]
    assert any("extra in spec: ['03']" in e for e in errors)
    assert any("Run-node Contrasts" in e for e in errors)


def test_validate_runs_are_warnings(basic_details, contrasts):
    spec = build_spec(load_template(), "ds1", "single", SUBJECTS, basic_details, contrasts)
    issues = validate_spec(spec, "single", SUBJECTS, {"Tasks": {"single": {"task_runs": [1, 2]}}}, contrasts)
    assert [i.level for i in issues] == ["warning"]


@pytest.mark.parametrize("weights,conds,levels", [
    ([1, -1], ["a", "b"], []),
    ([1], ["a", "b"], ["error"]),
    ([1, -0.5], ["a", "b"], ["warning"]),
    ([0.5, 0.5], ["a", "b"], []),
    ([[1, 0], [0, 1]], ["a", "b"], []),           # F-test rows
    ([[1, 0, 0], [0, 1]], ["a", "b"], ["error"]),
])
def test_contrast_weights(weights, conds, levels):
    spec = {"Nodes": [{"Level": "Run", "Name": "run", "Contrasts": [
        {"Name": "c", "ConditionList": conds, "Weights": weights, "Test": "t"}]}]}
    assert [i.level for i in check_contrast_weights(spec)] == levels


@pytest.mark.parametrize("study", ["ds000001", "ds001357"])
def test_reference_specs_have_consistent_weights(study):
    for spec_file in (SPECS / study).glob("*_specs.json"):
        spec = json.loads(spec_file.read_text())
        assert [i for i in check_contrast_weights(spec) if i.level == "error"] == [], spec_file.name


def test_reference_drift_is_reported():
    """ds001357 viewing lists subject 017 in the spec but not in subjects.json (see REFACTOR_PLAN #20)."""
    d = SPECS / "ds001357"
    spec = json.loads((d / "ds001357-viewing_specs.json").read_text())
    subjects = json.loads((d / "ds001357-viewing_subjects.json").read_text())["Subjects"]
    issues = validate_spec(spec, "viewing", subjects, None, None)
    assert any("017" in i.message for i in issues)


def _inputs(cfg, basic_details, contrasts, task="multi"):
    p = cfg.study("ds1")
    write_json(p.basic_details, basic_details)
    write_json(p.subjects_file(task), {"Subjects": SUBJECTS})
    write_json(p.contrasts_file(task), {"Contrasts": contrasts})
    return p


def test_run_spec_step_create_then_update(cfg, basic_details, contrasts, capsys):
    p = _inputs(cfg, basic_details, contrasts)
    assert run_spec_step(p, "multi", check=False) == 0
    created = p.spec_file("multi").read_text()

    # without --update an existing spec is left alone
    write_json(p.subjects_file("multi"), {"Subjects": ["01"]})
    assert run_spec_step(p, "multi", check=False) == 0
    assert p.spec_file("multi").read_text() == created
    assert run_validate(p, "multi") == 1

    assert run_spec_step(p, "multi", update=True, check=False) == 0
    assert json.loads(p.spec_file("multi").read_text())["Input"]["subject"] == ["01"]
    assert run_validate(p, "multi") == 0


def test_run_spec_step_suffix_uses_hyphen_and_shared_inputs(cfg, basic_details, contrasts):
    p = _inputs(cfg, basic_details, contrasts)
    assert run_spec_step(p, "multi", "mod2", check=False) == 0
    assert (p.spec_dir / "ds1-multi-mod2_specs.json").exists()


def test_run_spec_step_missing_inputs_fails(cfg, basic_details):
    p = cfg.study("ds1")
    write_json(p.basic_details, basic_details)
    assert run_spec_step(p, "multi", check=False) == 1
