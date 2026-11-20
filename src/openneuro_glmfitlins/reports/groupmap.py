"""Stage 5: group report (design/contrast figures, VIF, R-squared QC, group z-maps, README)."""

from __future__ import annotations

import fnmatch
import json
import os
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Optional

NOISE_REG = [
    "motion_", "c_comp_", "a_comp_", "w_comp_", "t_comp_",
    "global_signal", "csf", "white_matter",
    "rot_", "trans_", "cosine", "drift_",
]


@dataclass
class ReportOptions:
    zstat_thresh: float = 2.3
    dice_thresh: float = 0.85
    voxout_thresh: float = 0.10
    n_workers: Optional[int] = None  # default: all CPUs but 2
    template: str = "MNI152NLin2009cAsym"
    template_resolution: int = 2


def count_files(root: Path) -> int:
    """Files plus symlinks under ``root`` (same as ``find root -type f -o -type l | wc -l``)."""
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        n += len(filenames)
        n += sum(1 for d in dirnames if (Path(dirpath) / d).is_symlink())
    return n


def folder_size(root: Path) -> str:
    try:
        return subprocess.check_output(["du", "-sh", str(root)]).split()[0].decode()
    except (OSError, subprocess.CalledProcessError):
        return "unknown size"


def build_contrast_dict(spec_results: dict) -> dict:
    contrast_dict = {}
    for node in spec_results["nodes"]:
        for contrast in node.get("contrasts", []):
            weighted = [f"{w}*`{c}`" for w, c in zip(contrast["weights"], contrast["conditions"])]
            contrast_dict[contrast["name"]] = " + ".join(weighted).replace(" + -", " - ")
    return contrast_dict


def describe_hrf(node: dict) -> str:
    components = []
    if node["if_derivative_hrf"]:
        components.append("derivatives")
    if node["if_dispersion_hrf"]:
        components.append("dispersion")
    return f"{node['convolve_model']} w/ {' & '.join(components)}" if components else node["convolve_model"]


