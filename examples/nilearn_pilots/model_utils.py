import warnings
from scipy.stats import t as t_dist
from scipy.stats import norm
from nilearn.image import new_img_like
warnings.filterwarnings("ignore")
import pandas as pd
from pathlib import Path
import glob
from nilearn.glm import compute_fixed_effects
from nilearn.glm.second_level import SecondLevelModel


def group_onesample(fixedeffect_paths: list, session: str, task_type: str,
                    contrast_type: str, group_outdir: str,
                    mask: str = None, save_zstat: bool = True):
    """
    Computes a group (second-level) model by fitting an intercept to the length of maps.
    Saves computed statistics to disk.
    """    
    group_outdir.mkdir(parents=True, exist_ok=True)
    print("Directory ensured:", group_outdir)
    
    fixedeffect_paths = [str(path) for path in fixedeffect_paths]
    n_maps = len(fixedeffect_paths)
    design_matrix = pd.DataFrame([1] * n_maps, columns=['int'])


    # Fit second-level model
    sec_lvl_model = SecondLevelModel(mask_img=mask, smoothing_fwhm=None, minimize_memory=False)
    sec_lvl_model = sec_lvl_model.fit(second_level_input=fixedeffect_paths, design_matrix=design_matrix)

    tstat_map = sec_lvl_model.compute_contrast(
        second_level_contrast='int',
        second_level_stat_type='t',
        output_type='stat'
    )

    tstat_out = group_outdir / f"subs-{n_maps}_ses-{session}_task-{task_type}_contrast-{contrast_type}_stat-tstat.nii.gz"
    tstat_map.to_filename(tstat_out)

    if save_zstat:
        # t- to z-stat
        df = n_maps - 1  # dfs
        t_values = tstat_map.get_fdata()  # T-values from the image
        z_values = norm.ppf(t_dist.cdf(t_values, df))  # T to Z
        # create z-stat Nifti
        z_map = new_img_like(tstat_map, z_values)
        zstat_out = group_outdir / f"subs-{n_maps}_ses-{session}_task-{task_type}_contrast-{contrast_type}_stat-zstat.nii.gz"
        z_map.to_filename(zstat_out)


def fixed_effect(subject: str, session: str, task_type: str,
                 contrast_list: list, firstlvl_indir: str, fixedeffect_outdir: str,
                 save_beta=False, save_var=False, save_tstat=True):
    """
    Computes fixed effects across runs for a subject and saves results.
    """

    firstlvl_indir = Path(firstlvl_indir)
    fixedeffect_outdir = Path(fixedeffect_outdir)
    fixedeffect_outdir.mkdir(parents=True, exist_ok=True)
    print("Directory ensured:", fixedeffect_outdir)

    for contrast in contrast_list:
        try:
            print(f"\t\t\t Creating weighted fix-eff model for contrast: {contrast}")            
            betas = sorted(firstlvl_indir.glob(f"{subject}_ses-{session}_task-{task_type}_run-*_contrast-{contrast}_stat-beta.nii.gz"))
            var = sorted(firstlvl_indir.glob(f"{subject}_ses-{session}_task-{task_type}_run-*_contrast-{contrast}_stat-var.nii.gz"))

            # Compute fixed effects
            fix_effect, fix_var, fix_tstat = compute_fixed_effects(
                contrast_imgs=betas,
                variance_imgs=var,
                precision_weighted=True
            )

            # Save output files
            if save_beta:
                fix_effect_out = fixedeffect_outdir / f"{subject}_ses-{session}_task-{task_type}_contrast-{contrast}_stat-effect.nii.gz"
                fix_effect.to_filename(fix_effect_out)
            if save_var:
                fix_var_out = fixedeffect_outdir / f"{subject}_ses-{session}_task-{task_type}_contrast-{contrast}_stat-var.nii.gz"
                fix_var.to_filename(fix_var_out)
            if save_tstat:
                fix_tstat_out = fixedeffect_outdir / f"{subject}_ses-{session}_task-{task_type}_contrast-{contrast}_stat-tstat.nii.gz"
                fix_tstat.to_filename(fix_tstat_out)

        except Exception as e:
            print(f'Error processing Fixed Effect: {e} for {subject} and {contrast}')
