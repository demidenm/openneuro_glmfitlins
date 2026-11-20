import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from openneuro_glmfitlins.io.trim import trim_confounds
from openneuro_glmfitlins.qc.similarity import calc_niftis_meanstd, get_low_quality_subs, voxel_inout_ratio
from openneuro_glmfitlins.qc.vif import gen_vifdf


def test_vif_orthogonal_regressors_are_one():
    n = 40
    a = np.tile([1, 0, 0, 0], n // 4).astype(float)
    b = np.roll(a, 2)
    desmat = pd.DataFrame({"a": a, "b": b, "intercept": np.ones(n)})
    con, reg, df = gen_vifdf(desmat, {"AvB": "a - b"}, nuisance_regressors=[])
    assert reg["a"] == pytest.approx(1.0, rel=0.2)
    assert set(df["type"]) == {"contrast", "regressor"}
    assert "intercept" not in reg


def test_vif_collinear_regressors_are_large():
    rng = np.random.default_rng(0)
    a = rng.normal(size=100)
    desmat = pd.DataFrame({"a": a, "b": a + rng.normal(scale=0.05, size=100)})
    _, reg, _ = gen_vifdf(desmat, {}, nuisance_regressors=[])
    assert reg["a"] > 10


def test_low_quality_subs():
    df = pd.DataFrame({"img1": ["sub-02", "sub-01", "sub-03"], "dice": [0.5, 0.5, 0.9],
                       "voxoutmask": [0.5, 0.5, 0.5]})
    assert get_low_quality_subs(df) == ["sub-01", "sub-02"]
    assert get_low_quality_subs(df, dice_thresh=0.4) == []


def _img(path, data):
    nib.Nifti1Image(data.astype(np.float32), np.eye(4)).to_filename(path)
    return path


def test_voxel_inout_ratio(tmp_path):
    mask = np.zeros((4, 4, 4)); mask[:2] = 1
    img = np.zeros((4, 4, 4)); img[0, 0, :] = 1; img[3, 0, 0] = 1  # 4 in, 1 out
    pin, pout, ratio = voxel_inout_ratio(_img(tmp_path / "i.nii.gz", img), _img(tmp_path / "m.nii.gz", mask))
    assert (pin, pout, ratio) == (80.0, 20.0, 4.0)


def test_mean_std(tmp_path):
    paths = [_img(tmp_path / f"{i}.nii.gz", np.full((2, 2, 2), v)) for i, v in enumerate([1.0, 3.0])]
    mean, std = calc_niftis_meanstd(paths)
    assert np.allclose(mean.get_fdata(), 2.0)
    assert np.allclose(std.get_fdata(), np.sqrt(2))
    with pytest.raises(AssertionError):
        calc_niftis_meanstd(paths[:1])


def test_trim_confounds(tmp_path):
    f = tmp_path / "c.tsv"
    pd.DataFrame({"x": range(5)}).to_csv(f, sep="\t", index=False)
    assert list(trim_confounds(f, 2)["x"]) == [2, 3, 4]
    with pytest.raises(ValueError):
        trim_confounds(f, 5)