def run_group_report(study_id: str, task: str, spec_file: Path, basic_details_file: Path, analysis_dir: Path,
                     scratch_dir: Path, group_dir: Path, opts: Optional[ReportOptions] = None) -> int:
    """Write figures/TSVs to ``group_dir/files`` and ``group_dir/README.md``. Returns an exit code."""
    import matplotlib.pyplot as plt
    import pandas as pd
    import seaborn as sns
    from nilearn.image import load_img, new_img_like
    from nilearn.plotting import plot_stat_map
    from templateflow import api

    from ..qc.similarity import calc_niftis_meanstd, get_low_quality_subs, similarity_boldstand_metrics
    from ..qc.vif import gen_vifdf
    from ..specs.summary import extract_model_info
    from .readme import generate_groupmodsummary

    plt.switch_backend("Agg")
    opts = opts or ReportOptions()
    analysis_dir, scratch_dir, group_dir = Path(analysis_dir), Path(scratch_dir), Path(group_dir)

    if not analysis_dir.is_dir():
        print(f"ERROR: Analysis directory not found: {analysis_dir}")
        return 1

    spec_imgs_dir = group_dir / "files"
    spec_imgs_dir.mkdir(parents=True, exist_ok=True)

    with open(basic_details_file) as f:
        task_info = json.load(f).get("Tasks", {}).get(task, {})
    plt_coords = tuple(task_info.get("plot_coords") or (0, 0, 0))
    cite_list = tuple(task_info.get("cite_links") or ())

    try:
        with open(spec_file) as f:
            spec_results = extract_model_info(model_spec=json.load(f))
    except Exception as e:
        print(f"Failed to load or process spec file {spec_file}: {e}")
        return 1

    levels = {node["level"] for node in spec_results["nodes"]}
    has_run, has_subject = "Run" in levels, "Subject" in levels
    num_subjects = len(spec_results["subjects"])
    first = spec_results["nodes"][0]
    hrf_model = describe_hrf(first)
    convolved_inputs = first["convolve_inputs"]
    target_vars = first["target_var"]

    # ---- example contrast / design figures from FitLins output
    contrast_images = list(analysis_dir.rglob(f"*_task-{task}_*contrasts.svg"))
    con_matrix_copy = None
    if contrast_images:
        print(f"Found example contrasts image: {contrast_images[0].name}")
        con_matrix_copy = spec_imgs_dir / f"{study_id}_task-{task}_contrast-matrix.svg"
        shutil.copy(contrast_images[0], con_matrix_copy)

    design_images = list(analysis_dir.rglob(f"*_task-{task}_*design.svg"))
    design_matrix_copy = None
    if design_images:
        print(f"Found example design mat image: {design_images[0].name}")
        design_matrix_copy = spec_imgs_dir / f"{study_id}_task-{task}_design-matrix.svg"
        shutil.copy(design_images[0], design_matrix_copy)

    design_matrices = list(analysis_dir.rglob(f"*_task-{task}_*design.tsv"))
    if design_matrices:
        print(f"Found design matrix TSV file: {design_matrices[0].name}")
        shutil.copy(design_matrices[0], spec_imgs_dir / f"{study_id}_task-{task}_design-matrix.tsv")

    # ---- VIF
    contrast_dict = build_contrast_dict(spec_results)
    all_vif_dfs, signal_regressors, noise_regressors = [], [], []
    for design_mat_path in design_matrices:
        try:
            design_matrix = pd.read_csv(design_mat_path, sep="\t")
            noise_regressors = [c for c in design_matrix.columns if any(n in c for n in NOISE_REG)]
            signal_regressors = [c for c in design_matrix.columns if not any(n in c for n in NOISE_REG)]
            _, _, vif_df = gen_vifdf(designmat=design_matrix, contrastdict=contrast_dict,
                                     nuisance_regressors=noise_regressors)
            vif_df["design_matrix"] = design_mat_path.name
            all_vif_dfs.append(vif_df)
        except Exception as e:
            print(f"Error processing {design_mat_path.name}: {e}")

    convolved_names = []
    for pattern in convolved_inputs:
        convolved_names.extend(fnmatch.filter(signal_regressors, pattern))
    parametricmodulator_names = [
        name for name in signal_regressors
        if name not in ("intercept", "constant")
        and "trial_type" not in str(name).lower()
        and name not in target_vars
    ]

    if all_vif_dfs:
        combined_vif_df = pd.concat(all_vif_dfs, ignore_index=True)
        plt.figure(figsize=(10, 6))
        sns.boxplot(x="name", y="value", hue="type", data=combined_vif_df)
        plt.title("VIF for Regressors & Contrasts")
        plt.xlabel("Type")
        plt.ylabel("VIF")
        plt.xticks(rotation=90, ha="right")
        plt.tight_layout()
        plt.savefig(spec_imgs_dir / f"{study_id}_task-{task}_vif-boxplot.png", dpi=300)
        plt.close()
    else:
        print("No VIF data available for visualization")

    # ---- R-squared mean / std maps
    rsquare_statmaps = list(analysis_dir.rglob(f"*_task-{task}*_stat-rSquare_statmap.nii.gz"))
    try:
        r2mean, r2std = calc_niftis_meanstd(path_imgs=rsquare_statmaps)
    except AssertionError as e:
        print(f"Skipping R-squared mean/std maps: {e}")
        r2mean = r2std = None
    for img, kind, label in ((r2mean, "mean", "R2 mean"), (r2std, "std", "R2 stdev")):
        if img is not None:
            plot_stat_map(
                stat_map_img=img, cut_coords=plt_coords, cmap="Reds", vmin=0, vmax=1,
                display_mode="ortho", colorbar=True,
                output_file=str(spec_imgs_dir / f"{study_id}_task-{task}_rsquare-{kind}.png"),
                title=f"{label} across {len(rsquare_statmaps)} Subject/Run Imgs",
            )

    # ---- R-squared similarity with MNI mask
    tmp_r2_dir = scratch_dir / f"{study_id}_task-{task}" / "r2tmp"
    tmp_r2_dir.mkdir(parents=True, exist_ok=True)
    try:
        for file in rsquare_statmaps:
            img1 = load_img(file)
            data1 = img1.get_fdata()
            if data1.ndim == 4 and data1.shape[3] == 1:
                new_img_like(img1, data1.squeeze()).to_filename(str(tmp_r2_dir / file.name))
    except Exception as e:
        print(f"Error during squeeze and save: {e}")

    mni_mask_dir = tmp_r2_dir / "mask"
    mni_mask_dir.mkdir(parents=True, exist_ok=True)
    mni_tmp_img = mni_mask_dir / f"{opts.template}_desc-brain_mask.nii.gz"
    if not mni_tmp_img.exists():
        template_mni = api.get(opts.template, desc="brain", resolution=opts.template_resolution,
                               suffix="mask", extension="nii.gz")
        shutil.copy(template_mni, mni_tmp_img)
        print(f"MNI Brain mask saved to: {mni_tmp_img}")
    else:
        print("MNI brain mask already exists")

    r2_success, low_quality, ratio_df = False, None, None
    try:
        tmp_r2_paths = list(tmp_r2_dir.rglob(f"*_task-{task}*_stat-rSquare_statmap.nii.gz"))
        workers = opts.n_workers or max(1, (os.cpu_count() or 1) - 2)
        func = partial(similarity_boldstand_metrics, brainmask_path=str(mni_tmp_img))
        with ProcessPoolExecutor(max_workers=workers) as executor:
            ratio_results = list(executor.map(func, tmp_r2_paths))
        ratio_df = pd.DataFrame(ratio_results)
        low_quality = get_low_quality_subs(ratio_df=ratio_df, dice_thresh=opts.dice_thresh,
                                           voxout_thresh=opts.voxout_thresh)
        r2_success = True
    except Exception as e:
        print(f"R-square similarity calculation error: {e}")

    if r2_success:
        ratio_df.to_csv(spec_imgs_dir / f"{study_id}_task-{task}_hist-dicesimilarity.tsv", sep="\t", index=False)
        for col, title, xlabel, name in (
            ("dice", "Dice Similarity (R2 map ~ MNI)", "Dice Est", "hist-dicesimilarity"),
            ("voxoutmask", "Proportion of Voxels Outside of MNI Mask", "Percentage Out", "hist-voxoutmask"),
        ):
            plt.figure(figsize=(8, 5))
            plt.hist(ratio_df[col], bins=20, edgecolor="black", alpha=0.7)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel("Freq")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(spec_imgs_dir / f"{study_id}_task-{task}_{name}.png")
            plt.close()

    # ---- group z-maps (FitLins names the folder node-dataLevel or node-datasetLevel)
    grp_map_path = next((p for p in (analysis_dir / "node-dataLevel", analysis_dir / "node-datasetLevel")
                         if p.exists()), None)
    if grp_map_path:
        print(f"Setting group map path to: {grp_map_path}")
    sessionlabs = None
    if grp_map_path:
        for con_name in contrast_dict:
            direct = list(grp_map_path.glob(f"*contrast-{con_name}_stat-z_statmap.nii.gz"))
            if direct:
                print(f"No session folders, grabbing {con_name} group map from {grp_map_path.name} directly.\n")
                plot_stat_map(
                    stat_map_img=direct[0], cut_coords=plt_coords, display_mode="ortho", colorbar=True,
                    threshold=opts.zstat_thresh,
                    output_file=str(spec_imgs_dir / f"{study_id}_task-{task}_contrast-{con_name}_map.png"),
                    title=f"{con_name}: z-stat map",
                )
                continue
            session_folders = [f for f in grp_map_path.iterdir() if f.is_dir() and f.name.startswith("ses-")]
            sessionlabs = [s.name for s in session_folders]
            found = False
            for session_folder in session_folders:
                print(f"Session folders existing, grabbing {con_name} group map from "
                      f"{grp_map_path.name} {session_folder.name} sub-directory.\n")
                session_maps = list(session_folder.glob(f"*contrast-{con_name}_stat-z_statmap.nii.gz"))
                if session_maps:
                    found = True
                    plot_stat_map(
                        stat_map_img=session_maps[0], cut_coords=plt_coords, display_mode="ortho", colorbar=True,
                        threshold=opts.zstat_thresh,
                        output_file=str(spec_imgs_dir /
                                        f"{study_id}_task-{task}_{session_folder.name}_contrast-{con_name}_map.png"),
                        title=f"{session_folder.name}, {con_name}: z-stat map",
                    )
            if not found:
                print(f"No z-stat map found for contrast: {con_name}")
    else:
        print("Group map path not found.")

    fold_info = (f"The size of the Fitlins Derivatives for {study_id} {task} is {folder_size(analysis_dir)} "
                 f"with {count_files(analysis_dir)} files.")

    grp_readme = generate_groupmodsummary(
        study_id=study_id,
        task=task,
        deriv_size=fold_info,
        num_subjects=num_subjects,
        hrf_model_type=hrf_model,
        signal_regressors=signal_regressors,
        noise_regressors=noise_regressors,
        convolved_regressors=convolved_names,
        paramod_regressors=parametricmodulator_names,
        has_run=has_run,
        has_subject=has_subject,
        contrast_dict=contrast_dict,
        contrast_image=con_matrix_copy.name if con_matrix_copy else None,
        design_image=design_matrix_copy.name if design_matrix_copy else None,
        spec_imgs_dir=spec_imgs_dir,
        r2_quality_ran=r2_success,
        sub_flag=low_quality,
        sessions=sessionlabs,
        task_cites=cite_list,
        zstat_thresh=opts.zstat_thresh,
        dice_thresh=opts.dice_thresh,
        voxout_thresh=opts.voxout_thresh,
    )
    with open(group_dir / "README.md", "w") as f:
        f.write(grp_readme)
    print(f"Group report written to {group_dir / 'README.md'}")
    return 0
